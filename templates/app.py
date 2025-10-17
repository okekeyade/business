from flask import Flask, request, jsonify, send_from_directory
import pytesseract
from PIL import Image, ImageFilter
import base64, io, re, os, json, shutil

app = Flask(__name__)
DATA_FILE = 'data.json'

# Linux で tesseract を自動検出
tesseract_cmd = shutil.which("tesseract")
if tesseract_cmd is None:
    raise RuntimeError("Tesseract が見つかりません")
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

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

def preprocess_image(img):
    # 1. グレースケール化
    img = img.convert('L')

    # 2. ノイズ除去
    img = img.filter(ImageFilter.MedianFilter())

    # 3. サイズ調整（横幅1000px）
    basewidth = 1000
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)

    # 4. 二値化
    threshold = 150
    img = img.point(lambda x: 0 if x < threshold else 255)

    return img

@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.json['image']
    img_data = re.sub('^data:image/.+;base64,', '', data)
    img = Image.open(io.BytesIO(base64.b64decode(img_data)))

    # 前処理
    img = preprocess_image(img)

    # OCR 実行（PSM 6 + OEM 1）
    text = pytesseract.image_to_string(img, lang='jpn+eng', config='--psm 6 --oem 1')

    # 文字列解析
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

@app.route('/upload', methods=['POST'])
def upload():
    # /ocr と同じ処理を再利用
    return ocr()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
