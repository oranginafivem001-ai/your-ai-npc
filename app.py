from flask import Flask, request, jsonify
import wave
import io
import json
from vosk import Model, KaldiRecognizer
import os

app = Flask(__name__)

# Путь к модели Vosk
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Vosk model not found in ./model/")

# Загрузка модели (русская, small)
vosk_model = Model(MODEL_PATH)
SAMPLE_RATE = 16000

def bytes_to_wav_buffer(audio_bytes):
    """Преобразует байты в WAV-буфер (16kHz, mono, 16-bit)"""
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
        # Получаем JSON
        data = request.get_json()
        if not data:
            return jsonify({"player_text": "Ошибка: пустой запрос"}), 400

        audio_data = data.get("audioData")
        if not audio_
            return jsonify({"player_text": "Ошибка: нет аудио"}), 400

        print(f"📥 Получено {len(audio_data)} байт")

        # Преобразуем в байты и в WAV
        audio_bytes = bytes(audio_data)
        wav_buffer = bytes_to_wav_buffer(audio_bytes)

        # Распознавание через Vosk
        rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        text = ""
        while True:
            chunk = wav_buffer.read(4000)
            if not chunk:
                break
            if rec.AcceptWaveform(chunk):
                result = json.loads(rec.Result())
                text += result.get("text", "") + " "

        text = text.strip()
        if not text:
            text = "Не расслышал"

        print(f"✅ Распознано: '{text}'")
        return jsonify({"player_text": text})

    except Exception as e:
        print(f"❌ Ошибка обработки: {str(e)}")
        return jsonify({"player_text": "Ошибка распознавания"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)