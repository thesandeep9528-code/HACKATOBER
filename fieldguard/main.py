from __future__ import annotations

import io
import ipaddress
import os
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response
from PIL import Image, UnidentifiedImageError

from fieldguard.schemas import AdvisoryResponse, Esp32CaptureRequest, PredictionResponse, SensorContext
from fieldguard.services.advisory import irrigation_advice, precautions_for, sustainability_score
from fieldguard.services.image_quality import analyze_image_quality
from model.legacy_reference import convert as convert_legacy_reference
from model.predict import ArtifactPredictor, ModelNotConfiguredError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
# Artifact predictor configured with fine-tuned in-field weights
app = FastAPI(title="AgriSmart AI — FieldGuard", version="0.1.0")
predictor = ArtifactPredictor(
    weights_path=os.getenv("AGRISMART_WEIGHTS", "artifacts/current/best_model.pt"),
    class_names_path=os.getenv("AGRISMART_CLASS_NAMES", "artifacts/current/class_names.json"),
)
public_baseline_predictor = ArtifactPredictor(
    "artifacts/public_plantvillage_baseline/best_model.pt",
    "artifacts/public_plantvillage_baseline/class_names.json",
)
_legacy_predictor: ArtifactPredictor | None = None


def active_predictor() -> tuple[ArtifactPredictor, str, str]:
    global _legacy_predictor
    if predictor.is_configured:
        return predictor, "official_artifact", "Official-label artifact configured locally. Report only measured evaluation results."
    if public_baseline_predictor.is_configured:
        return public_baseline_predictor, "public_plantvillage_baseline", "Public PlantVillage baseline: lab-condition validation only; it is not an organizer-held-out field score."
    reference_h5 = "./.references/Predictive-Plant-Care-System/ai_models/plant_disease_detection.h5"
    reference_labels = "./.references/Predictive-Plant-Care-System/ai_models/categories.json"
    if os.path.isfile(reference_h5) and os.path.isfile(reference_labels):
        if _legacy_predictor is None:
            weights, labels = convert_legacy_reference(reference_h5, reference_labels, "artifacts/legacy_reference")
            _legacy_predictor = ArtifactPredictor(weights, labels, architecture="mobilenet_v2")
        return _legacy_predictor, "legacy_reference_demo", "Demo only: inherited 38-class PlantVillage reference artifact, not the official SIH label set or field-tested model."
    raise ModelNotConfiguredError("No trained artifact is available. Add official weights and class_names.json, or clone the documented reference repositories for demo mode.")


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True, "model_configured": predictor.is_configured, "public_baseline_available": public_baseline_predictor.is_configured, "legacy_demo_available": os.path.isfile("./.references/Predictive-Plant-Care-System/ai_models/plant_disease_detection.h5")}


@app.get("/favicon.ico", include_in_schema=False, status_code=204)
def favicon() -> Response:
    return Response(status_code=204)


@app.post("/api/advisory", response_model=AdvisoryResponse)
def advisory(context: SensorContext) -> AdvisoryResponse:
    action, reason, trace = irrigation_advice(context)
    return AdvisoryResponse(
        irrigation_action=action,
        reason=reason,
        sustainability_score=sustainability_score(context, action),
        trace=trace + ["Disease classification is intentionally independent of farm context."],
    )


@app.post("/api/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)) -> PredictionResponse:
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    return prediction_response(payload)


def prediction_response(payload: bytes) -> PredictionResponse:
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 8 MB limit.")
    try:
        image = Image.open(io.BytesIO(payload))
        image.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=422, detail="Upload a valid image file.") from None
    try:
        selected_predictor, model_mode, model_notice = active_predictor()
        result = selected_predictor.predict_bytes(payload)
    except ModelNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    is_valid_plant, warnings = analyze_image_quality(image, result.confidence, result.alternatives)
    if not is_valid_plant:
        return PredictionResponse(
            label="Non-Plant / Unrecognized Image",
            confidence=0.0,
            model_mode=model_mode,
            model_notice=model_notice,
            precautions=[
                "Upload a close-up photo of a plant leaf or crop foliage.",
                "Ensure the leaf fills at least 50% of the frame in natural lighting.",
            ],
            quality_warnings=warnings,
            alternatives=[],
        )

    return PredictionResponse(
        label=result.label,
        confidence=result.confidence,
        model_mode=model_mode,
        model_notice=model_notice,
        precautions=precautions_for(result.label),
        quality_warnings=warnings,
        alternatives=result.alternatives,
    )


@app.post("/api/esp32/capture", response_model=PredictionResponse)
def esp32_capture(device: Esp32CaptureRequest) -> PredictionResponse:
    """Capture one JPEG from a private-network ESP32-CAM and classify it.

    Restricting the host to private/loopback addresses prevents this demo endpoint
    from being used to fetch arbitrary internet URLs.
    """
    try:
        address = ipaddress.ip_address(device.host)
    except ValueError:
        raise HTTPException(status_code=422, detail="Enter only an ESP32 private IP address, without http:// or a port.") from None
    if not (address.is_private or address.is_loopback):
        raise HTTPException(status_code=422, detail="ESP32-CAM must use a private-network IP address.")
    try:
        with urlopen(f"http://{address.compressed}/capture", timeout=5) as response:
            payload = response.read(MAX_UPLOAD_BYTES + 1)
    except (URLError, OSError, TimeoutError):
        raise HTTPException(status_code=502, detail="Could not capture an image from the ESP32-CAM. Check Wi-Fi and its /capture endpoint.") from None
    return prediction_response(payload)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html><html><head><title>AgriSmart AI</title><style>body{font:16px system-ui;max-width:820px;margin:40px auto;padding:0 18px;color:#173b2d;background:#fbfdfb}h1{margin-bottom:0}section{background:white;border:1px solid #dce8df;border-radius:10px;padding:18px;margin:18px 0}button{background:#237a57;color:white;border:0;padding:10px 16px;border-radius:6px;font-weight:600;cursor:pointer}.tab{background:#e7f1ea;color:#173b2d;margin-right:6px}.tab.active{background:#237a57;color:white}input{margin:6px;padding:6px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.notice{background:#fff2cc;padding:10px;border-radius:6px}pre{white-space:pre-wrap;background:#f0f6f2;padding:14px;border-radius:6px;min-height:28px}video,canvas{display:block;max-width:100%;width:420px;border-radius:8px;margin:10px 0}.hidden{display:none}@media(max-width:600px){.grid{grid-template-columns:1fr}}</style></head><body><h1>AgriSmart AI · FieldGuard</h1><p>Detect a leaf condition, then turn farm context into a transparent irrigation decision.</p><p class=notice id=n>Checking local model…</p><section><h2>1. Scan leaf</h2><button class="tab active" data-panel=upload>Upload</button><button class=tab data-panel=camera>Camera</button><button class=tab data-panel=esp32>ESP32-CAM</button><div id=upload><form id=scan><input id=image type=file accept=image/* required><button>Analyze leaf</button></form></div><div id=camera class=hidden><video id=video autoplay playsinline></video><canvas id=canvas class=hidden></canvas><button id=startCamera>Start camera</button><button id=takePhoto>Take photo & analyze</button><button id=stopCamera>Stop camera</button></div><div id=esp32 class=hidden><form id=device><label>ESP32 private IP <input name=host placeholder="192.168.1.50" required></label><button>Capture & analyze</button></form><small>Your ESP32-CAM firmware must expose a JPEG at <code>/capture</code>.</small></div><pre id=scanOutput>Choose an upload, camera, or ESP32-CAM capture.</pre></section><section><h2>2. Farm context</h2><form id=farm><div class=grid><label>Crop <input name=crop value=Tomato required></label><label>Growth stage <input name=stage value=growing required></label><label>Soil moisture % <input name=soil_moisture_pct type=number min=0 max=100 value=31 required></label><label>Temperature °C <input name=temperature_c type=number value=30 required></label><label>Humidity % <input name=humidity_pct type=number min=0 max=100 value=72 required></label><label>Rain probability % <input name=rain_probability_pct type=number min=0 max=100 value=70 required></label><label>Forecast rain mm <input name=forecast_rain_mm type=number min=0 value=5 required></label></div><button>Get irrigation advice</button></form><pre id=farmOutput>Context is optional and cannot change the disease prediction.</pre></section><script>const $=x=>document.getElementById(x),pretty=x=>JSON.stringify(x,null,2);let stream;async function showResult(r){scanOutput.textContent=pretty(await r.json())}fetch('/api/health').then(r=>r.json()).then(x=>n.textContent=x.model_configured?'Official model artifact ready.':x.public_baseline_available?'Public PlantVillage baseline ready — lab validation only, not official SIH scoring.':x.legacy_demo_available?'Legacy demo model ready — not valid for official SIH scoring.':'Model training is required.');document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));b.classList.add('active');['upload','camera','esp32'].forEach(x=>$(x).classList.toggle('hidden',x!==b.dataset.panel))});scan.onsubmit=async e=>{e.preventDefault();scanOutput.textContent='Analyzing…';let d=new FormData();d.append('file',image.files[0]);showResult(await fetch('/api/predict',{method:'POST',body:d}))};startCamera.onclick=async()=>{try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}});video.srcObject=stream}catch(e){scanOutput.textContent='Camera unavailable: '+e.message}};stopCamera.onclick=()=>{stream?.getTracks().forEach(t=>t.stop());video.srcObject=null};takePhoto.onclick=async()=>{if(!stream)return scanOutput.textContent='Start the camera first.';canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);canvas.classList.remove('hidden');scanOutput.textContent='Analyzing…';canvas.toBlob(async blob=>{let d=new FormData();d.append('file',blob,'camera-leaf.jpg');showResult(await fetch('/api/predict',{method:'POST',body:d}))},'image/jpeg',.9)};device.onsubmit=async e=>{e.preventDefault();scanOutput.textContent='Capturing from ESP32-CAM…';let host=new FormData(device).get('host');showResult(await fetch('/api/esp32/capture',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({host})}))};farm.onsubmit=async e=>{e.preventDefault();farmOutput.textContent='Reasoning…';let d=Object.fromEntries(new FormData(farm));for(let k of ['soil_moisture_pct','temperature_c','humidity_pct','rain_probability_pct','forecast_rain_mm'])d[k]=Number(d[k]);let r=await fetch('/api/advisory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});farmOutput.textContent=pretty(await r.json())};</script></body></html>"""
