from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import os
import uuid
from vosk import Model, KaldiRecognizer

app = FastAPI()

# Загружаем модель один раз при старте
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model directory not found at {MODEL_PATH}")

model = Model(MODEL_PATH)
print("✅ Vosk model loaded")

# Хранилище активных сессий (в реальном проекте — лучше использовать Redis или TTL-кэш)
sessions = {}

@app.get("/health")
async def health():
    return {"status": "ok", "model": "vosk-small-ru-0.22"}

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    await websocket.accept()
    
    session_id = str(uuid.uuid4())
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    sessions[session_id] = rec
    
    try:
        # Отправляем session_id клиенту (опционально)
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
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
    finally:
        # Финальный результат
        final = rec.FinalResult()
        final_text = eval(final).get("text", "")
        if final_text:
            await websocket.send_json({"type": "final", "text": final_text})
        sessions.pop(session_id, None)
        await websocket.close()


# Запуск сервера (обязательно для Render.com)
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, workers=1)