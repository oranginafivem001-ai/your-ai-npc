from flask import Flask, request, jsonify
import wave
import io
import json
from vosk import Model, KaldiRecognizer
import os

app = Flask(__name__)

MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Vosk model not found!")

vosk_model = Model(MODEL_PATH)
SAMPLE_RATE = 16000

def bytes_to_wav(audio_bytes):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)
    buf.seek(0)
    return buf

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        audio_data = data.get("audioData")
        if not audio_
            return jsonify({"player_text": "Нет аудио"}), 400

        audio_bytes = bytes(audio_data)
        wav = bytes_to_wav(audio_bytes)

        rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        text = ""
        while True:
            chunk = wav.read(4000)
            if not chunk: break
            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result())
                text += res.get("text", "") + " "

        text = text.strip() or "Не расслышал"
        print(f"✅ Распознано: '{text}'")
        return jsonify({"player_text": text})

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({"player_text": "Ошибка"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))