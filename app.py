from fastapi import FastAPI, WebSocket
import os
import uuid
from vosk import Model, KaldiRecognizer

app = FastAPI()

# Загрузка модели Vosk
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model directory not found at {MODEL_PATH}")

model = Model(MODEL_PATH)
print("✅ Vosk model loaded")

@app.get("/health")
async def health():
    return {"status": "ok", "model": "vosk-small-ru-0.22"}

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    
    try:
        # Опционально: отправить session_id
        await websocket.send_json({"type": "session", "session_id": session_id})
        
        while True:
            data = await websocket.receive_bytes()
            
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = eval(result).get("text", "")
                if text:
                    await websocket.send_json({"type": "partial", "text": text})
            else:
                partial = rec.PartialResult()
                partial_text = eval(partial).get("partial", "")
                if partial_text:
                    await websocket.send_json({"type": "partial", "text": partial_text})
                    
    except Exception as e:
        # При любом разрыве (включая быстрый) — просто завершаем
        pass
    finally:
        # Финальный результат — только если есть текст
        final = rec.FinalResult()
        final_text = eval(final).get("text", "")
        if final_text:
            try:
                await websocket.send_json({"type": "final", "text": final_text})
            except:
                pass  # игнорируем, если соединение уже закрыто
        # НЕ вызываем websocket.close() — он уже закрыт клиентом