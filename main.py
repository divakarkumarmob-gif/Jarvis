"""
KIRA — Main Entry Point
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Kira AI", version="1.0.0")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Kira is live!"}


@app.get("/health")
async def health():
    return JSONResponse({"status": "healthy", "kira": "online"})
