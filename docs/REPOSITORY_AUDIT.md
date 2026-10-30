# AgriSmart AI — Repository Audit and Gap Analysis

## Audit basis

This analysis was completed before implementation. The uploaded **SIH-2026 Internal Hackathon — Problem Statement 1: AGRISMART AI** PDF (`oxpusiikphgm6s6uv2xs_260910_114128.pdf`) is authoritative. The following repositories were shallow-cloned and audited as reference material only; no code, weights, or UI is copied into this system.

- [GrowSense-AI](https://github.com/shivam-shukla11/GrowSense-AI)
- [Predictive-Plant-Care-System](https://github.com/shivam-shukla11/Predictive-Plant-Care-System), audited at `f893dc3`

The architectural decision is non-negotiable: **the image classifier is the source of truth. Farm context can enrich a recommendation, but never overwrite a disease label.**

## Official requirements internalized

| Area | Requirement from the official PDF | AgriSmart response |
|---|---|---|
| Core task | Predict an organizer-provided disease class or healthy class from a new leaf/crop image. | One flat, exact-label classifier with a stable Python and CLI contract. |
| Evaluation | Held-out macro-F1 is the primary metric; report a confusion matrix and per-class precision/recall. | Reproducible evaluator emits each required artifact; no result is fabricated before organizer evaluation. |
| Data integrity | PlantVillage-style data is train/validation; PlantDoc-style field data is held out and must never be trained on. | Explicit manifest roles, train-time held-out-data rejection, split/duplicate checks, and separately invoked evaluation. |
| Domain shift | Lab-to-field generalisation is the central challenge. | Transfer learning, realistic field-shift augmentation, calibration, input-quality checks, and a clearly labelled synthetic robustness proxy. |
| Interface | Provide `predict(image_path) → class_label` or a single-image CLI that loads weights. | Provide both through `model/predict.py`. |
| Farmer guidance | Show result, confidence, and basic actionable precautions. | Calibrated result, top alternatives, quality warnings, and conservative versioned guidance. |
| Reproducibility | README, source, model code, report, dependencies, and clear runnable instructions. | Python-first FastAPI app, artifact contract, data instructions, tests, model-report template, and optional Dockerfile. |
| Optional bonuses | Crop, irrigation, weather, sustainability, assistant, IoT, and agentic features are optional. | One cohesive context bundle: simulated sensors, weather-aware irrigation, transparent sustainability score, grounded explanations, and a traceable decision loop. |

## Reference repository findings

### GrowSense-AI

GrowSense includes a polished Vite/React/TypeScript dashboard with camera upload, ESP32-CAM capture, React Query, charts, typed API calls, and a farmer-facing multi-language design. Its documentation proposes a useful sensor message shape and good product concepts: plant context, trends, hydration, weather, alerts, and notifications.

Its `plant-backend` is an unresolved gitlink with no `.gitmodules` entry or tracked contents. Consequently, the claimed FastAPI, Keras model, MongoDB code, requirements, tests, and model artifacts cannot be reproduced or audited. The surviving frontend is wider than the hackathon needs, has legacy/fallback endpoint paths, retains Supabase/auth drift, and sends a client-controlled `user_id` pattern that is unsafe if trusted by a server. Its disease feature is dashboard plumbing rather than a testable ML product.

### Predictive-Plant-Care-System

Predictive Plant Care contains a small FastAPI prototype, MongoDB dependency, rule-based care modules, and a TensorFlow H5 classifier. The classifier lazily loads behind a lock, accepts a 224 px image, and returns an argmax/max-softmax value over a fixed 38-class PlantVillage map. The FastAPI/Pydantic boundary, lazy-load pattern, and transparent-rule idea are worth retaining as concepts.

It cannot serve as the AgriSmart core. It has no training provenance, dataset manifest, exact final class registry, macro-F1, confusion matrix, per-class metrics, calibration, confidence policy, or lab-to-field strategy. MongoDB is mandatory even for image inference. The upload endpoint trusts MIME type, writes a user-controlled filename to disk, and lacks image magic/size guards. Sensor access is globally scoped, weather paths are inconsistent, requirements omit imported modules, and a Python installer is committed to source control.

## Required gap analysis

| Requirement | GrowSense | Predictive Plant Care | Needed for AgriSmart | Action |
|---|---|---|---|---|
| Organizer-exact disease labels | No verifiable model or label registry. | Fixed 38 PlantVillage labels, not necessarily the final shared set. | Artifact-backed exact class registry read from organizer data. | ADD / REWRITE |
| Honest training and validation | No backend or training code available. | No training script, split, or data provenance. | Stratified manifests, duplicate audit, seed/config capture. | ADD |
| Held-out test governance | No protocol. | No protocol. | Test data never enters train/tune paths; evaluation is invoked separately. | ADD |
| Lab-to-field robustness | No ML pipeline. | Resize + `/255`, no shift strategy. | Transfer learning, realistic augmentation, calibration, robustness proxy. | ADD |
| Macro-F1/confusion/per-class report | Dashboard stats only. | No required metrics. | Metrics JSON, CSV, raw/normalised matrices, calibration report. | ADD |
| Reproducible prediction | UI calls unavailable backend. | Basic endpoint, but depends on MongoDB and opaque H5 provenance. | Standalone `predict(image_path)` plus CLI and exported metadata. | REWRITE |
| Safe image upload | Good capture UX idea; server unavailable. | MIME-only check and shared filename write. | In-memory image verification, size limits, response schema, quality flags. | KEEP idea / REWRITE implementation |
| Precaution guidance | UI expects treatments but source unavailable. | Disease/confidence only. | Versioned disease guidance and safe generic fallback. | ADD |
| Farmer UI | Strong but dependency-heavy dashboard. | No frontend. | Lightweight Python-served scan → result → action UI. | MODIFY |
| Sensor ingestion | Useful documented ESP32/worker message idea. | Pydantic sensor payload and Mongo concept. | Validated farm/plot/device-aware simulated or real feed with freshness. | KEEP concept / REWRITE |
| Irrigation/environment | Claimed but unavailable. | Transparent rules but generic thresholds and incorrect time-window use. | Crop-stage/weather-aware policy with an auditable trace. | MODIFY / REWRITE |
| Weather intelligence | UI expects weather/AQI. | Inconsistent weather API; current rain amount treated as probability. | Coherent provider plus offline/manual fixture. | REWRITE |
| Trends and alerts | Helpful visual/notification ideas. | Basic global-data rules. | Deterministic, deduplicated alert trace for demo. | MODIFY |
| Sustainability | Implied water-saving UI but no formula. | Not implemented. | Exact reproducible formula and scenario-only water estimate. | ADD |
| Assistant and language | English/Gujarati UI scaffolding. | Not implemented. | Grounded template explanations, optionally English/Gujarati/Hindi. | MODIFY / ADD |
| IoT / agentic flow | ESP32/Cloudflare ideas, server unverified. | Conceptual pipeline only. | Simulator → validation → policy → trace loop. | ADD |
| Authentication/tenancy | Unverified backend; client-controlled identity pattern. | Partial JWT, global sensor data, unauthenticated routes. | Keep an extensible ownership boundary; do not dilute the core MVP. | REMOVE from MVP / ADD later |
| Deployment/reproducibility | Missing backend and separate Node app block quick judge run. | MongoDB blocks standalone core. | Python-only local core with optional Docker, no external service required. | REWRITE |

## Component classification

| Reference component | Classification | AgriSmart decision |
|---|---|---|
| GrowSense upload/webcam/ESP32 capture flow | KEEP | Retain the farmer-first capture idea in a smaller, secure UI. |
| GrowSense typed client and dashboard patterns | MODIFY | Preserve clear contracts and scan UX, not the React/Supabase implementation. |
| GrowSense sensor schema, trends, notifications | MODIFY | Keep concepts; introduce one canonical schema, validation, freshness, and traceability. |
| GrowSense unresolved backend gitlink and legacy auth/fallbacks | REMOVE | It is unreproducible and conflicts with a clean trusted service boundary. |
| Predictive Plant Care FastAPI/Pydantic and lazy load lock | KEEP | Reimplement cleanly around a versioned PyTorch artifact. |
| Predictive Plant Care MobileNet H5 weights/categories | REMOVE | Insufficient provenance, final-label alignment, calibration, and evaluation. |
| Predictive Plant Care upload endpoint | REWRITE | Replace shared disk and user filename handling with safe validated inference. |
| Predictive Plant Care sensor/trend/irrigation rules | MODIFY | Preserve transparent rules but correct time, crop context, stale-data, and validation weaknesses. |
| Predictive Plant Care weather/client integration | REWRITE | Use a coherent provider and distinguish probability from precipitation volume. |
| Predictive Plant Care Mongo-required startup and partial auth | REMOVE | Core disease inference must start without a database or network. |
| Both repositories' missing ML reporting and field protocol | ADD | First-class training/evaluation/calibration/robustness stack with clear data governance. |

## Unified architecture decision

AgriSmart AI is an original **FieldGuard** system: a calibrated, transfer-learning disease classifier built for lab-to-field robustness, surrounded by a focused and auditable advisory layer. The optional context modules are intentionally coupled through one decision contract, so the demo shows depth without allowing dashboard features to dilute the core model.

## Audit-informed implementation order

1. Data contract, exact labels, leakage checks, baseline training, and prediction interface.
2. Evaluation artifacts, calibration, and field-shift robustness proxy.
3. Safe prediction API and focused farmer UI with precautions.
4. Simulated sensor → weather → irrigation → sustainability decision loop.
5. Documentation, model report, scenario tests, and demo rehearsal materials.
