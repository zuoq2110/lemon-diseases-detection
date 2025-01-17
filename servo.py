import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


class Servo():
    def __init__(self, pin):
        """
        Chân GPIO để điều khiển servo
        Args:
            pin (int): Chân GPIO kết nối với servo.
        """
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)  # Tần số PWM là 50Hz, phù hợp cho hầu hết các servo
        self.pwm.start(0)  # Bắt đầu PWM với độ rộng xung 0%

    def set_angle(self, angle):
        """
        Thiết lập góc quay cho servo.
        Servo quay từ 0 đến 180 độ.
        Args:
            angle (int): Góc quay từ 0 đến 180 độ.
        """
        if 0 <= angle <= 180:
            duty_cycle = (angle / 18) + 2  # Công thức để chuyển đổi góc sang duty cycle
            self.pwm.ChangeDutyCycle(duty_cycle)  # Điều chỉnh duty cycle cho servo
            sleep(1)  # Đợi servo di chuyển đến vị trí
        else:
            print("Góc quay không hợp lệ! Chỉ hỗ trợ từ 0 đến 180 độ.")

    def stop(self):
        """
        Dừng PWM, tắt servo.
        """
        self.pwm.ChangeDutyCycle(0)
        GPIO.cleanup()


# Ví dụ sử dụng:
servo = Servo(18)  # Chân GPIO 18 kết nối với servo
servo.set_angle(90)  # Quay servo đến góc 90 độ
sleep(2)
servo.set_angle(0)   # Quay servo đến góc 0 độ
sleep(2)
servo.set_angle(180)  # Quay servo đến góc 180 độ
sleep(2)
servo.stop()  # Dừng PWM và tắt servo
