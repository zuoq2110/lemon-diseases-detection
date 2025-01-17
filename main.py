import cv2
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf
import tkinter as tk
from tkinter import Label, Button
import time
import threading
import RPi.GPIO as GPIO
import pyrebase
from firebase_secrets import SECRETS
from helper import update_rottens, update_fresh

# Initialize FireBase DB.
firebase = pyrebase.initialize_app(SECRETS["FIREBASE"])
db = firebase.database()
# Servo setup
SERVO_1_PIN = 18
SERVO_2_PIN = 23
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_1_PIN, GPIO.OUT)
GPIO.setup(SERVO_2_PIN, GPIO.OUT)

servo1 = GPIO.PWM(SERVO_1_PIN, 50)  # 50 Hz (20ms period)
servo2 = GPIO.PWM(SERVO_2_PIN, 50)  # 50 Hz (20ms period)
servo1.start(0)
servo2.start(0)

# Hàm quay servo trong luồng riêng
def rotate_servo(servo, angle, reset_angle, delay=2):
    def _rotate():
        duty_cycle = 2 + (angle / 18)
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(1)  # Chờ servo di chuyển
        time.sleep(delay)  # Giữ vị trí
        duty_cycle_reset = 2 + (reset_angle / 18)
        servo.ChangeDutyCycle(duty_cycle_reset)
        time.sleep(1)
        servo.ChangeDutyCycle(0)  # Tắt tín hiệu
    threading.Thread(target=_rotate).start()

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path="model/lemon(background).lite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

FRESH_THRESHOLD = 0.5
ROTTEN_THRESHOLD = 0.5

# Camera settings
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("Cannot connect to the camera")
    exit()

# Counters
fresh_count = 0
rotten_count = 0

# GUI setup
root = tk.Tk()
root.title("Fruit Quality Detection")

# Labels to display counts
fresh_label = Label(root, text=f"Fresh Count: {fresh_count}", font=("Arial", 14))
fresh_label.pack()
rotten_label = Label(root, text=f"Rotten Count: {rotten_count}", font=("Arial", 14))
rotten_label.pack()

# Video display
video_label = Label(root)
video_label.pack()

# Quit button
def quit_app():
    cap.release()
    servo1.stop()
    servo2.stop()
    GPIO.cleanup()
    root.destroy()

quit_button = Button(root, text="Quit", command=quit_app, font=("Arial", 12))
quit_button.pack()

# Track time for next recognition
last_detection_time = time.time()

# Process frame function
def process_frame():
    global fresh_count, rotten_count, last_detection_time

    ret, frame = cap.read()
    if not ret:
        print("Cannot read frame from camera")
        return

    # Convert image to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Check if 5 seconds have passed since last detection
    if time.time() - last_detection_time >= 5:
        # Preprocess input for model
        frame_resized = cv2.resize(frame_rgb, (96, 96))
        input_data = np.expand_dims(frame_resized, axis=0).astype(np.float32) / 255.0

        # Run TFLite model
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_details[0]['index']).squeeze()

        # Get label based on highest probability
        predicted_index = np.argmax(predictions)

        current_prediction = "NO FRUIT"
        if predicted_index == 1 and predictions[1] > ROTTEN_THRESHOLD:
            current_prediction = "ROTTEN"
        elif predicted_index == 2 and predictions[2] > FRESH_THRESHOLD:
            current_prediction = "FRESH"

        # Update counts and control servos
        if current_prediction == "FRESH":
            fresh_count += 1
            rotate_servo(servo2, 90, 0)  # Quay servo 1
            time.sleep(1)
            rotate_servo(servo1, 90, 0)  # Quay servo 1
            update_fresh(db)

        elif current_prediction == "ROTTEN":
            rotten_count += 1
            rotate_servo(servo1, 90, 0)  # Quay servo 2
            
            update_rottens(db)

        # Update the last detection time
        last_detection_time = time.time()

    # Update GUI labels
    fresh_label.config(text=f"Fresh Count: {fresh_count}")
    rotten_label.config(text=f"Rotten Count: {rotten_count}")

    # Display video in GUI
    img_tk = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
    video_label.imgtk = img_tk
    video_label.configure(image=img_tk)

    video_label.after(10, process_frame)

# Start the application
process_frame()
root.mainloop()
