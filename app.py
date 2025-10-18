<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>子ども向けページ</title>
<style>
  body {
    font-family: 'Arial';
    background-color: #f0f8ff;
    text-align: center;
    margin: 0;
    padding: 0;
  }
  video, canvas {
    width: 90%;
    max-width: 400px;
    border-radius: 10px;
    margin: 10px auto;
  }
  button {
    display: block;
    margin: 10px auto;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
    cursor: pointer;
  }
  #result {
    margin-top: 15px;
    font-size: 18px;
    font-weight: bold;
  }
</style>
</head>
<body>
  <h2>📸 カメラで文字を読み取ろう！</h2>
  <video id="camera" autoplay playsinline></video>
  <canvas id="canvas" style="display:none;"></canvas>

  <button id="flipBtn">🔄 カメラ切り替え</button>
  <button id="captureBtn">📷 撮影する</button>
  <button onclick="location.href='/'">🏠 ホームに戻る</button>

  <p id="result"></p>

<script>
let useFront = false;
let stream;

async function startCamera() {
  if (stream) stream.getTracks().forEach(track => track.stop());
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: useFront ? "user" : "environment" }
    });
    document.getElementById('camera').srcObject = stream;
  } catch (err) {
    alert("カメラが利用できません: " + err.message);
  }
}

document.getElementById('flipBtn').onclick = () => {
  useFront = !useFront;
  startCamera();
};

document.getElementById('captureBtn').onclick = async () => {
  const video = document.getElementById('camera');
  const canvas = document.getElementById('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext('2d').drawImage(video, 0, 0);
  const imageData = canvas.toDataURL('image/png');

  document.getElementById('result').innerText = "🔍 認識中...";
  const res = await fetch("/ocr", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: imageData })
  });
  const data = await res.json();
  document.getElementById('result').innerText = 
    `📘 品目: ${data.item || "なし"} / 💰 金額: ${data.amount || "なし"}`;
};

startCamera();
</script>
</body>
</html>
