import cv2
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf
import tkinter as tk
from tkinter import Label, Button
import time

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path="model/lemon(background).lite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

DIFFERENCE_THRESHOLD = 800000
FRESH_THRESHOLD = 0.5
ROTTEN_THRESHOLD = 0.5

# Camera settings
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

if not cap.isOpened():
    print("Không thể kết nối với camera")
    exit()

previous_frame = None
last_prediction = "NO FRUIT"
last_update_time = time.time()

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
    root.destroy()

quit_button = Button(root, text="Quit", command=quit_app, font=("Arial", 12))
quit_button.pack()

# Process frame function
def process_frame():
    global previous_frame, fresh_count, rotten_count, last_prediction, last_update_time

    ret, frame = cap.read()
    if not ret:
        print("Không thể đọc khung hình từ camera")
        return

    # Convert image to RGB and blur it
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_blurred = cv2.GaussianBlur(frame_rgb, (5, 5), 0)

    if previous_frame is not None:
        # Calculate difference between current and previous frame
        diff = cv2.absdiff(frame_blurred, previous_frame)
        diff_sum = np.sum(diff)

        if diff_sum > DIFFERENCE_THRESHOLD:
            # Preprocess input for model
            frame_resized = cv2.resize(frame_rgb, (96, 96))
            input_data = np.expand_dims(frame_resized, axis=0).astype(np.float32) / 255.0

            # Run TFLite model
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            predictions = interpreter.get_tensor(output_details[0]['index']).squeeze()
            print(predictions)

            # Get label based on highest probability
            predicted_index = np.argmax(predictions)
            print(predicted_index)
            current_prediction = "NO FRUIT"
            if predicted_index == 1 and predictions[1] > ROTTEN_THRESHOLD:
                current_prediction = "ROTTEN"
            elif predicted_index == 2 and predictions[2] > FRESH_THRESHOLD:
                current_prediction = "FRESH"

            # Update count if the prediction changes and satisfies time threshold
            current_time = time.time()
            if (
                # current_prediction != last_prediction
                 current_time - last_update_time > 5  # 2-second threshold
            ):
                # last_prediction = current_prediction
                last_update_time = current_time
                if current_prediction == "FRESH":
                    fresh_count += 1
                elif current_prediction == "ROTTEN":
                    rotten_count += 1

            # Update GUI labels
            fresh_label.config(text=f"Fresh Count: {fresh_count}")
            rotten_label.config(text=f"Rotten Count: {rotten_count}")

    # Display video in GUI
    img_tk = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
    video_label.imgtk = img_tk
    video_label.configure(image=img_tk)

    previous_frame = frame_blurred.copy()
    video_label.after(10, process_frame)

# Start the application
process_frame()
root.mainloop()
