# Reference integration decisions

| Reference insight | AgriSmart implementation | Reason |
|---|---|---|
| Predictive Plant Care lazy-load lock | `ArtifactPredictor` loads a PyTorch artifact once under a lock. | Efficient, testable inference without importing an opaque H5 model. |
| Predictive Plant Care FastAPI/Pydantic boundary | FastAPI endpoint plus strict response models. | Clear integration contract. |
| Predictive Plant Care upload flow | In-memory, size-capped Pillow verification; no client filename is written. | Avoids MIME-only validation and shared upload files. |
| GrowSense scan/upload UX | A compact same-origin farmer scan UI. | Keeps the farmer-first flow without a separate React/Supabase stack. |
| GrowSense camera and ESP32-CAM flow | Native browser camera capture plus a validated private-IP ESP32 `/capture` endpoint. | Preserves the demo value while avoiding client-controlled identity and unrestricted server-side fetches. |
| GrowSense sensor/dashboard concepts | `/api/advisory` accepts an explicit context and returns a deterministic trace. | No client-controlled identity or global sensor state. |
| Both repositories' disease models | Not reused. | Neither demonstrates official labels, split provenance, field-test macro-F1, calibration, or compliant evaluation. |

The classifier label is immutable within the advisory flow. Optional weather/sensor context may change irrigation advice only.

The GrowSense implementation guide claims backend files, MongoDB records, Twilio alerts, and ESP32 firmware that are absent from its published checkout: `plant-backend` is an unmapped gitlink. These claims were not copied or treated as verified. AgriSmart independently implements the observable farmer scan interactions above.
