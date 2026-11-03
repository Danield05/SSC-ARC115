#include "display.h"

#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Wire.h>

#include "config.h"

namespace display {

static Adafruit_SSD1306 oled(128, 64, &Wire, -1);
static bool g_ready = false;

bool begin() {
  g_ready = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS);
  if (g_ready) {
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    oled.display();
  }
  return g_ready;
}

static void titleBar(const char* title) {
  oled.fillRect(0, 0, 128, 11, SSD1306_WHITE);
  oled.setTextColor(SSD1306_BLACK);
  oled.setTextSize(1);
  oled.setCursor(2, 2);
  oled.print(title);
  oled.setTextColor(SSD1306_WHITE);
}

static void footerLine(const char* footer) {
  if (!footer || !footer[0]) return;
  oled.setTextSize(1);
  oled.setCursor(0, 56);
  oled.print(footer);
}

void show(const char* title, const char* line1, const char* line2, const char* line3,
          const char* footer) {
  if (!g_ready) return;
  oled.clearDisplay();
  titleBar(title);
  oled.setTextSize(1);
  const char* lines[3] = {line1, line2, line3};
  for (int i = 0; i < 3; i++) {
    oled.setCursor(0, 16 + i * 12);
    oled.print(lines[i]);
  }
  footerLine(footer);
  oled.display();
}

void showBig(const char* title, const char* big, const char* line, const char* footer) {
  if (!g_ready) return;
  oled.clearDisplay();
  titleBar(title);
  oled.setTextSize(2);
  oled.setCursor(0, 18);
  oled.print(big);
  oled.setTextSize(1);
  oled.setCursor(0, 42);
  oled.print(line);
  footerLine(footer);
  oled.display();
}

}  // namespace display
