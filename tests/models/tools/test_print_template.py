import pytest
from jinja2.exceptions import SecurityError, UndefinedError

from models.enums import PrintTemplateType
from models.tools.print_template import PrintTemplate
from utils import generate_qr_code, generate_web_qr_code


def _sandbox_template(user, front_html, back_html="", has_back_side=False):
    return PrintTemplate(
        type=PrintTemplateType.ITEM_CARD,
        type_name="Sandbox Template",
        front_html=front_html,
        back_html=back_html,
        has_back_side=has_back_side,
        created_by_user_id=user.id,
    )


def _assert_render_blocks_secret(render, secret):
    with pytest.raises((SecurityError, UndefinedError)) as exc_info:
        render()
    assert secret not in str(exc_info.value)


def test_print_template_methods(db, new_user):
    """Test PrintTemplate methods without creating a database record due to unique
    constraints."""
    # Create a template instance without saving to database
    template = PrintTemplate(
        type=PrintTemplateType.ITEM_CARD,
        type_name="Test Item Card",
        width_mm=85.6,
        height_mm=53.98,
        front_html="<body><h1>{{ item.name }}</h1></body>",
        back_html="<body><p>{{ item.description }}</p></body>",
        css_styles="body { color: red; } /* comment */",
        has_back_side=True,
        created_by_user_id=new_user.id,
        is_landscape=False,
        items_per_row=2,
        items_per_column=3,
        margin_top_mm=5.0,
        margin_bottom_mm=5.0,
        margin_left_mm=5.0,
        margin_right_mm=5.0,
        gap_horizontal_mm=1.0,
        gap_vertical_mm=1.0,
    )

    # Test template processing methods
    context = {"item": {"name": "Test Item", "description": "A test item"}}

    # Test front page rendering
    front_render = template.get_front_page_render(context)
    assert "<h1>Test Item</h1>" in front_render

    # Test back page rendering
    back_render = template.get_back_page_render(context)
    assert "<p>A test item</p>" in back_render

    # Test CSS processing
    css_render = template.get_css_render()
    assert ".template-content" in css_render
    assert "color: red" in css_render
    assert "/* comment */" not in css_render  # Comments should be removed
    assert f"width: {template.width_mm}mm" in css_render
    assert f"height: {template.height_mm}mm" in css_render

    # Test comment removal methods
    html_with_comments = "<!-- comment --><div>content</div>"
    cleaned_html = template.remove_html_comments(html_with_comments)
    assert "<!-- comment -->" not in cleaned_html
    assert "<div>content</div>" in cleaned_html

    css_with_comments = "/* comment */ body { color: red; }"
    cleaned_css = template.remove_css_comments(css_with_comments)
    assert "/* comment */" not in cleaned_css
    assert "body { color: red; }" in cleaned_css

    # Test extract_body_content method
    html_with_body = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    body_content = template.extract_body_content(html_with_body)
    assert "<h1>Title</h1>" in body_content
    assert "<p>Content</p>" in body_content
    assert "<html>" not in body_content
    assert "<body>" not in body_content

    # Test scope_template_css method
    scoped_css = template.scope_template_css()
    assert ".template-content" in scoped_css
    assert "color: red" in scoped_css
    assert "/* comment */" not in scoped_css
    assert f"width: {template.width_mm}mm" in scoped_css
    assert f"height: {template.height_mm}mm" in scoped_css


def test_print_template_renders_fields_methods_and_qr_codes(db, new_user):
    class Skill:
        def __init__(self, name):
            self.name = name

    class CharacterSkill:
        def __init__(self, name):
            self.skill = Skill(name)
            self.times_purchased = 2

        def format_description(self):
            return f"{self.skill.name} x{self.times_purchased}"

    class Character:
        def __init__(self):
            self.name = "Alex Chen"
            self.user = type("User", (), {"first_name": "Admin", "surname": "User"})()
            self.faction = type("Faction", (), {"name": "Free Traders"})()
            self.species = type("Species", (), {"body_hits": 3})()
            self.skills = [CharacterSkill("Engineering")]

        def get_character_sheet_values(self):
            return {"will": {"name": "Will Points", "value": 1}}

    character = Character()
    template = _sandbox_template(
        new_user,
        """
        {{ character.user.first_name }} {{ character.user.surname }}
        {{ character.name }}
        {{ character.faction.name }}
        {{ character.species.body_hits }}
        {% for value in character.get_character_sheet_values().values() %}
        {{ value.name }}:{{ value.value }}
        {% endfor %}
        {% for character_skill in character.skills %}
        {{ character_skill.skill.name }} {{ character_skill.format_description() }}
        {% endfor %}
        {{ generate_qr_code(character.name) }}
        {{ generate_web_qr_code('templates.template_list') }}
        """,
    )

    rendered = template.get_front_page_render(
        {
            "character": character,
            "generate_qr_code": generate_qr_code,
            "generate_web_qr_code": generate_web_qr_code,
        }
    )

    assert "Admin User" in rendered
    assert "Alex Chen" in rendered
    assert "Free Traders" in rendered
    assert "Will Points:1" in rendered
    assert "Engineering x2" in rendered
    assert rendered.count("data:image/png;base64,") == 2


def test_print_template_leaves_optional_context_blank(db, new_user):
    template = _sandbox_template(new_user, "URL:{{ item_view_url }}")

    assert template.get_front_page_render({"item": {"name": "Card"}}) == "URL:"


def test_print_template_blocks_config_and_python_globals(db, new_user, app):
    secret = "print-template-secret-value"
    original_secret = app.config["SECRET_KEY"]
    app.config["SECRET_KEY"] = secret

    class Carrier:
        def __init__(self):
            self.name = "Card"
            self.config = {"SECRET_KEY": secret}

    try:
        leaked_templates = [
            "{{ config }}",
            "{{ config.SECRET_KEY }}",
            "{{ config['SECRET_KEY'] }}",
            "{{ generate_qr_code.__globals__ }}",
            "{{ generate_qr_code|attr('__' ~ 'globals__') }}",
            "{{ item.config.SECRET_KEY }}",
            "{{ helper.config.SECRET_KEY }}",
        ]
        context = {
            "item": Carrier(),
            "helper": app,
            "config": app.config,
            "current_app": app,
            "generate_qr_code": generate_qr_code,
        }
        for front_html in leaked_templates:
            template = _sandbox_template(new_user, front_html)
            _assert_render_blocks_secret(
                lambda template=template: template.get_front_page_render(context),
                secret,
            )

        back_template = _sandbox_template(
            new_user,
            "front",
            back_html="{{ config.SECRET_KEY }}",
            has_back_side=True,
        )
        _assert_render_blocks_secret(
            lambda: back_template.get_back_page_render(context),
            secret,
        )

        safe = _sandbox_template(new_user, "{{ item.name }}")
        assert safe.get_front_page_render(context) == "Card"
    finally:
        app.config["SECRET_KEY"] = original_secret
