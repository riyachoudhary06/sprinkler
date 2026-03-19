"""
camera/preprocess.py
Resize and base64-encode a captured image for the Gemini Vision API.

Gemini accepts images up to 20 MB; we target ~200 KB for fast upload.
"""
import base64
import logging
from io import BytesIO
from PIL import Image

log = logging.getLogger(__name__)

TARGET_LONG_EDGE = 1024   # px — keeps enough detail for disease identification
JPEG_QUALITY     = 85


def preprocess_image(image_path: str) -> str:
    """
    Load image at image_path, resize to fit within TARGET_LONG_EDGE,
    and return a base64-encoded JPEG string.

    Returns empty string if the file cannot be processed.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        original_size = img.size

        # Resize so the longest edge = TARGET_LONG_EDGE, preserving aspect ratio
        img.thumbnail((TARGET_LONG_EDGE, TARGET_LONG_EDGE), Image.LANCZOS)

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("utf-8")

        log.debug(
            f"Preprocess: {original_size} → {img.size} | "
            f"{len(buf.getvalue())//1024} KB | b64 len={len(encoded)}"
        )
        return encoded

    except Exception as e:
        log.error(f"preprocess_image() failed for '{image_path}': {e}")
        return ""
