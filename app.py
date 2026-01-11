from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import os
import uuid
from vosk import Model, KaldiRecognizer

app = FastAPI()

# Загружаем модель один раз
MODEL_PATH = "./model"
if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model not found at {MODEL_PATH}")

model = Model(MODEL_PATH)
print("✅ Vosk model loaded")

# Хранилище активных сессий: session_id → recognizer
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
        # Отправляем клиенту session_id
        await websocket.send_json({"type": "session", "session_id": session_id})
        
        while True:
            data = await websocket.receive_bytes()
            
            if rec.AcceptWaveform(data):
                res = rec.Result()
                await websocket.send_json({"type": "partial", "text": eval(res).get("text", "")})
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
        # Финальный результат при закрытии
        final = rec.FinalResult()
        final_text = eval(final).get("text", "")
        if final_text:
            await websocket.send_json({"type": "final", "text": final_text})
        sessions.pop(session_id, None)
        await websocket.close()