from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import time
import cv2
import numpy as np
from utils import classify_image

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_server.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
CORS(app)

# Khởi tạo model nhận dạng tiền
money_model = cv2.dnn.readNetFromONNX("classifier.onnx")

def ocr_space_file(image_data, api_key='K88511949788957', overlay=False, engine=1):
    """
    Hàm gửi ảnh tới OCR.Space API
    """

    url = 'https://api.ocr.space/parse/image'

    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': 'vnm',  # Tiếng Việt
        'OCREngine': engine  # Sử dụng Engine 1 (mặc định) hoặc Engine 2
    }

    files = {
        'file': ('image.jpg', image_data, 'image/jpeg')
    }

    response = requests.post(url, files=files, data=payload)
    return response.json()

def process_money_recognition(image_data):
    """

    """
    try:
        # Chuyển đổi dữ liệu ảnh thành numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Nhận dạng tiền
        result = classify_image(img, money_model)
        return result
    except Exception as e:
        logging.error(f"Lỗi nhận dạng tiền: {str(e)}")
        raise e

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'endpoints': {
            'ocr': '/ocr (POST)',
            'money': '/money (POST)'
        }
    })

@app.route('/ocr', methods=['POST'])
def process_ocr():
    start_time = time.time()

    if 'image' not in request.files:
        logging.error("Không tìm thấy ảnh trong request")
        return jsonify({'error': 'Không tìm thấy ảnh'}), 400

    try:
        # Lấy file ảnh
        image_file = request.files['image']

        # Đọc dữ liệu ảnh
        image_data = image_file.read()

        # Xử lý OCR
        result = ocr_space_file(image_data, engine=2)

        # Kiểm tra kết quả
        if result['OCRExitCode'] == 1:
            processing_time = time.time() - start_time
            logging.info(f"Xử lý OCR thành công trong {processing_time:.2f} giây")

            return jsonify({
                'success': True,
                'text': result['ParsedResults'][0]['ParsedText'],
                'processing_time': processing_time
            })
        else:
            error_msg = result.get('ErrorMessage', 'Lỗi không xác định')
            logging.error(f"Lỗi OCR: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

    except Exception as e:
        logging.error(f"Lỗi xử lý OCR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/money', methods=['POST'])
def process_money():
    start_time = time.time()

    if 'image' not in request.files:
        logging.error("Không tìm thấy ảnh trong request")
        return jsonify({'error': 'Không tìm thấy ảnh'}), 400

    try:
        # Lấy file ảnh
        image_file = request.files['image']

        # Đọc dữ liệu ảnh
        image_data = image_file.read()

        # Xử lý nhận dạng tiền
        result = process_money_recognition(image_data)
        processing_time = time.time() - start_time
        logging.info(f"Xử lý nhận dạng tiền thành công trong {processing_time:.2f} giây")

        return jsonify({
            'success': True,
            'text': result,
            'processing_time': processing_time
        })

    except Exception as e:
        logging.error(f"Lỗi xử lý nhận dạng tiền: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logging.info("Khởi động server...")
    app.run(host='0.0.0.0', port=5000)


