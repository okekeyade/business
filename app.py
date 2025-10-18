from flask import Flask, render_template, jsonify, request, send_from_directory, current_app
import pytesseract, os, io, re, json, shutil, traceback
from PIL import Image, ImageFilter
import base64

app = Flask(__name__)

# ---------- 基本設定 ----------
DATA_FILE = 'data.json'

# tesseract の検出（例外を投げない）
tesseract_cmd = shutil.which("tesseract")
if tesseract_cmd is None:
    app.logger.warning("Tesseract が見つかりません。OCR 機能は無効化されます。")
    TESSERACT_AVAILABLE = False
else:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    TESSERACT_AVAILABLE = True

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

# ---------- 前処理 ----------
def preprocess_image(img):
    try:
        img = img.convert('L')
        img = img.filter(ImageFilter.MedianFilter())
        basewidth = 1000
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), Image.ANTIALIAS)
        threshold = 150
        img = img.point(lambda x: 0 if x < threshold else 255)
        return img
    except Exception:
        current_app.logger.error("画像前処理でエラー\n" + traceback.format_exc())
        raise

# ---------- OCR（/ocr と /upload の両対応） ----------
@app.route('/ocr', methods=['POST'])
@app.route('/upload', methods=['POST'])
def ocr():
    if not TESSERACT_AVAILABLE:
        return jsonify({"error": "Tesseract がサーバ上にインストールされていません。管理者に確認してください。"}), 500

    try:
        # JSONで dataURL が送られた場合
        if request.is_json:
            data = request.json.get('image')
            if not data:
                return jsonify({"error": "image フィールドがありません"}), 400
            img_data = re.sub('^data:image/.+;base64,', '', data)
            img = Image.open(io.BytesIO(base64.b64decode(img_data)))
        # FormDataからのアップロード（blob）
        elif 'image' in request.files:
            img = Image.open(request.files['image'].stream)
        elif 'file' in request.files:
            img = Image.open(request.files['file'].stream)
        else:
            return jsonify({"error": "画像が送信されていません"}), 400

        # 前処理
        img = preprocess_image(img)

        # OCR 実行
        text = pytesseract.image_to_string(img, lang='jpn+eng', config='--psm 6 --oem 1')

        # 文字列解析（シンプル）
        item, amount = "", ""
        for ln in text.splitlines():
            if ln.strip():
                m = re.search(r'(\D+)\s*(\d+)', ln)
                if m:
                    item, amount = m.group(1).strip(), m.group(2)
                    break

        return jsonify({"item": item, "amount": amount})
    except Exception:
        current_app.logger.error("OCR処理で例外\n" + traceback.format_exc())
        return jsonify({"error": "OCR 処理中にサーバでエラーが発生しました"}), 500

@app.route('/save', methods=['POST'])
def save():
    try:
        data = request.json
        all_data = load_data()
        t = data.get('type', '支出')
        all_data.setdefault(t, []).append({"item": data.get('item',''), "amount": data.get('amount','')})
        save_data(all_data)
        return jsonify({"status": "ok"})
    except Exception:
        current_app.logger.error("保存処理で例外\n" + traceback.format_exc())
        return jsonify({"error":"保存に失敗しました"}), 500

# ---------- 静的ファイル ----------
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
