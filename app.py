from flask import Flask, request, jsonify
import os
import wave
import json
from vosk import Model, KaldiRecognizer

app = Flask(__name__)

# Загружаем модель один раз при старте
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise Exception(f"Model path {MODEL_PATH} does not exist")

model = Model(MODEL_PATH)
print("✅ Vosk model loaded successfully.")

@app.route('/stt', methods=['POST'])
def stt():
    try:
        # Проверяем, есть ли файл или raw audio data
        if 'audio' in request.files:
            audio_file = request.files['audio']
            audio_path = "/tmp/audio.wav"
            audio_file.save(audio_path)
        elif 'audioData' in request.json:
            # Если приходит массив байтов (как в твоём скрипте)
            audio_data = bytes(request.json['audioData'])
            audio_path = "/tmp/audio.wav"
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
        else:
            return jsonify({"error": "No audio data provided"}), 400

        # Открываем WAV
        wf = wave.open(audio_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            return jsonify({"error": "Audio must be 16kHz, mono, 16-bit PCM"}), 400

        # Распознавание
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)

        result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                result += res.get("text", "") + " "

        final_result = rec.FinalResult()
        final_text = json.loads(final_result).get("text", "").strip()

        # Очищаем временный файл
        os.remove(audio_path)

        return jsonify({
            "text": final_text,
            "success": True
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": "vosk-small-ru-0.22"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)