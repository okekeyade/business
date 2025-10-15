from flask import Flask, request, jsonify, send_from_directory
import pytesseract
from PIL import Image
import base64, io, re, os, json

app = Flask(__name__)
DATA_FILE = 'data.json'

# Tesseract設定
tesseract_root = r"C:\一時ファイル\ビジコン\2025\app\tesseract"
pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_root, "tesseract.exe")

def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE, 'r', encoding='utf-8'))
    return {"収入": [], "支出": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/list')
def list_page():
    return send_from_directory('.', 'list.html')

@app.route('/data')
def data_api():
    return jsonify(load_data())

@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.json['image']
    img_data = re.sub('^data:image/.+;base64,', '', data)
    img = Image.open(io.BytesIO(base64.b64decode(img_data)))
    text = pytesseract.image_to_string(img, lang='jpn+eng')

    lines = text.splitlines()
    item, amount = "", ""
    for ln in lines:
        if ln.strip():
            m = re.search(r'(\D+)\s*(\d+)', ln)
            if m:
                item, amount = m.group(1).strip(), m.group(2)
                break
    return jsonify({"item": item, "amount": amount})

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    all_data = load_data()
    all_data[data['type']].append({"item": data['item'], "amount": data['amount']})
    save_data(all_data)
    return jsonify({"status":"ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
