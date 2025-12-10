# 512-Final

# Tilt It! "Pock"-it Pocket Bop It — A 90s-Style Handheld Reaction Game

## Overview
**Tilt It!** is a 90s-era electronic reaction game inspired by *Bop-It* and *Brain Warp*, built using an **ESP32 Xiao**, **CircuitPython**, and multiple physical sensors including a **Rotary Encoder**, **ADXL345 Accelerometer**, and a **NeoPixel LED**.

Players react to on-screen commands—*Push it*, *Twist it*, *Forward*, *Backward*—within an ever-shrinking time limit across 10 levels. Each level increases complexity with more required actions and faster reaction windows.

---

## How to Play
1. Power the device with the side **On/Off switch**.
2. Use the **Rotary Encoder** to choose a difficulty:
   - Easy (20s per move)
   - Medium (10s)
   - Hard (5s)
   Press the encoder to confirm.
3. The game begins at **Level 1**.
4. Commands are shown on the OLED screen:
   - **Push it!** → Press the encoder button  
   - **Twist it!** → Rotate the encoder  
   - **Forward!** → Tilt device forward  
   - **Backward!** → Tilt device backward  
5. Complete all rounds to advance to the next level.
6. Wrong move or timeout → **Game Over**
   - Game returns automatically to difficulty selection.
7. Survive all 10 levels → **YOU WIN!**

---

## Features

### ✔ Difficulty Selection Menu
Accessible using the rotary encoder:
- **Easy** – 20s reaction window  
- **Medium** – 10s  
- **Hard** – 5s  

### ✔ Four Move Types
- Encoder **button press**
- Encoder **twist**
- **Forward tilt** (pitch threshold)
- **Backward tilt**

### ✔ Accelerometer Filtering & Calibration
- Startup zero calibration
- Exponential smoothing filter  
- Neutral-zone detection to avoid false triggers  
- Forward/backward thresholding based on pitch angle

### ✔ Ten-Level Game Progression
- Levels 1–4: Single-move rounds  
- Levels 5–6: Two-move randomization  
- Levels 7–10: Full 4-move set with increasing rounds  

### ✔ Game Over & Win Screens
OLED displays:
- `"Game Over"`  
- `"YOU WIN!"`  
- Auto-reset to difficulty screen

### ✔ NeoPixel Feedback
| Color | Meaning |
|-------|---------|
| Green | Correct move |
| Red | Incorrect / timeout |
| White | Reset/neutral state |

---

## Hardware Used

### Required Components
- **Xiao ESP32-C3**
- **SSD1306 128×64 OLED Display**
- **ADXL345 Accelerometer**
- **Rotary Encoder (with push button)**
- **1× NeoPixel LED**
- **LiPo Battery**
- **On/Off Switch**

### Additional Build Materials
- Custom PCB / perfboard (**no breadboards**)
- Female header connectors

---

## Electronic System Overview

### Key Connections
| Component | Pins |
|----------|------|
| OLED (I2C) | SCL, SDA |
| ADXL345 | SCL, SDA |
| Rotary Encoder | D8, D7 |
| Encoder Button | D9 |
| NeoPixel | D10 |
| Battery | VIN → Switch → ESP32 |


## Enclosure Design
Plywood laser cut enclosure
- Fits all components   
- Allows access to:
  - USB-C port  
  - Rotary encoder  
  - On/Off switch  
- Includes removable top panel for repairs  
- Designed for handheld use    

---

## Software Architecture

### Major Modules
- **Difficulty Menu** – Encoder navigation & selection  
- **Game Engine** – Level logic, timing, random command generation  
- **Move Detection**
  - Button press  
  - Encoder rotation  
  - Accelerometer tilt detection  
- **Filtering**
  - Startup calibration  
  - Smoothing filter (`alpha = 0.2`)  
- **Feedback System**
  - OLED messages  
  - NeoPixel color cues  


