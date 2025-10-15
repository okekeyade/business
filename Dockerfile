# ベースイメージ
FROM python:3.13-slim

# Tesseract + 日本語データをインストール
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-jpn && \
    rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# ファイルをコピー
COPY . /app

# Python パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# Flask ポート公開
EXPOSE 5000

# アプリ起動
CMD ["python3", "app.py"]
