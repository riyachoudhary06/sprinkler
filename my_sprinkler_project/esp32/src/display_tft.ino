/**
 * display_tft.ino — TFT LCD display (ST7735 / ILI9341 via TFT_eSPI)
 * 
 * IMPORTANT: Configure TFT_eSPI for your specific display module
 * by editing User_Setup.h in the TFT_eSPI library folder before
 * compiling. Set the correct driver, pins, and resolution.
 * 
 * Tested with: 1.8" ST7735 128×160 and 2.4" ILI9341 240×320.
 * 
 * Screen layout (3 lines):
 *   Line 1 (large, white)  — primary status / mode
 *   Line 2 (medium, green) — sensor or spray info
 *   Line 3 (small, gray)   — secondary detail
 */

#include <TFT_eSPI.h>
#include <SPI.h>

TFT_eSPI tft;

// Colour palette (RGB565)
#define C_BG      0x0821   // very dark green-black
#define C_WHITE   TFT_WHITE
#define C_GREEN   0x3FE6   // #3cb47a
#define C_AMBER   0xFD40   // #ffaa00
#define C_RED     0xF800
#define C_GRAY    0x8410
#define C_BORDER  0x2945

static String _prevL1, _prevL2, _prevL3;

void setupDisplay() {
    tft.init();
    tft.setRotation(1);           // landscape
    tft.fillScreen(C_BG);
    tft.setTextDatum(MC_DATUM);   // middle-centre

    // Draw static chrome
    tft.drawFastHLine(0, 25, tft.width(), C_BORDER);
    tft.drawFastHLine(0, tft.height() - 18, tft.width(), C_BORDER);

    // Header label
    tft.setTextColor(C_GREEN, C_BG);
    tft.setTextSize(1);
    tft.drawString("AGRI-WATCH v1.0", tft.width() / 2, 12);

    Serial.println("TFT display initialised.");
}

void updateDisplay(const String& l1, const String& l2, const String& l3) {
    // Only redraw changed lines to avoid flicker
    if (l1 != _prevL1) {
        tft.fillRect(0, 28, tft.width(), 30, C_BG);
        tft.setTextColor(C_WHITE, C_BG);
        tft.setTextSize(2);
        tft.drawString(l1, tft.width() / 2, 43);
        _prevL1 = l1;
    }
    if (l2 != _prevL2) {
        tft.fillRect(0, 60, tft.width(), 22, C_BG);
        tft.setTextColor(C_GREEN, C_BG);
        tft.setTextSize(1);
        tft.drawString(l2, tft.width() / 2, 71);
        _prevL2 = l2;
    }
    if (l3 != _prevL3) {
        tft.fillRect(0, 84, tft.width(), 18, C_BG);
        tft.setTextColor(C_GRAY, C_BG);
        tft.setTextSize(1);
        tft.drawString(l3, tft.width() / 2, 95);
        _prevL3 = l3;
    }

    // Footer: uptime
    tft.fillRect(0, tft.height() - 17, tft.width(), 17, C_BG);
    tft.setTextColor(C_GRAY, C_BG);
    tft.setTextSize(1);
    unsigned long s = millis() / 1000;
    char uptime[16];
    snprintf(uptime, sizeof(uptime), "UP %02lu:%02lu:%02lu",
             s / 3600, (s % 3600) / 60, s % 60);
    tft.drawString(uptime, tft.width() / 2, tft.height() - 9);
}

void displayLoop() {
    // Reserved for future animated elements (e.g. spray progress bar)
}
