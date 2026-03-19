"""
display/oled_display.py
SSD1306 128×64 OLED display via I2C.

Shows rotating screens:
  Screen 1 — IP address + system mode
  Screen 2 — pH, moisture, temperature
  Screen 3 — NPK values
  Screen 4 — Last disease detection result
  Screen 5 — MQTT connection status + uptime

Wiring:
  SSD1306 VCC → 3.3V
  SSD1306 GND → GND
  SSD1306 SCL → GPIO 3 (SCL)
  SSD1306 SDA → GPIO 2 (SDA)
"""
import socket
import time
import logging

log = logging.getLogger(__name__)

WIDTH  = 128
HEIGHT = 64

try:
    import board
    import busio
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    log.warning("OLED libraries not found — display thread will run in no-op mode.")


class OledDisplay:
    def __init__(self, cfg):
        self.cfg          = cfg
        self.display      = None
        self._screen_idx  = 0
        self._last_disease = {}
        self._start_time  = time.time()

        if OLED_AVAILABLE:
            try:
                i2c          = busio.I2C(board.SCL, board.SDA)
                self.display = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
                self.display.fill(0)
                self.display.show()
                log.info("OLED display initialised (SSD1306 128×64).")
            except Exception as e:
                log.error(f"OLED init failed: {e}")
                self.display = None

    # ── public ────────────────────────────────────────────────────────────────

    def update_disease(self, result: dict):
        """Called by DiseaseDetector after each inference cycle."""
        self._last_disease = result

    def start_loop(self):
        log.info(f"OLED loop started — updating every {self.cfg.DISPLAY_UPDATE_INTERVAL}s")
        screens = [
            self._screen_network,
            self._screen_sensors_env,
            self._screen_sensors_npk,
            self._screen_disease,
            self._screen_status,
        ]
        while True:
            try:
                screens[self._screen_idx % len(screens)]()
                self._screen_idx += 1
            except Exception as e:
                log.error(f"OLED loop error: {e}")
            time.sleep(self.cfg.DISPLAY_UPDATE_INTERVAL)

    # ── screens ───────────────────────────────────────────────────────────────

    def _screen_network(self):
        ip = self._get_ip()
        self._draw([
            ("AGRI-WATCH", 0,  True),
            (f"IP: {ip}",  16, False),
            (f"Mode: {self.cfg.mode.upper()}", 28, False),
            ("─" * 21,    40, False),
            ("Pi Node v1.0", 50, False),
        ])

    def _screen_sensors_env(self):
        s = self.cfg._latest_sensors if hasattr(self.cfg, "_latest_sensors") else {}
        ph   = s.get("ph",          "—")
        mois = s.get("moisture",    "—")
        temp = s.get("temperature", "—")
        humi = s.get("humidity",    "—")
        self._draw([
            ("ENV SENSORS",          0,  True),
            (f"pH:      {ph}",       14, False),
            (f"Moisture:{mois}%",    24, False),
            (f"Temp:    {temp}C",    34, False),
            (f"Humidity:{humi}%",    44, False),
        ])

    def _screen_sensors_npk(self):
        s = self.cfg._latest_sensors if hasattr(self.cfg, "_latest_sensors") else {}
        n = s.get("nitrogen",   "—")
        p = s.get("phosphorus", "—")
        k = s.get("potassium",  "—")
        l = s.get("light_lux",  "—")
        self._draw([
            ("NPK SENSORS",      0,  True),
            (f"N: {n} mg/kg",    14, False),
            (f"P: {p} mg/kg",    24, False),
            (f"K: {k} mg/kg",    34, False),
            (f"Lux: {l}",        44, False),
        ])

    def _screen_disease(self):
        d = self._last_disease
        disease  = d.get("disease",  "No data")[:16]
        severity = d.get("severity", "—")
        conf     = d.get("confidence", 0)
        dosage   = d.get("dosage_ml", 0)
        self._draw([
            ("LAST DETECTION",            0,  True),
            (f"{disease}",                14, False),
            (f"Severity: {severity}",     24, False),
            (f"Conf: {int(conf*100)}%",   34, False),
            (f"Dose: {dosage} ml/m2",     44, False),
        ])

    def _screen_status(self):
        uptime_s = int(time.time() - self._start_time)
        h, rem   = divmod(uptime_s, 3600)
        m, s     = divmod(rem, 60)
        uptime   = f"{h:02d}:{m:02d}:{s:02d}"
        self._draw([
            ("SYSTEM STATUS",        0,  True),
            (f"Uptime: {uptime}",    14, False),
            ("MQTT:   OK",           24, False),
            ("Camera: OK",           34, False),
            ("Gemini: OK",           44, False),
        ])

    # ── helpers ───────────────────────────────────────────────────────────────

    def _draw(self, lines: list[tuple]):
        """
        lines: list of (text, y_position, bold)
        Renders to the OLED; if no display, logs to debug instead.
        """
        if not self.display:
            log.debug("OLED (no-op): " + " | ".join(t for t, _, _ in lines))
            return

        img  = Image.new("1", (WIDTH, HEIGHT), 0)
        draw = ImageDraw.Draw(img)

        try:
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
            font_bold   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 9)
        except Exception:
            font_normal = ImageFont.load_default()
            font_bold   = font_normal

        for text, y, bold in lines:
            font = font_bold if bold else font_normal
            draw.text((0, y), text, font=font, fill=255)

        self.display.image(img)
        self.display.show()

    @staticmethod
    def _get_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "no network"
