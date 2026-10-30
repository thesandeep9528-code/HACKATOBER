from __future__ import annotations

import argparse
import io
import json
import threading
from dataclasses import dataclass
from pathlib import Path


class ModelNotConfiguredError(RuntimeError):
    pass


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float
    alternatives: list[dict[str, float | str]]
    gradcam_b64: str | None = None
    is_tta: bool = True
    crop_filter_applied: str | None = None
    crop_refinements: list[dict] | None = None


CROP_KEY_MAP = {
    "apple": "Apple",
    "blueberry": "Blueberry",
    "cherry": "Cherry_(including_sour)",
    "corn": "Corn_(maize)",
    "maize": "Corn_(maize)",
    "grape": "Grape",
    "orange": "Orange",
    "citrus": "Orange",
    "peach": "Peach",
    "pepper": "Pepper,_bell",
    "bell pepper": "Pepper,_bell",
    "potato": "Potato",
    "raspberry": "Raspberry",
    "soybean": "Soybean",
    "squash": "Squash",
    "strawberry": "Strawberry",
    "tomato": "Tomato",
}

CROP_DISPLAY_NAMES = {
    "Apple": "Apple",
    "Blueberry": "Blueberry",
    "Cherry_(including_sour)": "Cherry",
    "Corn_(maize)": "Corn (Maize)",
    "Grape": "Grape",
    "Orange": "Citrus / Orange",
    "Peach": "Peach",
    "Pepper,_bell": "Bell Pepper",
    "Potato": "Potato",
    "Raspberry": "Raspberry",
    "Soybean": "Soybean",
    "Squash": "Squash",
    "Strawberry": "Strawberry",
    "Tomato": "Tomato",
}


class ArtifactPredictor:
    """Thread-safe, lazy loader for an explicitly versioned PyTorch artifact with TTA and Grad-CAM."""

    def __init__(self, weights_path: str | Path, class_names_path: str | Path, architecture: str = "efficientnet_b0") -> None:
        self.weights_path, self.class_names_path = Path(weights_path), Path(class_names_path)
        self.architecture = architecture
        self._model = self._classes = self._transform = self._tta_transforms = None
        self._lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        return self.weights_path.is_file() and self.class_names_path.is_file()

    def _load(self) -> None:
        if self._model is not None:
            return
        if not self.is_configured:
            raise ModelNotConfiguredError("No trained AgriSmart artifact is configured. Train the official-label model first.")
        import torch
        from torchvision.models import efficientnet_b0, mobilenet_v2
        from torchvision.transforms import v2

        with self._lock:
            if self._model is None:
                self._classes = json.loads(self.class_names_path.read_text(encoding="utf-8"))
                if self.architecture == "efficientnet_b0":
                    model = efficientnet_b0(weights=None)
                elif self.architecture == "mobilenet_v2":
                    model = mobilenet_v2(weights=None)
                else:
                    raise ModelNotConfiguredError(f"Unsupported artifact architecture: {self.architecture}")
                model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(self._classes))
                model.load_state_dict(torch.load(self.weights_path, map_location="cpu", weights_only=True))
                model.eval()
                self._model = model
                normalise = v2.Normalize([0.0, 0.0, 0.0], [1.0, 1.0, 1.0]) if self.architecture == "mobilenet_v2" else v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                self._transform = v2.Compose([v2.Resize((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise])

                # Test-Time Augmentation (TTA) multi-view pipeline
                self._tta_transforms = [
                    v2.Compose([v2.Resize((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise]),
                    v2.Compose([v2.Resize((224, 224)), v2.RandomHorizontalFlip(p=1.0), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise]),
                    v2.Compose([v2.Resize((256, 256)), v2.CenterCrop((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise]),
                    v2.Compose([v2.Resize((256, 256)), v2.CenterCrop((224, 224)), v2.RandomHorizontalFlip(p=1.0), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise]),
                    v2.Compose([v2.Resize((240, 240)), v2.CenterCrop((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), normalise]),
                ]

    def predict_bytes(
        self,
        payload: bytes,
        use_tta: bool = True,
        generate_cam: bool = True,
        crop_filter: str | None = None
    ) -> Prediction:
        self._load()
        import torch
        from PIL import Image

        image = Image.open(io.BytesIO(payload)).convert("RGB")

        if use_tta and self._tta_transforms:
            batch_tensors = [t(image) for t in self._tta_transforms]
            batch = torch.stack(batch_tensors)
            with torch.inference_mode():
                probs_batch = torch.softmax(self._model(batch), dim=1)
                probabilities = probs_batch.mean(dim=0)
        else:
            tensor = self._transform(image).unsqueeze(0)
            with torch.inference_mode():
                probabilities = torch.softmax(self._model(tensor)[0], dim=0)

        # Normalize crop_filter if requested
        canonical_crop = None
        filtered_indices = None
        if crop_filter:
            norm_cf = crop_filter.strip().lower()
            if norm_cf not in ("all", "auto", "auto-detect", "none", ""):
                canonical_crop = CROP_KEY_MAP.get(norm_cf)
                if not canonical_crop:
                    for k, v in CROP_KEY_MAP.items():
                        if k in norm_cf or norm_cf in k:
                            canonical_crop = v
                            break
                if canonical_crop:
                    filtered_indices = [
                        i for i, c in enumerate(self._classes)
                        if c.split("___")[0] == canonical_crop
                    ]

        crop_refinements = None
        applied_filter_name = None

        if filtered_indices:
            applied_filter_name = CROP_DISPLAY_NAMES.get(canonical_crop, canonical_crop)
            sub_probs = probabilities[filtered_indices]
            sub_sum = sub_probs.sum().item()
            if sub_sum > 0:
                cond_probs = sub_probs / sub_sum
            else:
                cond_probs = sub_probs

            sorted_cond_idx = torch.argsort(cond_probs, descending=True)
            alternatives = []
            for rank_idx in sorted_cond_idx[:min(3, len(filtered_indices))]:
                orig_idx = filtered_indices[rank_idx]
                alternatives.append({
                    "label": self._classes[orig_idx],
                    "confidence": round(float(cond_probs[rank_idx]), 4)
                })

            top_idx = filtered_indices[sorted_cond_idx[0]]
            primary_label = alternatives[0]["label"]
            primary_conf = alternatives[0]["confidence"]
        else:
            top = torch.topk(probabilities, k=min(3, len(self._classes)))
            alternatives = [{"label": self._classes[index], "confidence": round(float(score), 4)} for score, index in zip(top.values, top.indices)]
            top_idx = int(top.indices[0])
            primary_label = alternatives[0]["label"]
            primary_conf = alternatives[0]["confidence"]

            # Compute cross-crop disambiguation / smart refinement suggestions
            crop_prob_sums: dict[str, float] = {}
            crop_best_classes: dict[str, tuple[int, float]] = {}
            for idx, (p_val, cls_name) in enumerate(zip(probabilities, self._classes)):
                p = float(p_val)
                raw_c = cls_name.split("___")[0]
                crop_prob_sums[raw_c] = crop_prob_sums.get(raw_c, 0.0) + p
                if raw_c not in crop_best_classes or p > crop_best_classes[raw_c][1]:
                    crop_best_classes[raw_c] = (idx, p)

            primary_raw_crop = primary_label.split("___")[0]
            refinements = []
            for raw_c, c_sum in sorted(crop_prob_sums.items(), key=lambda x: -x[1]):
                if raw_c == primary_raw_crop:
                    continue
                # Suggest refinement if secondary crop has >= 5% probability mass
                if c_sum >= 0.05:
                    best_idx, best_p = crop_best_classes[raw_c]
                    cond_conf = (best_p / c_sum) if c_sum > 0 else best_p
                    if cond_conf >= 0.40:
                        disp_name = CROP_DISPLAY_NAMES.get(raw_c, raw_c)
                        clean_disease = self._classes[best_idx].split("___")[-1].replace("_", " ")
                        crop_key = norm_cf_key = raw_c.lower().split("_")[0]
                        refinements.append({
                            "crop": disp_name,
                            "crop_key": crop_key,
                            "top_label": self._classes[best_idx],
                            "display_name": disp_name,
                            "disease_name": clean_disease,
                            "raw_confidence": round(best_p, 4),
                            "conditioned_confidence": round(cond_conf, 4),
                            "crop_prob_sum": round(c_sum, 4)
                        })
            if refinements:
                crop_refinements = refinements[:2]

        gradcam_b64 = None
        if generate_cam:
            try:
                from model.gradcam import generate_gradcam_overlay
                base_tensor = self._transform(image).unsqueeze(0)
                gradcam_b64 = generate_gradcam_overlay(self._model, base_tensor, image, top_idx)
            except Exception as e:
                print(f"[Grad-CAM Notice] Bypassed heatmap: {e}")

        return Prediction(
            label=primary_label,
            confidence=primary_conf,
            alternatives=alternatives,
            gradcam_b64=gradcam_b64,
            is_tta=use_tta,
            crop_filter_applied=applied_filter_name,
            crop_refinements=crop_refinements
        )


_default_predictor = ArtifactPredictor("artifacts/current/best_model.pt", "artifacts/current/class_names.json")


def predict(image_path: str) -> str:
    """Required single-image contract: returns the exact trained label string."""
    return _default_predictor.predict_bytes(Path(image_path).read_bytes()).label


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--weights", default="artifacts/current/best_model.pt")
    parser.add_argument("--class-names", default="artifacts/current/class_names.json")
    args = parser.parse_args()
    result = ArtifactPredictor(args.weights, args.class_names).predict_bytes(Path(args.image).read_bytes())
    print(json.dumps({"label": result.label, "confidence": result.confidence, "alternatives": result.alternatives}))
