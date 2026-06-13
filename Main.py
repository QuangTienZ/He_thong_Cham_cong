"""
ESP32 - Đọc thẻ RFID MFRC522 và hiển thị lên LCD I2C 16x2
Yêu cầu: i2c_lcd.py, lcd_api.py, MFRC522.py

Sơ đồ kết nối:
-------------------------------------------------
MFRC522 (RFID)     ->  ESP32
  SDA (CS)         ->  GPIO 5
  SCK              ->  GPIO 18
  MOSI             ->  GPIO 23
  MISO             ->  GPIO 19
  RST              ->  GPIO 4
  3.3V             ->  3.3V
  GND              ->  GND

LCD I2C (PCF8574)  ->  ESP32
  SDA              ->  GPIO 21
  SCL              ->  GPIO 22
  VCC              ->  5V (hoặc 3.3V tùy module)
  GND              ->  GND
-------------------------------------------------
"""

import utime
from machine import I2C, Pin
from i2c_lcd import I2cLcd
from mfrc522 import MFRC522

# ── Cấu hình LCD ──────────────────────────────────────────────────────────────
I2C_ADDR    = 0x27   # Địa chỉ I2C của module PCF8574 (0x27 hoặc 0x3F)
LCD_ROWS    = 2
LCD_COLS    = 16

i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, LCD_ROWS, LCD_COLS)

# ── Cấu hình RFID ─────────────────────────────────────────────────────────────
SCK_PIN  = 18
MOSI_PIN = 23
MISO_PIN = 19
RST_PIN  = 4
CS_PIN   = 5

rfid = MFRC522(sck=SCK_PIN, mosi=MOSI_PIN, miso=MISO_PIN, rst=RST_PIN, cs=CS_PIN)

# ── Danh sách thẻ được phép (tuỳ chỉnh) ───────────────────────────────────────
# Thêm UID thẻ của bạn vào đây, dạng tuple
# Ví dụ: (0xDE, 0xAD, 0xBE, 0xEF, 0x00)
AUTHORIZED_CARDS = {
    # (0x12, 0x34, 0x56, 0x78): "Nguyen Van A",
    # (0xAB, 0xCD, 0xEF, 0x01): "Tran Thi B",
}

# ── Hàm tiện ích ──────────────────────────────────────────────────────────────

def uid_to_str(uid_list):
    """Chuyển danh sách bytes UID thành chuỗi hex."""
    return ":".join("{:02X}".format(b) for b in uid_list)

def uid_to_tuple(uid_list):
    """Chuyển danh sách bytes UID thành tuple (dùng tra cứu dict)."""
    return tuple(uid_list[:4])

def lcd_print(line1="", line2=""):
    """Xoá màn hình và in 2 dòng lên LCD."""
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:LCD_COLS])
    if line2:
        lcd.move_to(0, 1)
        lcd.putstr(line2[:LCD_COLS])

# ── Màn hình chờ ──────────────────────────────────────────────────────────────

def show_ready():
    lcd_print("  Quet the RFID ", "   de tiep tuc  ")

# ── Vòng lặp chính ────────────────────────────────────────────────────────────

def main():
    #print("He thong dang khoi dong...")
    lcd_print(" He thong RFID  ", "  Dang khoi dong")
    utime.sleep(2)
    show_ready()
    #print("San sang doc the RFID...")

    last_uid = None
    last_read_time = 0
    DEBOUNCE_MS = 5000  # Tránh đọc lại thẻ liên tục (2 giây)

    while True:
        stat, _ = rfid.request(rfid.REQIDL)

        if stat == rfid.OK:
            stat, uid = rfid.anticoll()

            if stat == rfid.OK:
                rfid.select_tag(uid)
                rfid.stop_crypto1()
                now = utime.ticks_ms()
                uid_tuple = uid_to_tuple(uid)

                # Bỏ qua nếu vừa đọc thẻ này trong vòng DEBOUNCE_MS
                if uid_tuple == last_uid and utime.ticks_diff(now, last_read_time) < DEBOUNCE_MS:
                    continue

                last_uid = uid_tuple
                last_read_time = now

                uid_str = uid_to_str(uid[:4])
                print(uid_str.replace(":", ""))

                # Kiểm tra thẻ có trong danh sách không
                if AUTHORIZED_CARDS:
                    name = AUTHORIZED_CARDS.get(uid_tuple)
                    if name:
                        print("Cho phep:", name)
                        lcd_print("✓ Cho phep!     ", name)
                    else:
                        print("Tu choi! UID:", uid_str)
                        lcd_print("✗ Tu choi!      ", uid_str)
                else:
                    # Chế độ chỉ hiển thị UID (không kiểm tra danh sách)
                    short_uid = uid_str.replace(":", "")
                    lcd_print("UID the:        ", short_uid)
                    #print("UID:", uid_str)

                utime.sleep_ms(2000)
                show_ready()

        utime.sleep_ms(100)

# ── Khởi chạy ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()


