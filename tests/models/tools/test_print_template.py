from models.enums import PrintTemplateType
from models.tools.print_template import PrintTemplate


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
