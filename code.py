import time
import board
import busio
import displayio
import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label
import i2cdisplaybus
from rotary_encoder import RotaryEncoder
from digitalio import DigitalInOut, Direction, Pull
import random
import adafruit_adxl34x
import math
import neopixel

displayio.release_displays()

# -----------------------------------------
# ROTARY ENCODER
# -----------------------------------------
encoder = RotaryEncoder(board.D8, board.D7, debounce_ms=3, pulses_per_detent=3)

btn = DigitalInOut(board.D9)
btn.direction = Direction.INPUT
btn.pull = Pull.UP
prev_state = btn.value

# -----------------------------------------
# OLED setup
# -----------------------------------------
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Screen group
splash = displayio.Group()
display.root_group = splash

text_layer = label.Label(terminalio.FONT, text="")
splash.append(text_layer)

# -----------------------------------------
# DIFFICULTY MENU (WORKING – NO .position writes)
# -----------------------------------------

options = ["Easy", "Medium", "Hard"]
index = 0

def center_txt(layer):
    layer.x = (display.width - text_layer.bounding_box[2]) // 2
    layer.y = (display.height - text_layer.bounding_box[3]) // 2

def draw_menu():
    text = ""
    for i, opt in enumerate(options):
        if i == index:
            text += "> " + opt + "\n"
        else:
            text += "  " + opt + "\n"

    text_layer.text = text
    center_txt(text_layer)

def select_difficulty():
    global index, prev_state

    # Show first message
    text_layer.text = "Select Mode"
    center_txt(text_layer)
    time.sleep(1)

    draw_menu()

    # Track encoder movement
    prev_pos = encoder.position

    while True:
        encoder.update()
        cur_pos = encoder.position

        # ROTATION movement
        delta = cur_pos - prev_pos

        if delta != 0:
            # Clamp movement to +1 or -1
            step = 1 if delta > 0 else -1
            index = (index + step) % len(options)
            draw_menu()
            prev_pos = cur_pos
            time.sleep(0.15)

        # BUTTON PRESS
        cur = btn.value
        if prev_state and not cur:  # falling edge
            chosen = options[index]
            text_layer.text = "Chosen: " + chosen
            center_txt(text_layer)
            time.sleep(1)
            return chosen

        prev_state = cur

# Timer values by difficulty
def diff_mode(choice):
    if choice == "Easy":
        return 20
    if choice == "Medium":
        return 10
    if choice == "Hard":
        return 5

# --------------------------------------------------
# GET DIFFICULTY SELECTION NOW
# --------------------------------------------------
difficulty_choice = select_difficulty()
timer_limit = diff_mode(difficulty_choice)


# --------------------------------------------------
# REST OF YOUR GAME CODE (UNCHANGED)
# --------------------------------------------------

# Accelerometer
accelerometer = adafruit_adxl34x.ADXL345(i2c)

start_time = time.monotonic()
response_time = None
prev_encoder_pos = encoder.position

alpha = 0.2
pitch_filtered = 0

FORWARD_ANGLE = 25
BACKWARD_ANGLE = -25
EXIT_ANGLE = 5
state = "neutral"
neutral_start = None
twist_cooldown = 0.3
last_success_time = 0

pixel_pin = board.D10
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=True)

RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

def set_color(color):
    pixels.fill(color)
    pixels.brightness = 0.03
    pixels.show()

def calibrate_zero(accel, samples=50, delay=0.01):
    x_list, y_list = [], []
    for _ in range(samples):
        x, y, _ = accel.acceleration
        x_list.append(x)
        y_list.append(y)
        time.sleep(delay)
    return sum(x_list) / samples, sum(y_list) / samples

def get_pitch(ax, ay, az):
    return math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))

def detect_neutral(pitch):
    global state, neutral_start
    if -EXIT_ANGLE < pitch < EXIT_ANGLE:
        if state != "neutral":
            state = "neutral"
            neutral_start = time.monotonic()
            return True
    return False

def detect_forwardTilt(pitch):
    global state
    if pitch > FORWARD_ANGLE and state != "forward":
        state = "forward"
        return True
    detect_neutral(pitch)
    return False

def detect_backwardTilt(pitch):
    global state
    if pitch < BACKWARD_ANGLE and state != "backward":
        state = "backward"
        return True
    detect_neutral(pitch)
    return False

def update_inputs():
    global prev_encoder_pos, prev_state

    encoder.update()
    delta = encoder.position - prev_encoder_pos
    twist = False
    if abs(delta) >= 1:
        prev_encoder_pos = encoder.position
        twist = True

    cur = btn.value
    push = False
    if prev_state and not cur:
        push = True
    prev_state = cur

    return push, twist

def player_response(pitch_filtered):
    push, twist = update_inputs()

    tilt_fwd = detect_forwardTilt(pitch_filtered)
    tilt_back = detect_backwardTilt(pitch_filtered)

    if push: return "Push it!"
    if twist: return "Twist it!"
    if tilt_fwd: return "Forward!"
    if tilt_back: return "Backward!"
    return None

def twistIt():
    text_layer.text = "Twist it!"
    center_txt(text_layer)

def pushIt():
    text_layer.text = "Push it!"
    center_txt(text_layer)

def forward():
    text_layer.text = "Forward!"
    center_txt(text_layer)

def backward():
    text_layer.text = "Backward!"
    center_txt(text_layer)

plays = [
    {"label": "Twist it!", "func": twistIt, "check": lambda p: p == "Twist it!"},
    {"label": "Push it!",  "func": pushIt,  "check": lambda p: p == "Push it!"},
    {"label": "Forward!", "func": forward, "check": lambda p: p == "Forward!"},
    {"label": "Backward!","func": backward,"check": lambda p: p == "Backward!"},
]

game_over = False
x_b, y_b = calibrate_zero(accelerometer)

while not game_over:
    set_color((255, 150, 0))
    chosen = random.choice(plays)
    prev_encoder_pos = encoder.position
    chosen["func"]()
    expected = chosen["label"]
    start_time = time.monotonic()

    while True:
        ax, ay, az = accelerometer.acceleration
        pitch_raw = get_pitch(ax - x_b, ay - y_b, az)
        pitch_filtered = alpha * pitch_raw + (1 - alpha) * pitch_filtered

        move = player_response(pitch_filtered)

        if move == expected:
            set_color((0, 255, 0))
            text_layer.text = "Nice!"
            center_txt(text_layer)
            time.sleep(0.7)
            state = "neutral"
            break

        if move:
            set_color((255, 0, 0))
            text_layer.text = "Wrong move!"
            center_txt(text_layer)
            time.sleep(1)
            text_layer.text = "Game Over!"
            center_txt(text_layer)
            set_color((255, 255, 255))
            game_over = True
            break

        if time.monotonic() - start_time > timer_limit:
            set_color((255, 0, 0))
            text_layer.text = "Times Up!"
            center_txt(text_layer)
            time.sleep(1)
            text_layer.text = "Game Over!"
            center_txt(text_layer)
            set_color((255, 255, 255))
            game_over = True
            break

        time.sleep(0.001)

