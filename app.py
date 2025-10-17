from flask import Flask, request, jsonify, render_template, send_from_directory
import pytesseract
from PIL import Image, ImageFilter
import base64, io, re, os, json, shutil

app = Flask(__name__)
DATA_FILE = 'data.json'

# --- Tesseract 自動検出 ---
tesseract_cmd = shutil.which("tesseract")
if tesseract_cmd is None:
    raise RuntimeError("Tesseract が見つかりません。Render設定で tesseract-ocr を追加してください。")
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


# --- データ読み書き ---
def load_data():
    if os.path.exists(DATA_FILE):
        return json.load(open(DATA_FILE, 'r', encoding='utf-8'))
    return {"収入": [], "支出": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# --- ページルーティング ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/list')
def list_page():
    return render_template('list.html')


# --- データAPI ---
@app.route('/data')
def data_api():
    return jsonify(load_data())


# --- 画像前処理 ---
def preprocess_image(img):
    img = img.convert('L')
    img = img.filter(ImageFilter.MedianFilter())
    basewidth = 1000
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    threshold = 150
    img = img.point(lambda x: 0 if x < threshold else 255)
    return img


# --- OCR処理（/ocr と /upload 両対応） ---
@app.route('/ocr', methods=['POST'])
@app.route('/upload', methods=['POST'])
def ocr():
    data = request.json.get('image') if request.is_json else None

    # JSON形式でない場合（FormData）
    if data is None and 'image' in request.files:
        img = Image.open(request.files['image'].stream)
    else:
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


# --- データ保存 ---
@app.route('/save', methods=['POST'])
def save():
    data = request.json
    all_data = load_data()
    all_data[data['type']].append({"item": data['item'], "amount": data['amount']})
    save_data(all_data)
    return jsonify({"status": "ok"})


# --- 静的ファイル (faviconなど) ---
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
