import cv2
import requests

# Hàm gửi ảnh tới OCR.Space API
def ocr_space_file(filename, api_key='K88511949788957', overlay=False, engine=1):
    with open(filename, 'rb') as f:
        img_data = f.read()

    # URL của OCR.Space API
    url = 'https://api.ocr.space/parse/image'

    # Tạo dữ liệu gửi tới API
    payload = {
        'isOverlayRequired': overlay,  # Kiểm tra xem có cần overlay không
        'apikey': api_key,
        'language': 'vnm',  # Tiếng Việt
        'OCREngine': engine  # Sử dụng Engine 1 (mặc định) hoặc Engine 2
    }

    # Gửi yêu cầu POST
    files = {
        'file': (filename, img_data, 'image/jpeg')  # Đảm bảo MIME type là 'image/jpeg' cho file .jpg
    }

    response = requests.post(url, files=files, data=payload)

    # Phân tích kết quả trả về
    result = response.json()

    # Kiểm tra lỗi và hiển thị chi tiết lỗi
    if 'ErrorDetails' in result:
        print("Chi tiết lỗi: ", result['ErrorDetails'])
    if result['OCRExitCode'] == 1:
        print("Nhận diện văn bản thành công!")
        print("Văn bản nhận được: ")
        print(result['ParsedResults'][0]['ParsedText'])
    else:
        print("Có lỗi xảy ra:", result['ErrorMessage'])

# Chạy chương trình với ảnh có sẵn
if __name__ == "__main__":
    # Thay thế đường dẫn ảnh có sẵn ở đây
    image_file = "./test/3.png"  # Ví dụ: "captured_image.jpg"
    ocr_space_file(image_file, engine=2)  # Gửi ảnh và nhận kết quả OCR với Engine 2
