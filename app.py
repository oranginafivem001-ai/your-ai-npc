from flask import Flask, request, jsonify
import wave
import io
import json
from vosk import Model, KaldiRecognizer
import os

app = Flask(__name__)

# === Загрузка Vosk (small модель для русского) ===
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Модель Vosk не найдена! Скачайте vosk-model-small-ru-0.22 в папку model/")

vosk_model = Model(MODEL_PATH)
SAMPLE_RATE = 16000

def audio_bytes_to_wav_buffer(audio_bytes):
    """Преобразует байты в WAV-буфер (16kHz, mono)"""
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)
    buffer.seek(0)
    return buffer

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        data = request.get_json()
        audio_data = data.get("audioData")  # список чисел (байты)

        if not audio_data:
            return jsonify({"player_text": "Ошибка: нет аудио"}), 400

        # Конвертируем список байтов в bytes
        audio_bytes = bytes(audio_data)

        # Преобразуем в WAV
        wav_buffer = audio_bytes_to_wav_buffer(audio_bytes)

        # STT через Vosk
        rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)

        text = ""
        while True:
            chunk = wav_buffer.read(4000)
            if not chunk:
                break
            if rec.AcceptWaveform(chunk):
                res = json.loads(rec.Result())
                text += res.get("text", "") + " "

        text = text.strip()
        if not text:
            text = "Не расслышал"

        print(f"✅ Распознано: '{text}'")
        return jsonify({"player_text": text})

    except Exception as e:
        print("❌ Ошибка:", str(e))
        return jsonify({"player_text": "Ошибка распознавания"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))