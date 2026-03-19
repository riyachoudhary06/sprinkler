"""
camera/camera_stream.py
Serves an MJPEG stream over HTTP using picamera2.
Stream URL: http://<pi-ip>:8080/stream
"""
import io
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

log = logging.getLogger(__name__)


class _StreamingOutput(io.BufferedIOBase):
    """Thread-safe buffer that holds the latest JPEG frame."""

    def __init__(self):
        self.frame     = None
        self.condition = threading.Condition()

    def write(self, buf: bytes) -> int:
        with self.condition:
            self.frame = buf
            self.condition.notify_all()
        return len(buf)


class _StreamHandler(BaseHTTPRequestHandler):
    output: _StreamingOutput = None

    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Age", "0")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
            self.end_headers()
            try:
                while True:
                    with _StreamHandler.output.condition:
                        _StreamHandler.output.condition.wait()
                        frame = _StreamHandler.output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError):
                pass   # client disconnected
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass   # suppress per-request access logs


class CameraStream:
    def __init__(self, cfg):
        self.cfg    = cfg
        self.output = _StreamingOutput()
        _StreamHandler.output = self.output
        self._cam   = None

    def start(self):
        log.info(f"Camera stream starting on port {self.cfg.STREAM_PORT}...")
        self._cam = Picamera2()
        config = self._cam.create_video_configuration(
            main={"size": (self.cfg.STREAM_WIDTH, self.cfg.STREAM_HEIGHT), "format": "RGB888"}
        )
        self._cam.configure(config)
        self._cam.start_recording(JpegEncoder(), FileOutput(self.output))

        server = HTTPServer(("", self.cfg.STREAM_PORT), _StreamHandler)
        log.info(
            f"Camera stream live → http://0.0.0.0:{self.cfg.STREAM_PORT}/stream"
        )
        server.serve_forever()

    def stop(self):
        if self._cam:
            self._cam.stop_recording()
            self._cam.close()
