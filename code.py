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

# Initializing rotary encoder set up for rotation
encoder = RotaryEncoder(board.D8, board.D7, debounce_ms= 3, pulses_per_detent=3)

# Initializing rotary encoder set up for button
btn = DigitalInOut(board.D9)
btn.direction = Direction.INPUT
btn.pull = Pull.UP
prev_state = btn.value

# Create the display object (display setup)
i2c = busio.I2C(board.SCL, board.SDA)
display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)

# Accelerometer
accelerometer = adafruit_adxl34x.ADXL345(i2c)

# Optional: increase data rate for faster response
#accelerometer.data_rate = adafruit_adxl34x.DataRate.RATE_100_HZ

# Group
# Container that holds everything you want to draw on the screen
splash = displayio.Group()
display.root_group = splash

# Create label
text_layer = label.Label(terminalio.FONT, text="")
splash.append(text_layer)

def cent_txt(text):
    # Center the label/text
    text.x = (display.width - text_layer.bounding_box[2]) // 2
    text.y = (display.height - text_layer.bounding_box[3]) // 2
    
# Create variable to keep track of players response time 
start_time = time.monotonic()
response_time = None

# Detect the ecoders position 
prev_encoder_pos = encoder.position

# --- Tilt detection setup ---
alpha = 0.2       # EMA smoothing factor
pitch_filtered = 0

# Angle thresholds (degrees) for tilt detection set-up
FORWARD_ANGLE = 25
BACKWARD_ANGLE = -25
EXIT_ANGLE = 5 #hysterisis
state = "neutral" 
neutral_start = None # for measuring how long it stays neutral
twist_cooldown = 0.3  # seconds to ignore after a twist
last_success_time = 0

# --- Settin up neopixel
pixel_pin = board.D10
num_pixels = 1
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.3, auto_write=True)

# Defining the 5 colors picked
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Function to set NeoPixel color
def set_color(color):
    pixels.fill(color)
    pixels.brightness = 0.03
    pixels.show()

# --- X and Y-axis calibration only ---
# zero offset calibration
def calibrate_zero(accel, samples=50, delay=0.01):
    x_list, y_list = [], []
    for _ in range(samples):
        x, y, _ = accel.acceleration
        x_list.append(x)
        y_list.append(y)
        time.sleep(delay)
    x_offset = sum(x_list) / samples
    y_offset = sum(y_list) / samples
    return x_offset, y_offset

def get_pitch(ax, ay, az):
    return math.degrees(math.atan2(ay, math.sqrt(ax*ax + az*az)))


def detect_neutral(pitch_filtered):
    global state, neutral_start
    if -EXIT_ANGLE < pitch_filtered < EXIT_ANGLE:
        if state != "neutral":
            state = "neutral"
            neutral_start = time.monotonic()
            return True
    return False

def detect_forwardTilt(pitch_filtered):
    """Return True only once per forward tilt until neutral is reached."""
    global state
    # Forward tilt
    if pitch_filtered > FORWARD_ANGLE and state != "forward":
        state = "forward"
        return True
    else:
        detect_neutral(pitch_filtered)
        return False

def detect_backwardTilt(pitch_filtered):
    """Return True only once per backward tilt until neutral is reached."""
    global state
    if pitch_filtered < BACKWARD_ANGLE and state != "backward":
        state = "backward"
        return True
    else:
        detect_neutral(pitch_filtered)
        return False

# --- Unified Input Detection ---
def update_inputs():
    global prev_encoder_pos, prev_state

    encoder.update()
    delta = encoder.position - prev_encoder_pos
    twist_detected = False
    if abs(delta) >= 1:
        prev_encoder_pos = encoder.position
        twist_detected = True

    cur_state = btn.value
    push_detected = False
    if prev_state and not cur_state:
        push_detected = True
    prev_state = cur_state

    return push_detected, twist_detected


# --- Player response uses ONLY update_inputs ---
def player_response(pitch_filtered):
    push, twist = update_inputs()

    # tilt is NOT updated inside this function anymore
    tilt_fwd = detect_forwardTilt(pitch_filtered)
    tilt_back = detect_backwardTilt(pitch_filtered)

    if push:
        return "Push it!"
    if twist:
        return "Twist it!"
    if tilt_fwd:
        return "Forward!"
    if tilt_back:
        return "Backward!"

    return None


def twistIt():
    text_layer.text = "Twist it!"
    cent_txt(text_layer)

def pushIt():
    text_layer.text = "Push it!"
    cent_txt(text_layer)
    
def forward():
    text_layer.text = "Forward!"
    cent_txt(text_layer)

def backward():
    text_layer.text = "Backward!"
    cent_txt(text_layer)
plays = [
    {"label": "Twist it!", "func": twistIt, "check": lambda p: p == "Twist it!"},
    {"label": "Push it!",  "func": pushIt,  "check": lambda p: p == "Push it!"},
    {"label": "Forward!", "func": forward, "check": lambda p: p == "Forward!"},
       {"label": "Backward!","func": backward,"check": lambda p: p == "Backward!"},
]

game_over = False
x_b, y_b = calibrate_zero(accelerometer, samples=50, delay=0.01)

while not game_over:
    set_color((255, 150, 0)) # Yellow
    chosen = random.choice(plays)
    prev_encoder_pos = encoder.position
    chosen["func"]()
    expected = chosen["label"]
    #prev_encoder_pos = encoder.position
    start_time = time.monotonic()

    while True:
        # -------- TILT UPDATE --------
        ax, ay, az = accelerometer.acceleration
        pitch_raw = get_pitch(ax - x_b, ay - y_b, az)
        pitch_filtered = alpha * pitch_raw + (1 - alpha) * pitch_filtered

        # -------- PLAYER MOVE --------
        player_move = player_response(pitch_filtered)

        # Correct move
        if player_move == expected:
            set_color((0, 255, 0)) # Green
            text_layer.text = "Nice!"
            cent_txt(text_layer)
            time.sleep(0.7)
            state = "neutral"
            break

        # Wrong move
        if player_move:
            set_color((255, 0, 0))  # Revert to red
            text_layer.text = "Wrong move!"
            cent_txt(text_layer)
            time.sleep(1)
            text_layer.text = "Game Over!"
            cent_txt(text_layer)
            set_color((255, 255, 255))
            game_over = True
            print(expected)
            print(player_move)
            break

        # Timeout
        if time.monotonic() - start_time > 5:
            set_color((255, 0, 0))  # Revert to red
            text_layer.text = "Times Up!"
            cent_txt(text_layer)
            time.sleep(1)
            text_layer.text = "Game Over!"
            cent_txt(text_layer)
            set_color((255, 255, 255))
            game_over = True
            break

        time.sleep(0.001)
        

