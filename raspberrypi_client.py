import cv2
import requests
import time
import numpy as np
import RPi.GPIO as GPIO
import pyttsx3
import os


class RaspberryClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.cap = None
        self.frame_width = 640
        self.frame_height = 480
        
        # Thiết lập GPIO
        GPIO.setmode(GPIO.BCM)
        # Nút OCR - GPIO 18
        GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Nút Money - GPIO 23
        GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Nút Quit - GPIO 24
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Biến để theo dõi trạng thái nút
        self.last_button_state = {
            18: True,  # True = không nhấn, False = đang nhấn
            23: True,
            24: True
        }
        
        # Khởi tạo text-to-speech engine
        self.engine = pyttsx3.init()
        
        # Thiết lập giọng nói tiếng Việt
        voices = self.engine.getProperty('voices')
        vietnamese_voice = None
        
        # Tìm giọng tiếng Việt
        for voice in voices:
            if 'vietnamese' in voice.name.lower():
                vietnamese_voice = voice
                break
        
        if vietnamese_voice:
            self.engine.setProperty('voice', vietnamese_voice.id)
        else:
            # Nếu không tìm thấy giọng tiếng Việt, sử dụng espeak
            os.system('espeak -v vi "Đang sử dụng giọng đọc tiếng Việt"')
            self.engine.setProperty('voice', 'vi')
        
        # Điều chỉnh tốc độ nói
        self.engine.setProperty('rate', 150)  # Tốc độ mặc định là 200

    def speak(self, text):
        """Chuyển văn bản thành giọng nói"""
        try:
            # Thử sử dụng pyttsx3 trước
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            try:
                # Nếu pyttsx3 thất bại, sử dụng espeak
                os.system(f'espeak -v vi "{text}"')
            except Exception as e2:
                print(f"Lỗi khi chuyển văn bản thành giọng nói: {str(e2)}")

    def check_button(self, pin):
        current_state = GPIO.input(pin)
        if current_state != self.last_button_state[pin]:
            self.last_button_state[pin] = current_state
            if current_state == False:  # Nút được nhấn (active low)
                return True
        return False

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Lỗi: Không thể mở webcam")
            return False

        # Thiết lập độ phân giải
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        return True

    def compress_image(self, image):
        # Nén ảnh để giảm kích thước
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        _, encoded_img = cv2.imencode('.jpg', image, encode_param)
        return encoded_img.tobytes()

    def capture_and_send(self, mode="ocr"):
        ret, frame = self.cap.read()
        if not ret:
            print("Lỗi: Không thể đọc frame")
            return False

        try:
            # Nén ảnh
            compressed_image = self.compress_image(frame)

            # Gửi ảnh lên server
            files = {'image': ('image.jpg', compressed_image, 'image/jpeg')}
            endpoint = "/money" if mode == "money" else "/ocr"
            response = requests.post(
                f"{self.server_url}{endpoint}",
                files=files,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print("\n=== Kết quả nhận dạng ===")
                    print(result['text'])
                    print(f"Thời gian xử lý: {result.get('processing_time', 0):.2f} giây")
                    print("=========================")
                    
                    # Kiểm tra kết quả trống
                    if not result['text'].strip():
                        if mode == "money":
                            self.speak("Không tìm thấy tờ tiền nào trong ảnh")
                        else:
                            self.speak("Không có văn bản nào được tìm thấy")
                    else:
                        # Chuyển kết quả thành giọng nói
                        if mode == "money":
                            self.speak(f"Đây là tờ tiền {result['text']}")
                        else:
                            self.speak(result['text'])
                else:
                    error_msg = f"Lỗi {mode}: {result.get('error', 'Lỗi không xác định')}"
                    print(error_msg)
                    self.speak("Không thể nhận dạng, vui lòng thử lại")
            else:
                error_msg = f"Lỗi: Server trả về mã {response.status_code}"
                print(error_msg)
                print("Response:", response.text)
                self.speak("Có lỗi xảy ra, vui lòng thử lại")

        except requests.exceptions.ConnectionError:
            error_msg = "Lỗi: Không thể kết nối đến server"
            print(error_msg)
            print(f"URL server: {self.server_url}")
            self.speak("Không thể kết nối đến máy chủ")
        except requests.exceptions.Timeout:
            error_msg = "Lỗi: Server không phản hồi sau 30 giây"
            print(error_msg)
            self.speak("Máy chủ không phản hồi, vui lòng thử lại")
        except Exception as e:
            error_msg = f"Lỗi: {str(e)}"
            print(error_msg)
            self.speak("Có lỗi xảy ra, vui lòng thử lại")

    def run(self):
        if not self.start_camera():
            return

        print("\n=== Hướng dẫn sử dụng ===")
        print("Nút GPIO 18: Nhận dạng văn bản")
        print("Nút GPIO 23: Nhận dạng tiền mặt")
        print("Nút GPIO 24: Thoát chương trình")
        print("=========================")
        
        # Phát âm hướng dẫn
        self.speak("Chào mừng bạn đến với hệ thống nhận dạng")
        time.sleep(1)  # Đợi 1 giây
        self.speak("Nhấn nút 18 để nhận dạng văn bản")
        time.sleep(0.5)  # Đợi 0.5 giây
        self.speak("Nhấn nút 23 để nhận dạng tiền mặt")
        time.sleep(0.5)  # Đợi 0.5 giây
        self.speak("Nhấn nút 24 để thoát chương trình")

        current_mode = "menu"  # Thêm biến theo dõi chế độ hiện tại

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Lỗi: Không thể đọc frame")
                break

            # Hiển thị frame
            cv2.imshow('Webcam', frame)

            # Kiểm tra các nút GPIO
            if self.check_button(18):  # Nút OCR
                current_mode = "ocr"
                self.speak("Bạn đã chọn nhận dạng văn bản")
                time.sleep(0.5)  # Đợi 0.5 giây
                self.speak("Bạn đã nhấn nút 18, chức năng nhận dạng văn bản")
                time.sleep(0.5)  # Đợi 0.5 giây
                self.speak("Đang nhận dạng văn bản")
                self.capture_and_send(mode="ocr")
            elif self.check_button(23):  # Nút Money
                current_mode = "money"
                self.speak("Bạn đã chọn nhận dạng tiền mặt")
                time.sleep(0.5)  # Đợi 0.5 giây
                self.speak("Bạn đã nhấn nút 23, chức năng nhận dạng tiền mặt")
                time.sleep(0.5)  # Đợi 0.5 giây
                self.speak("Đang nhận dạng tiền mặt")
                self.capture_and_send(mode="money")
            elif self.check_button(24):  # Nút Quit
                if current_mode != "menu":
                    self.speak("Quay về menu chính")
                    time.sleep(0.5)
                    current_mode = "menu"
                    self.speak("Nhấn nút 18 để nhận dạng văn bản")
                    time.sleep(0.5)
                    self.speak("Nhấn nút 23 để nhận dạng tiền mặt")
                    time.sleep(0.5)
                    self.speak("Nhấn nút 24 để thoát chương trình")
                else:
                    self.speak("Bạn đã chọn thoát chương trình")
                    time.sleep(0.5)
                    self.speak("Bạn đã nhấn nút 24, chức năng thoát chương trình")
                    time.sleep(0.5)
                    self.speak("Tạm biệt")
                    break

            # Vẫn giữ xử lý phím cho mục đích debug
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                if current_mode != "menu":
                    self.speak("Quay về menu chính")
                    time.sleep(0.5)
                    current_mode = "menu"
                    self.speak("Nhấn nút 18 để nhận dạng văn bản")
                    time.sleep(0.5)
                    self.speak("Nhấn nút 23 để nhận dạng tiền mặt")
                    time.sleep(0.5)
                    self.speak("Nhấn nút 24 để thoát chương trình")
                else:
                    break

        # Dọn dẹp
        self.cap.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()

if __name__ == "__main__":
    # URL của server
    SERVER_URL = "https://057f-2a09-bac1-7a80-10-00-247-23.ngrok-free.app"

    print(f"Kết nối đến server: {SERVER_URL}")
    client = RaspberryClient(SERVER_URL)
    client.run()