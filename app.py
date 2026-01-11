from fastapi import FastAPI, WebSocket
import os
import uuid
from vosk import Model, KaldiRecognizer

app = FastAPI()

# Загрузка модели Vosk (один раз при старте)
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
    
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            # Основная логика Vosk: обрабатываем чанк
            if rec.AcceptWaveform(data):
                # Фраза завершена → полный результат
                result = rec.Result()
                text = eval(result).get("text", "")
                if text.strip():
                    await websocket.send_json({"type": "partial", "text": text})
            else:
                # Фраза ещё идёт → промежуточный результат
                partial = rec.PartialResult()
                partial_text = eval(partial).get("partial", "")
                if partial_text.strip():
                    await websocket.send_json({"type": "partial", "text": partial_text})
                    
    except Exception:
        # Любое отключение (включая быстрое) — просто выходим
        pass
    finally:
        # Обязательно вызываем FinalResult — даже если речь была короткой
        final = rec.FinalResult()
        final_text = eval(final).get("text", "")
            print(">>> FINAL RESULT:", repr(final_text))  # ← ДОБАВЬ ЭТО
        if final_text.strip():
            try:
                await websocket.send_json({"type": "final", "text": final_text})
            except:
                pass  # игнорируем, если соединение уже закрыто