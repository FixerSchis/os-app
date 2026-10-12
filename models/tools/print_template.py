import re
import types
from datetime import datetime, timezone

from flask import Flask
from flask.config import Config
from jinja2 import select_autoescape
from jinja2.exceptions import SecurityError
from jinja2.runtime import Undefined
from jinja2.sandbox import SandboxedEnvironment, is_internal_attribute
from jinja2.utils import missing

from models.enums import PrintTemplateType
from models.extensions import db

# Flask injects these names into render_template_string. Print templates must not see them.
_BLOCKED_CONTEXT_NAMES = frozenset({"config", "current_app", "request", "session", "g"})

# Attribute names that walk from a print object or helper into app config or Python globals.
_BLOCKED_ATTRIBUTES = frozenset(
    {
        "config",
        "__globals__",
        "__dict__",
        "__class__",
        "__bases__",
        "__mro__",
        "__subclasses__",
        "__init__",
        "func_globals",
        "func_code",
        "gi_frame",
        "gi_code",
        "cr_frame",
        "cr_code",
        "ag_frame",
        "ag_code",
        "f_globals",
        "f_locals",
        "f_code",
        "tb_frame",
        "mro",
    }
)

_ALLOWED_CALLABLES = frozenset({"generate_qr_code", "generate_web_qr_code", "qr_code_filter"})


class PrintTemplateUndefined(Undefined):
    """Undefined values that fail closed for config and other blocked names."""

    __slots__ = ()

    def _deny_blocked_access(self):
        if self._undefined_exception is SecurityError:
            self._fail_with_undefined_error()
        if self._undefined_obj is missing and self._undefined_name in _BLOCKED_CONTEXT_NAMES:
            raise SecurityError(f"{self._undefined_name} is not available in print templates")

    def __str__(self):
        self._deny_blocked_access()
        return ""

    def __iter__(self):
        self._deny_blocked_access()
        yield from ()

    def __bool__(self):
        if self._undefined_exception is SecurityError or (
            self._undefined_obj is missing and self._undefined_name in _BLOCKED_CONTEXT_NAMES
        ):
            self._deny_blocked_access()
        return False


class PrintTemplateEnvironment(SandboxedEnvironment):
    """Sandboxed Jinja environment for stored print templates."""

    def is_safe_attribute(self, obj, attr, value):
        if attr in _BLOCKED_ATTRIBUTES or attr.startswith("_"):
            return False
        if is_internal_attribute(obj, attr):
            return False
        if isinstance(
            value,
            (Flask, Config, types.ModuleType, types.FrameType, types.TracebackType, types.CodeType),
        ):
            return False
        return True

    def is_safe_callable(self, obj):
        # Print context passes QR helpers as callables. Keep those callable, and
        # still allow ordinary model methods used by character sheets and cards.
        if getattr(obj, "__name__", None) in _ALLOWED_CALLABLES:
            return True
        return super().is_safe_callable(obj)


_print_environment = PrintTemplateEnvironment(
    autoescape=select_autoescape(default_for_string=True),
    undefined=PrintTemplateUndefined,
)


def _render_print_html(html, context):
    safe_context = {}
    for key, value in (context or {}).items():
        if key in _BLOCKED_CONTEXT_NAMES or isinstance(value, (Flask, Config)):
            continue
        safe_context[key] = value
    return _print_environment.from_string(html).render(**safe_context)


class PrintTemplate(db.Model):
    __tablename__ = "print_templates"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(
        db.Enum(
            PrintTemplateType,
            values_callable=lambda x: [e.value for e in x],
            native_enum=False,
        ),
        nullable=False,
        unique=True,
    )
    type_name = db.Column(db.String(100), nullable=False)  # Human-readable name
    width_mm = db.Column(db.Float, nullable=False, default=85.6)  # Default to item card width
    height_mm = db.Column(db.Float, nullable=False, default=53.98)  # Default to item card height
    front_html = db.Column(db.Text, nullable=False, default="")
    back_html = db.Column(db.Text, nullable=True)
    css_styles = db.Column(db.Text, nullable=False, default="")
    has_back_side = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Layout settings
    is_landscape = db.Column(db.Boolean, nullable=False, default=False)  # Page orientation
    items_per_row = db.Column(db.Integer, nullable=False, default=1)  # Number of items per row
    items_per_column = db.Column(
        db.Integer, nullable=False, default=1
    )  # Number of items per column
    margin_top_mm = db.Column(db.Float, nullable=False, default=10.0)  # Top margin in mm
    margin_bottom_mm = db.Column(db.Float, nullable=False, default=10.0)  # Bottom margin in mm
    margin_left_mm = db.Column(db.Float, nullable=False, default=10.0)  # Left margin in mm
    margin_right_mm = db.Column(db.Float, nullable=False, default=10.0)  # Right margin in mm
    gap_horizontal_mm = db.Column(
        db.Float, nullable=False, default=2.0
    )  # Horizontal gap between items in mm
    gap_vertical_mm = db.Column(
        db.Float, nullable=False, default=2.0
    )  # Vertical gap between items in mm

    created_by_user = db.relationship("User", backref="created_templates")

    def __repr__(self):
        return f"<PrintTemplate {self.type_name} ({self.type})>"

    def remove_html_comments(self, html):
        return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    def remove_css_comments(self, css):
        return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

    def extract_body_content(self, html):
        html = self.remove_html_comments(html)
        match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return html

    def scope_template_css(self):
        css = self.remove_css_comments(self.css_styles)
        css = re.sub(r"\bbody\b", ".template-content", css)
        css += (
            f"\n.template-content {{ width: {self.width_mm}mm; " f"height: {self.height_mm}mm; }}"
        )
        return css

    def get_front_page_render(self, context):
        if not self.front_html:
            return ""
        rendered = _render_print_html(self.front_html, context)
        return self.extract_body_content(rendered)

    def get_back_page_render(self, context):
        if not self.back_html or not self.has_back_side:
            return ""
        rendered = _render_print_html(self.back_html, context)
        return self.extract_body_content(rendered)

    def get_css_render(self):
        css = self.remove_css_comments(self.css_styles)
        css = re.sub(r"\bbody\b", ".template-content", css)
        css += (
            f"\n.template-content {{ width: {self.width_mm}mm; " f"height: {self.height_mm}mm; }}"
        )
        return css
