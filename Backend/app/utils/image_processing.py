"""
CareSlot — Image Processing Utilities
"""

from PIL import Image
import io
from typing import Tuple

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_image(filename: str, file_size: int) -> Tuple[bool, str]:
    """Validate image file type and size."""
    import os
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}"
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large ({file_size} bytes). Max: {MAX_FILE_SIZE} bytes"
    return True, "Valid"


def resize_image(image_bytes: bytes, target_size: Tuple[int, int] = (224, 224)) -> bytes:
    """Resize an image to the target dimensions."""
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size, Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def get_image_dimensions(image_bytes: bytes) -> Tuple[int, int]:
    """Get width and height of an image."""
    image = Image.open(io.BytesIO(image_bytes))
    return image.size
