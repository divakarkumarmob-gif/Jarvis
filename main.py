"""
KIRA — Main Entry Point
FastAPI app with all routes
"""

import os
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import io

load_dotenv()

from core.api_manager import api_manager
from core.kira_brain import kira_brain
from core.pin_security import pin_security
from core.wake_word import session_manager
from voice.tts import tts_manager
from voice.stt import stt_manager

app = FastAPI(title="Kira AI", version="1.0.0")

# ============================================
# Request Models
# ============================================

class ChatRequest(BaseModel):
    text: str

class PinRequest(BaseModel):
    pin: str

class ChangePinRequest(BaseModel):
    old_pin: str
    new_pin: str

class TTSRequest(BaseModel):
    text: str

class ModeRequest(BaseModel):
    mode: str

class ProviderRequest(BaseModel):
    provider: str
    model: str = ""
    api_key: str = ""
    url: str = ""

# ============================================
# Health
# ============================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Kira is live!", "version": "1.0.0"}

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "kira": "online",
        "session_active": session_manager.is_active,
        "mode": kira_brain.mode,
        "tts_provider": tts_manager.provider
    })

@app.get("/status")
async def status():
    return JSONResponse({
        "session": session_manager.get_status(),
        "mode": kira_brain.mode,
        "tts_provider": tts_manager.provider,
        "available_apis": [p.value for p in api_manager.get_available_providers()],
        "offline_mode": api_manager.offline_mode,
        "pin_required": pin_security.needs_pin_check(),
        "locked": pin_security.is_locked()
    })

# ============================================
# PIN Security
# ============================================

@app.post("/pin/verify")
async def verify_pin(req: PinRequest):
    success, message = pin_security.verify_pin(req.pin)
    if success:
        session_manager.activate()
        return JSONResponse({"success": True, "message": message})
    raise HTTPException(status_code=401, detail=message)

@app.post("/pin/change")
async def change_pin(req: ChangePinRequest):
    success, message = pin_security.change_pin(req.old_pin, req.new_pin)
    if success:
        return JSONResponse({"success": True, "message": message})
    raise HTTPException(status_code=400, detail=message)

@app.get("/pin/status")
async def pin_status():
    return JSONResponse({
        "needs_pin": pin_security.needs_pin_check(),
        "locked": pin_security.is_locked()
    })

# ============================================
# Chat
# ============================================

@app.post("/chat")
async def chat(req: ChatRequest):
    if pin_security.needs_pin_check():
        return JSONResponse({"error": "pin_required", "message": "Boss pehle PIN batao"}, status_code=401)

    announcement, should_process = session_manager.process_text(req.text)
    if announcement and not should_process:
        return JSONResponse({"response": announcement, "session_active": session_manager.is_active})

    if not session_manager.is_active:
        return JSONResponse({"response": "Kira bolo pehle wake karo", "session_active": False})

    response, provider = await kira_brain.think(req.text)
    return JSONResponse({"response": response, "provider": provider, "mode": kira_brain.mode})

# ============================================
# Voice
# ============================================

@app.post("/voice/chat")
async def voice_chat(audio: UploadFile = File(...)):
    if pin_security.needs_pin_check():
        audio_resp = await tts_manager.speak("Boss pehle PIN batao")
        if audio_resp:
            return StreamingResponse(io.BytesIO(audio_resp), media_type="audio/mpeg")
        raise HTTPException(status_code=401, detail="PIN required")

    audio_bytes = await audio.read()
    text = await stt_manager.transcribe(audio_bytes, audio.filename or "audio.webm")

    if not text:
        msg = "Awaaz samajh nahi aayi"
        audio_resp = await tts_manager.speak(msg)
        if audio_resp:
            return StreamingResponse(io.BytesIO(audio_resp), media_type="audio/mpeg")
        return JSONResponse({"error": msg})

    announcement, should_process = session_manager.process_text(text)
    if announcement and not should_process:
        audio_resp = await tts_manager.speak(announcement)
        if audio_resp:
            return StreamingResponse(io.BytesIO(audio_resp), media_type="audio/mpeg")
        return JSONResponse({"response": announcement})

    if not session_manager.is_active:
        msg = "Kira bolo pehle"
        audio_resp = await tts_manager.speak(msg)
        if audio_resp:
            return StreamingResponse(io.BytesIO(audio_resp), media_type="audio/mpeg")
        return JSONResponse({"response": msg})

    response, provider = await kira_brain.think(text)
    audio_resp = await tts_manager.speak(response)

    if audio_resp:
        return StreamingResponse(
            io.BytesIO(audio_resp),
            media_type="audio/mpeg",
            headers={"X-Transcript": text, "X-Response": response, "X-Provider": provider}
        )

    return JSONResponse({"transcript": text, "response": response, "provider": provider})

# ============================================
# TTS
# ============================================

@app.post("/tts")
async def text_to_speech(req: TTSRequest):
    audio = await tts_manager.speak(req.text)
    if audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg")
    raise HTTPException(status_code=500, detail="TTS failed")

@app.post("/tts/switch")
async def switch_tts(req: ProviderRequest):
    if req.provider == "custom":
        msg = tts_manager.set_custom_provider(req.url, req.api_key, req.model)
    else:
        msg = tts_manager.switch_provider(req.provider)
    return JSONResponse({"message": msg})

# ============================================
# Mode & Offline
# ============================================

@app.post("/mode")
async def set_mode(req: ModeRequest):
    success = kira_brain.set_mode(req.mode)
    if success:
        return JSONResponse({"success": True, "mode": req.mode})
    raise HTTPException(status_code=400, detail="Invalid mode")

@app.post("/offline/on")
async def offline_on():
    msg = await api_manager.switch_offline()
    return JSONResponse({"message": msg, "offline": True})

@app.post("/offline/off")
async def offline_off():
    msg = await api_manager.switch_online()
    return JSONResponse({"message": msg, "offline": False})

# ============================================
# Session
# ============================================

@app.post("/session/wake")
async def wake_kira():
    msg = session_manager.activate()
    return JSONResponse({"message": msg, "active": True})

@app.post("/session/sleep")
async def sleep_kira():
    msg = session_manager.deactivate()
    return JSONResponse({"message": msg, "active": False})

# ============================================
# Background timeout
# ============================================

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(timeout_checker())

async def timeout_checker():
    while True:
        await asyncio.sleep(5)
        msg = session_manager.check_timeout()
        if msg:
            await tts_manager.speak(msg)


# ============================================
# Memory Routes — added in Phase 3
# ============================================

from memory.conversation import conversation_memory
from memory.people import people_memory
from memory.photos import photo_memory
from features.search import search_manager
from features.announcements import announcements

class PersonRequest(BaseModel):
    name: str
    relation: str = ""
    details: dict = {}

class SearchRequest(BaseModel):
    query: str

@app.on_event("startup")
async def init_memory():
    await conversation_memory.init_db()
    await people_memory.init_db()

@app.post("/memory/person/add")
async def add_person(req: PersonRequest):
    msg = await people_memory.add_person(req.name, req.relation, req.details)
    return JSONResponse({"message": msg})

@app.get("/memory/person/{name}")
async def get_person(name: str):
    person = await people_memory.get_person(name)
    if person:
        return JSONResponse(person)
    raise HTTPException(status_code=404, detail=f"{name} yaad nahi")

@app.get("/memory/people")
async def list_people():
    people = await people_memory.list_all()
    return JSONResponse({"people": people, "count": len(people)})

@app.post("/memory/photo")
async def analyze_photo(
    file: UploadFile = File(...),
    label: str = ""
):
    image_bytes = await file.read()
    if label:
        path, analysis = await photo_memory.save_photo_with_label(image_bytes, label, file.filename)
        if label:
            await people_memory.add_photo_to_person(label, path)
        return JSONResponse({"analysis": analysis, "saved_as": label, "path": path})
    else:
        analysis = await photo_memory.analyze_photo(image_bytes)
        return JSONResponse({"analysis": analysis})

@app.post("/search")
async def live_search(req: SearchRequest):
    result = await search_manager.search(req.query)
    return JSONResponse({"result": result})

@app.get("/memory/search")
async def search_memory(q: str):
    results = await conversation_memory.search_memory(q)
    return JSONResponse({"results": results, "count": len(results)})
