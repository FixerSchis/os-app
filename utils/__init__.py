# Utils package

import base64
import logging
from io import BytesIO

import qrcode
from flask import url_for


def generate_qr_code(data, size=10, border=2):
    """
    Generate a QR code and return it as a base64 encoded data URL

    Args:
        data: The data to encode in the QR code (usually a URL)
        size: The size of each QR code module in pixels (default: 10)
        border: The border width in modules (default: 2)

    Returns:
        Base64 encoded data URL for the QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def generate_web_qr_code(route_name, **kwargs):
    """
    Generate a QR code for a web route

    Args:
        route_name: The Flask route name
        **kwargs: URL parameters for the route

    Returns:
        Base64 encoded data URL for the QR code image
    """
    try:
        url = url_for(route_name, **kwargs, _external=True)
        return generate_qr_code(url)
    except Exception:
        logging.exception("Error generating QR code")
