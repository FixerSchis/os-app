import math
from io import BytesIO
from typing import Dict, List

from weasyprint import HTML

from models.enums import PrintTemplateType
from models.tools.print_template import PrintTemplate
from utils import generate_qr_code, generate_web_qr_code

# A4 dimensions in millimeters
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
CUT_GUIDE_WIDTH_MM = 0.2  # Width of cut guide lines


class PrintLayout:
    def __init__(self):
        self.page_width = A4_WIDTH_MM
        self.page_height = A4_HEIGHT_MM

    def calculate_layout(
        self,
        item_width: float,
        item_height: float,
        template: PrintTemplate,
        is_back: bool = False,
        generate_cut_guides: bool = True,
    ) -> Dict:
        """
        Calculate layout for items (character sheets, cards, labels) on A4.
        Uses template layout settings for positioning.

        Args:
            item_width: Width of each item in mm
            item_height: Height of each item in mm
            template: PrintTemplate object with layout settings
            is_back: Whether this is for a back side (swaps left/right margins)
            generate_cut_guides: Whether to generate cut guides
        """
        # Use template orientation
        if template.is_landscape:
            # page_width = self.page_height  # 297mm
            # page_height = self.page_width  # 210mm
            pass
        else:
            # page_width = self.page_width  # 210mm
            # page_height = self.page_height  # 297mm
            pass

        # For back sides, swap left and right margins
        margin_left = template.margin_right_mm if is_back else template.margin_left_mm
        template.margin_left_mm if is_back else template.margin_right_mm

        # Calculate positions based on template settings
        positions = []
        for row in range(template.items_per_column):
            for col in range(template.items_per_row):
                # Calculate x position
                x = margin_left + col * (item_width + template.gap_horizontal_mm)
                # Calculate y position
                y = template.margin_top_mm + row * (item_height + template.gap_vertical_mm)
                positions.append((x, y))

        # Generate cut guides if needed
        cut_guides = []
        if generate_cut_guides:
            cut_guides = self._generate_cut_guides(
                margin_left,
                template.margin_top_mm,
                item_width,
                item_height,
                template.items_per_row,
                template.items_per_column,
                template.gap_horizontal_mm,
                template.gap_vertical_mm,
            )

        return {
            "items_per_page": len(positions),
            "sheet_dimensions": (item_width, item_height),
            "positions": positions,
            "cut_guides": cut_guides,
            "landscape": template.is_landscape,
        }

    def _generate_cut_guides(
        self,
        margin_x: float,
        margin_y: float,
        item_width: float,
        item_height: float,
        items_per_row: int,
        items_per_column: int,
        gap_horizontal: float,
        gap_vertical: float,
    ) -> List[Dict]:
        """Generate cut guides for item layouts."""
        guides = []

        # Vertical guides
        for col in range(items_per_row + 1):
            x = margin_x + col * (item_width + gap_horizontal) - gap_horizontal / 2
            guides.append(
                {
                    "x": x,
                    "y": margin_y - 5,
                    "width": CUT_GUIDE_WIDTH_MM,
                    "height": items_per_column * item_height
                    + (items_per_column - 1) * gap_vertical
                    + 10,
                }
            )

        # Horizontal guides
        for row in range(items_per_column + 1):
            y = margin_y + row * (item_height + gap_vertical) - gap_vertical / 2
            guides.append(
                {
                    "x": margin_x - 5,
                    "y": y,
                    "width": items_per_row * item_width + (items_per_row - 1) * gap_horizontal + 10,
                    "height": CUT_GUIDE_WIDTH_MM,
                }
            )

        return guides

    def generate_pdf(
        self, items: List[Dict], template: PrintTemplate, double_sided: bool = False
    ) -> BytesIO:
        """
        Generate a print-ready PDF for either single or double-sided printing.
        For double-sided printing, arranges pages so that fronts and backs match up.

        Args:
            items: List of dictionaries containing item data and rendered HTML
            template: PrintTemplate object with layout settings
            double_sided: Whether to generate a double-sided PDF

        Returns:
            BytesIO object containing the PDF data
        """
        if not items:
            raise ValueError("No items provided for layout calculation")

        # Get width and height from first item or template
        width = float(items[0].get("width_mm", template.width_mm))
        height = float(items[0].get("height_mm", template.height_mm))

        # Get layouts
        front_layout = self.calculate_layout(width, height, template)
        back_layout = (
            self.calculate_layout(width, height, template, is_back=True) if double_sided else None
        )

        items_per_page = front_layout["items_per_page"]
        arranged_pages = []  # Each entry is a list of items for a single page

        if not double_sided:
            # Single-sided: just add layout info to each item
            for page_start in range(0, len(items), items_per_page):
                page_items = []
                for idx, item in enumerate(items[page_start : page_start + items_per_page]):
                    if idx >= len(front_layout["positions"]):
                        break
                    page_items.append(
                        {
                            "width_mm": width,
                            "height_mm": height,
                            "html": item.get("front_html", ""),
                            "css": item.get("css", ""),
                            "position": front_layout["positions"][idx],
                            "layout": front_layout,
                        }
                    )
                arranged_pages.append(page_items)
        else:
            # Double-sided: arrange items so fronts and backs match up when printed
            for page_start in range(0, len(items), items_per_page):
                page_items = items[page_start : page_start + items_per_page]

                # Front page
                front_page = []
                for idx, item in enumerate(page_items):
                    if idx >= len(front_layout["positions"]):
                        break
                    front_page.append(
                        {
                            "width_mm": width,
                            "height_mm": height,
                            "html": item.get("front_html", ""),
                            "css": item.get("css", ""),
                            "position": front_layout["positions"][idx],
                            "layout": front_layout,
                        }
                    )
                arranged_pages.append(front_page)

                # Back page
                back_page = []
                items_per_row = template.items_per_row
                num_rows = math.ceil(len(page_items) / items_per_row)
                for row_idx in range(num_rows):
                    row_start = row_idx * items_per_row
                    row_items = page_items[row_start : row_start + items_per_row]
                    reversed_row_items = list(reversed(row_items))
                    # For back page, assign items to positions in reverse order within each row
                    # This ensures the first item goes to the rightmost position
                    for col_idx, item in enumerate(reversed_row_items):
                        # Calculate position index in reverse order for this row
                        # If items_per_row is 3, positions are: 2, 1, 0 (right to left)
                        pos_idx = row_idx * items_per_row + (items_per_row - 1 - col_idx)
                        if pos_idx >= len(back_layout["positions"]):
                            break
                        back_page.append(
                            {
                                "width_mm": width,
                                "height_mm": height,
                                "html": item.get("back_html", ""),
                                "css": item.get("css", ""),
                                "position": back_layout["positions"][pos_idx],
                                "layout": back_layout,
                            }
                        )
                arranged_pages.append(back_page)

        # Generate the HTML
        html_content = self._generate_print_html(arranged_pages, template.type)

        # Create PDF using WeasyPrint with minimal options
        pdf_buffer = BytesIO()
        html = HTML(string=html_content)
        html.write_pdf(target=pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer

    def _generate_print_html(self, pages: List[List[Dict]], template_type: str) -> str:
        """Internal method to generate print-ready HTML."""
        if not pages or not pages[0]:
            raise ValueError("No items provided for layout calculation")

        # Get template for layout settings
        template = PrintTemplate.query.filter_by(type=template_type).first()
        if not template:
            raise ValueError(f"Template not found for type: {template_type}")

        # Build the HTML
        html = ['<!DOCTYPE html><html><head><meta charset="UTF-8">']

        # Add page orientation style and base CSS
        orientation = "landscape" if template.is_landscape else "portrait"
        html.append(
            f"""
            <style>
                @page {{
                    size: {orientation};
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    width: {297 if orientation == 'landscape' else 210}mm;
                    height: {210 if orientation == 'landscape' else 297}mm;
                    position: relative;
                }}
                .page {{
                    width: {297 if orientation == 'landscape' else 210}mm;
                    height: {210 if orientation == 'landscape' else 297}mm;
                    position: relative;
                    page-break-after: always;
                }}
                .page:last-child {{
                    page-break-after: avoid;
                }}
                .cut-guide {{
                    opacity: 0.5;
                }}
                .template-content {{
                    width: 100%;
                    height: 100%;
                    transform-origin: top left;
                    margin: 0;
                    padding: 0;
                }}
                .item {{
                    position: absolute;
                    transform-origin: top left;
                }}
            </style>
        """
        )
        html.append("</head>")
        html.append("<body>")

        # Generate pages
        for page_items in pages:
            html.append('<div class="page">')
            for item in page_items:
                x, y = item["position"]
                item_html = item.get("html", "")
                html.append(
                    f"""
                <div class="item" style="
                    left: {x}mm;
                    top: {y}mm;
                    width: {item['width_mm']}mm;
                    height: {item['height_mm']}mm;
                    overflow: visible;
                ">
                    <style>
                        /* Base styles for the template content */
                        .template-content {{
                            position: relative;
                            width: {item['width_mm']}mm;
                            height: {item['height_mm']}mm;
                        }}
                        /* Template-specific styles */
                        {item.get('css', '')}
                    </style>
                    <div class="template-content">
                        {item_html}
                    </div>
                </div>
                """
                )
            for guide in item["layout"]["cut_guides"]:
                html.append(
                    f"""
                <div class="cut-guide" style="
                    position: absolute;
                    left: {guide['x']}mm;
                    top: {guide['y']}mm;
                    width: {guide['width']}mm;
                    height: {guide['height']}mm;
                    background-color: #000;
                "></div>
                """
                )
            html.append("</div>")

        html.append("</body></html>")
        return "\n".join(html)

    def generate_character_sheets_pdf(
        self, characters: List, template: PrintTemplate = None
    ) -> BytesIO:
        """Generate a PDF containing character sheets for the given characters."""
        if template is None:
            template = PrintTemplate.query.filter_by(
                type=PrintTemplateType.CHARACTER_SHEET.value
            ).first()
        if not template:
            raise ValueError("Character sheet template not found")

        items_to_print = []
        for character in characters:
            template_context = {
                "character": character,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": (
                        template.get_back_page_render(template_context)
                        if template.has_back_side
                        else None
                    ),
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)

    def generate_character_id_pdf(
        self, characters: List, template: PrintTemplate = None
    ) -> BytesIO:
        """Generate a PDF containing character IDs for the given characters."""
        if template is None:
            template = PrintTemplate.query.filter_by(
                type=PrintTemplateType.CHARACTER_ID.value
            ).first()
        if not template:
            raise ValueError("Character ID template not found")

        items_to_print = []
        for character in characters:
            template_context = {
                "character": character,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": None,
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)

    def generate_item_cards_pdf(self, items: List, template: PrintTemplate = None) -> BytesIO:
        """Generate a PDF containing item cards for the given items."""
        if template is None:
            template = PrintTemplate.query.filter_by(type=PrintTemplateType.ITEM_CARD.value).first()
        if not template:
            raise ValueError("Item card template not found")

        items_to_print = []
        for item in items:
            template_context = {
                "item": item,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": (
                        template.get_back_page_render(template_context)
                        if template.has_back_side
                        else None
                    ),
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)

    def generate_exotic_substance_labels_pdf(
        self, items: List, template: PrintTemplate = None
    ) -> BytesIO:
        """Generate a PDF containing a full sheet of exotic substance labels."""
        if template is None:
            template = PrintTemplate.query.filter_by(
                type=PrintTemplateType.EXOTIC_SUBSTANCE_LABEL.value
            ).first()
        if not template:
            raise ValueError("Exotic substance label template not found")

        items_to_print = []
        for item in items:  # Default to 160 (8x20 grid)
            template_context = {
                "substance": item,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": None,  # Labels are single-sided
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)

    def generate_condition_sheet_pdf(self, items: List, template: PrintTemplate = None) -> BytesIO:
        """Generate a PDF containing a full sheet of identical condition cards."""
        if template is None:
            template = PrintTemplate.query.filter_by(
                type=PrintTemplateType.CONDITION_CARD.value
            ).first()
        if not template:
            raise ValueError("Condition card template not found")

        items_to_print = []
        for item in items:  # Default to 9 (3x3 grid)
            template_context = {
                "condition": item,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": (
                        template.get_back_page_render(template_context)
                        if template.has_back_side
                        else None
                    ),
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)

    def generate_medicament_sheet_pdf(self, items: List, template: PrintTemplate = None) -> BytesIO:
        """Generate a PDF containing a full sheet of identical medicament cards."""
        if template is None:
            template = PrintTemplate.query.filter_by(
                type=PrintTemplateType.MEDICAMENT_CARD.value
            ).first()
        if not template:
            raise ValueError("Medicament card template not found")

        items_to_print = []
        for item in items:  # Default to 9 (3x3 grid)
            template_context = {
                "medicament": item,
                "generate_qr_code": generate_qr_code,
                "generate_web_qr_code": generate_web_qr_code,
            }
            items_to_print.append(
                {
                    "width_mm": template.width_mm,
                    "height_mm": template.height_mm,
                    "front_html": template.get_front_page_render(template_context),
                    "back_html": (
                        template.get_back_page_render(template_context)
                        if template.has_back_side
                        else None
                    ),
                    "css": template.get_css_render(),
                }
            )

        return self.generate_pdf(items_to_print, template, template.has_back_side)
