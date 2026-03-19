"""
camera/capture.py
Take a high-resolution still snapshot with picamera2.
Returns the saved file path.
"""
import os
import time
import logging
from picamera2 import Picamera2

log = logging.getLogger(__name__)


def capture_image(save_dir: str, width: int = 1280, height: int = 960) -> str:
    """
    Capture a JPEG still and save to save_dir.
    Returns the absolute path to the saved file.
    Raises RuntimeError if capture fails.
    """
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"capture_{int(time.time())}.jpg")

    cam = Picamera2()
    try:
        config = cam.create_still_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        cam.configure(config)
        cam.start()
        time.sleep(0.5)   # allow auto-exposure to settle
        cam.capture_file(filename)
        log.info(f"Snapshot saved: {filename}")
        return filename
    except Exception as e:
        log.error(f"capture_image() failed: {e}")
        raise RuntimeError(f"Camera capture failed: {e}") from e
    finally:
        cam.stop()
        cam.close()
