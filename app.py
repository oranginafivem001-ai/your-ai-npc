from flask import Flask, request, jsonify
import wave
import io
import json
from vosk import Model, KaldiRecognizer
import os

app = Flask(__name__)

# Загрузка модели
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Vosk model not found in ./model/")

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
    print("=== [PYTHON DEBUG] НОВЫЙ ЗАПРОС ПОЛУЧЕН ===")
    print(f"Headers: {dict(request.headers)}")
    print(f"Content-Type: {request.content_type}")

    try:
        data = request.get_json()
        print(f"JSON получен: {type(data)}")

        if not 
            print("❌ ОШИБКА: запрос пустой")
            return jsonify({"player_text": "Ошибка: пустой запрос"}), 400

        audio_data = data.get("audioData")
        print(f"AudioData длина: {len(audio_data) if audio_data else 'None'}")

        if not audio_data:
            print("❌ ОШИБКА: нет аудио")
            return jsonify({"player_text": "Ошибка: нет аудио"}), 400

        print(f"📥 Получено {len(audio_data)} байт аудио")

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
    print(f"=== [PYTHON DEBUG] Запуск сервера на порту {port} ===")
    app.run(host='0.0.0.0', port=port, debug=False)