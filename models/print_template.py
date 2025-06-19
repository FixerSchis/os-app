from models.extensions import db
from datetime import datetime
from models.enums import PrintTemplateType
import re
from flask import render_template_string
import base64

class PrintTemplate(db.Model):
    __tablename__ = 'print_templates'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum(PrintTemplateType, values_callable=lambda x: [e.value for e in x], native_enum=False), nullable=False, unique=True)
    type_name = db.Column(db.String(100), nullable=False)         # Human-readable name
    width_mm = db.Column(db.Float, nullable=False, default=85.6)  # Default to item card width
    height_mm = db.Column(db.Float, nullable=False, default=53.98)  # Default to item card height
    front_html = db.Column(db.Text, nullable=False, default='')
    back_html = db.Column(db.Text, nullable=True)
    css_styles = db.Column(db.Text, nullable=False, default='')
    has_back_side = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Layout settings
    is_landscape = db.Column(db.Boolean, nullable=False, default=False)  # Page orientation
    items_per_row = db.Column(db.Integer, nullable=False, default=1)  # Number of items per row
    items_per_column = db.Column(db.Integer, nullable=False, default=1)  # Number of items per column
    margin_top_mm = db.Column(db.Float, nullable=False, default=10.0)  # Top margin in mm
    margin_bottom_mm = db.Column(db.Float, nullable=False, default=10.0)  # Bottom margin in mm
    margin_left_mm = db.Column(db.Float, nullable=False, default=10.0)  # Left margin in mm
    margin_right_mm = db.Column(db.Float, nullable=False, default=10.0)  # Right margin in mm
    gap_horizontal_mm = db.Column(db.Float, nullable=False, default=2.0)  # Horizontal gap between items in mm
    gap_vertical_mm = db.Column(db.Float, nullable=False, default=2.0)  # Vertical gap between items in mm

    created_by_user = db.relationship('User', backref='created_templates')

    def __repr__(self):
        return f'<PrintTemplate {self.type_name} ({self.type})>'

    def remove_html_comments(self, html):
        return re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    def remove_css_comments(self, css):
        return re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)

    def extract_body_content(self, html):
        html = self.remove_html_comments(html)
        match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return html

    def scope_template_css(self):
        css = self.remove_css_comments(self.css_styles)
        css = re.sub(r'\bbody\b', '.template-content', css)
        css += f"\n.template-content {{ width: {self.width_mm}mm; height: {self.height_mm}mm; }}"
        return css

    def get_front_page_render(self, context):
        if not self.front_html:
            return ''
        rendered = render_template_string(self.front_html, **context)
        return self.extract_body_content(rendered)

    def get_back_page_render(self, context):
        if not self.back_html or not self.has_back_side:
            return ''
        rendered = render_template_string(self.back_html, **context)
        return self.extract_body_content(rendered)

    def get_css_render(self):
        css = self.remove_css_comments(self.css_styles)
        css = re.sub(r'\bbody\b', '.template-content', css)
        css += f"\n.template-content {{ width: {self.width_mm}mm; height: {self.height_mm}mm; }}"
        return css 