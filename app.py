from flask import Flask, request, jsonify
import wave
import io
import json
from vosk import Model, KaldiRecognizer
from openai import OpenAI
import os

app = Flask(__name__)

# === Загрузка Vosk (small модель для русского) ===
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("Модель Vosk не найдена! Скачайте vosk-model-small-ru-0.22 в папку model/")

vosk_model = Model(MODEL_PATH)
SAMPLE_RATE = 16000

# === Groq клиент ===
groq_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),  # задайте в Render Environment Variables
    base_url="https://api.groq.com/openai/v1"
)

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
        npc_role = data.get("npc_role", "NPC")
        location = data.get("location", "Лос-Сантос")
        weather = data.get("weather", "ясно")

        if not audio_data:
            return jsonify({"error": "No audio data"}), 400

        # Конвертируем список байтов в bytes
        audio_bytes = bytes(audio_data)

        # Преобразуем в WAV
        wav_buffer = audio_bytes_to_wav_buffer(audio_bytes)

        # STT через Vosk
        rec = KaldiRecognizer(vosk_model, SAMPLE_RATE)
        rec.SetWords(True)

        text = ""
        while True:
            data = wav_buffer.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text += res.get("text", "") + " "

        text = text.strip()
        if not text:
            return jsonify({"response": "Не расслышал, повтори."})

        # Формируем промпт для Groq
        prompt = f"""
Ты — {npc_role} в Лос-Сантосе.
Ты находишься на {location}, сейчас {weather}.
Твоя задача — отвечать коротко, в характере, по-русски.
Игрок говорит: "{text}"
Ответ:
"""

        # Запрос к Groq
        groq_response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7
        )

        answer = groq_response.choices[0].message.content.strip()

        return jsonify({"response": answer})

    except Exception as e:
        print("Ошибка:", str(e))
        return jsonify({"response": "Чё? Повтори!"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))