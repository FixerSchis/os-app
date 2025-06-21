from unittest.mock import MagicMock, patch

import pytest

from models.enums import PrintTemplateType
from utils.print_layout import PrintLayout


@pytest.fixture
def print_layout():
    """Create a PrintLayout instance for testing."""
    return PrintLayout()


@pytest.fixture
def mock_template():
    """Create a mock PrintTemplate for testing."""
    template = MagicMock()
    template.width_mm = 85.6
    template.height_mm = 53.98
    template.is_landscape = False
    template.items_per_row = 2
    template.items_per_column = 3
    template.margin_top_mm = 10.0
    template.margin_bottom_mm = 10.0
    template.margin_left_mm = 10.0
    template.margin_right_mm = 10.0
    template.gap_horizontal_mm = 2.0
    template.gap_vertical_mm = 2.0
    template.type = PrintTemplateType.ITEM_CARD
    return template


def test_calculate_layout_basic(print_layout, mock_template):
    """Test basic layout calculation."""
    layout = print_layout.calculate_layout(
        item_width=85.6,
        item_height=53.98,
        template=mock_template,
        is_back=False,
        generate_cut_guides=True,
    )

    # Check that layout contains expected keys
    assert "items_per_page" in layout
    assert "sheet_dimensions" in layout
    assert "positions" in layout
    assert "cut_guides" in layout
    assert "landscape" in layout

    # Check items per page (2 rows * 3 columns = 6 items)
    assert layout["items_per_page"] == 6

    # Check sheet dimensions
    assert layout["sheet_dimensions"] == (85.6, 53.98)

    # Check landscape setting
    assert layout["landscape"] is False

    # Check positions
    assert len(layout["positions"]) == 6

    # Check first position (top-left)
    first_pos = layout["positions"][0]
    assert first_pos[0] == 10.0  # margin_left
    assert first_pos[1] == 10.0  # margin_top

    # Check cut guides
    assert len(layout["cut_guides"]) > 0


def test_calculate_layout_landscape(print_layout, mock_template):
    """Test layout calculation with landscape orientation."""
    mock_template.is_landscape = True

    layout = print_layout.calculate_layout(
        item_width=85.6,
        item_height=53.98,
        template=mock_template,
        is_back=False,
        generate_cut_guides=True,
    )

    # Check landscape setting
    assert layout["landscape"] is True


def test_calculate_layout_back_side(print_layout, mock_template):
    """Test layout calculation for back side (swaps margins)."""
    layout = print_layout.calculate_layout(
        item_width=85.6,
        item_height=53.98,
        template=mock_template,
        is_back=True,
        generate_cut_guides=True,
    )

    # Check first position (should use margin_right as left margin)
    first_pos = layout["positions"][0]
    assert first_pos[0] == 10.0  # margin_right becomes left margin
    assert first_pos[1] == 10.0  # margin_top stays the same


def test_calculate_layout_no_cut_guides(print_layout, mock_template):
    """Test layout calculation without cut guides."""
    layout = print_layout.calculate_layout(
        item_width=85.6,
        item_height=53.98,
        template=mock_template,
        is_back=False,
        generate_cut_guides=False,
    )

    # Check that no cut guides were generated
    assert len(layout["cut_guides"]) == 0


def test_calculate_layout_different_dimensions(print_layout, mock_template):
    """Test layout calculation with different item dimensions."""
    layout = print_layout.calculate_layout(
        item_width=100.0,
        item_height=70.0,
        template=mock_template,
        is_back=False,
        generate_cut_guides=True,
    )

    # Check sheet dimensions
    assert layout["sheet_dimensions"] == (100.0, 70.0)

    # Check items per page
    assert layout["items_per_page"] == 6


def test_generate_cut_guides(print_layout):
    """Test cut guide generation."""
    guides = print_layout._generate_cut_guides(
        margin_x=10.0,
        margin_y=10.0,
        item_width=85.6,
        item_height=53.98,
        items_per_row=2,
        items_per_column=3,
        gap_horizontal=2.0,
        gap_vertical=2.0,
    )

    # Check that guides were generated
    assert len(guides) > 0

    # Check guide structure
    for guide in guides:
        assert "x" in guide
        assert "y" in guide
        assert "width" in guide
        assert "height" in guide
        assert isinstance(guide["x"], (int, float))
        assert isinstance(guide["y"], (int, float))
        assert isinstance(guide["width"], (int, float))
        assert isinstance(guide["height"], (int, float))


@patch("utils.print_layout.HTML")
@patch("utils.print_layout.PrintTemplate")
def test_generate_pdf_single_sided(mock_print_template, mock_html, print_layout, mock_template):
    """Test PDF generation for single-sided printing."""
    mock_print_template.query.filter_by.return_value.first.return_value = mock_template

    mock_html_instance = MagicMock()
    mock_html.return_value = mock_html_instance

    # Create test items
    items = [
        {
            "width_mm": 85.6,
            "height_mm": 53.98,
            "front_html": "<div>Item 1</div>",
            "css": "body { color: black; }",
        },
        {
            "width_mm": 85.6,
            "height_mm": 53.98,
            "front_html": "<div>Item 2</div>",
            "css": "body { color: black; }",
        },
    ]

    # Test PDF generation
    pdf_buffer = print_layout.generate_pdf(items, mock_template, double_sided=False)

    # Check that HTML was created
    mock_html.assert_called_once()

    # Check that PDF was written
    mock_html_instance.write_pdf.assert_called_once()

    # Check that buffer was returned
    assert pdf_buffer is not None


@patch("utils.print_layout.HTML")
@patch("utils.print_layout.PrintTemplate")
def test_generate_pdf_double_sided(mock_print_template, mock_html, print_layout, mock_template):
    """Test PDF generation for double-sided printing."""
    mock_print_template.query.filter_by.return_value.first.return_value = mock_template

    mock_html_instance = MagicMock()
    mock_html.return_value = mock_html_instance

    # Create test items with back content
    items = [
        {
            "width_mm": 85.6,
            "height_mm": 53.98,
            "front_html": "<div>Item 1 Front</div>",
            "back_html": "<div>Item 1 Back</div>",
            "css": "body { color: black; }",
        },
        {
            "width_mm": 85.6,
            "height_mm": 53.98,
            "front_html": "<div>Item 2 Front</div>",
            "back_html": "<div>Item 2 Back</div>",
            "css": "body { color: black; }",
        },
    ]

    # Test PDF generation
    pdf_buffer = print_layout.generate_pdf(items, mock_template, double_sided=True)

    # Check that HTML was created
    mock_html.assert_called_once()

    # Check that PDF was written
    mock_html_instance.write_pdf.assert_called_once()

    # Check that buffer was returned
    assert pdf_buffer is not None


def test_generate_pdf_no_items(print_layout, mock_template):
    """Test PDF generation with no items."""
    with pytest.raises(ValueError, match="No items provided for layout calculation"):
        print_layout.generate_pdf([], mock_template)


def test_generate_print_html_no_items(print_layout):
    """Test HTML generation with no items."""
    with pytest.raises(ValueError, match="No items provided for layout calculation"):
        print_layout._generate_print_html([], PrintTemplateType.ITEM_CARD)
