from flask import Flask, render_template, jsonify, request, send_from_directory
import pytesseract, os, io, re, json, shutil
from PIL import Image, ImageFilter
import base64

app = Flask(__name__)

# ---------- 基本設定 ----------
DATA_FILE = 'data.json'
tesseract_cmd = shutil.which("tesseract")
if tesseract_cmd is None:
    raise RuntimeError("Tesseract が見つかりません")
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


# ---------- データ操作 ----------
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE, 'r', encoding='utf-8'))
    return {"収入": [], "支出": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- ページ ----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/kids')
def kids_page():
    return render_template('kids.html')

@app.route('/adult')
def adult_page():
    return render_template('adult.html')

@app.route('/list')
def list_page():
    return render_template('list.html')


# ---------- API ----------
@app.route('/data')
def data_api():
    return jsonify(load_data())


@app.route('/ocr', methods=['POST'])
def ocr():
    data = request.json['image']
    img_data = re.sub('^data:image/.+;base64,', '', data)
    img = Image.open(io.BytesIO(base64.b64decode(img_data)))
    img = preprocess_image(img)
    text = pytesseract.image_to_string(img, lang='jpn+eng', config='--psm 6 --oem 1')

    item, amount = "", ""
    for ln in text.splitlines():
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
    return jsonify({"status": "ok"})


# ---------- 静的ファイル ----------
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


# ---------- 前処理 ----------
def preprocess_image(img):
    img = img.convert('L')
    img = img.filter(ImageFilter.MedianFilter())
    img = img.resize((1000, int(img.height * 1000 / img.width)))
    img = img.point(lambda x: 0 if x < 150 else 255)
    return img


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
