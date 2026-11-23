import io
import os
import time
import base64
import threading
from collections import defaultdict, deque
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from openai import AsyncOpenAI

ORIGIN = "https://dragasakisn-beep.github.io"
MAX_UPLOAD = 8 * 1024 * 1024
WINDOW = 3600
MAX_PER_IP = int(os.getenv("MAX_GENERATIONS_PER_IP_HOUR", "3"))
MAX_GLOBAL = int(os.getenv("MAX_GENERATIONS_PER_INSTANCE", "30"))
PROMPTS = {
 "Billionaire": "A cinematic editorial photograph of this same person as an ultra-wealthy entrepreneur in an elegant penthouse, bespoke tailoring, warm natural lighting, realistic face.",
 "Villain Arc": "A dramatic cinematic portrait of this same person as a fictional sophisticated movie antagonist, dark tailored outfit, atmospheric architectural setting, realistic face, no violence.",
 "Cyberpunk": "A photorealistic futuristic cyberpunk portrait of this same person, neon-lit city at night, high-tech fashion, cinematic reflections, realistic face.",
 "Age 70": "A photorealistic age-progression portrait depicting this same adult person at approximately 70 years old, plausible natural aging, same facial structure, natural daylight.",
 "Superhero": "A cinematic portrait of this same person as an original fictional superhero, distinctive non-branded suit, heroic skyline, photorealistic face.",
 "Astronaut": "A photorealistic portrait of this same person as an astronaut in an original modern spacesuit, spacecraft observation deck, Earth visible through window."
}
app = FastAPI(title="FutureFace AI API")
app.add_middleware(CORSMiddleware, allow_origins=[ORIGIN], allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["Content-Type"])
lock = threading.Lock()
requests_by_ip = defaultdict(deque)
total = 0

@app.get("/health")
async def health():
    return {"status": "ok", "configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/api/transform")
async def transform(request: Request, photo: UploadFile = File(...), timeline: str = Form(...)):
    global total
    if timeline not in PROMPTS:
        raise HTTPException(400, "Unknown timeline")
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(503, "AI service is not configured")
    # Render is the trusted proxy; do not accept arbitrary client-supplied forwarded IPs.
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with lock:
        q = requests_by_ip[ip]
        while q and now-q[0] > WINDOW:
            q.popleft()
        if len(q) >= MAX_PER_IP or total >= MAX_GLOBAL:
            raise HTTPException(429, "Generation limit reached. Please try again later.")
        q.append(now)
        total += 1
    raw = await photo.read(MAX_UPLOAD+1)
    if len(raw)>MAX_UPLOAD:
        raise HTTPException(413, "Image exceeds 8 MB")
    try:
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image)
        image.verify() if False else None
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1024,1024))
        buf = io.BytesIO()
        image.save(buf,format="PNG")
        buf.seek(0)
        buf.name = "portrait.png"
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(415, "Please upload a valid JPEG or PNG photo")
    prompt = ("Edit the supplied portrait to depict the SAME PERSON. Preserve recognizable facial identity, "
              "ethnicity, facial proportions and expression where practical. Make a genuinely new photorealistic "
              "image rather than a color filter. No text, logos or watermark. " + PROMPTS[timeline])
    try:
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=90.0, max_retries=1)
        result = await client.images.edit(model=os.getenv("OPENAI_IMAGE_MODEL","gpt-image-1"),image=buf,prompt=prompt,size="1024x1024",quality="medium")
        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("No image returned")
        return JSONResponse({"image": "data:image/png;base64,"+result.data[0].b64_json,"timeline":timeline})
    except Exception:
        raise HTTPException(502, "Image generation failed. Check model access, billing and service logs.")
