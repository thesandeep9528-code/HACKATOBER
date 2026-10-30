from __future__ import annotations

import io
import base64
from typing import Any
import numpy as np
import torch
from PIL import Image
import matplotlib.cm as cm

def generate_gradcam_overlay(
    model: torch.nn.Module,
    input_tensor: torch.Tensor,
    original_image: Image.Image,
    target_class_idx: int,
    target_layer: torch.nn.Module | None = None
) -> str | None:
    """Compute Grad-CAM for target class and return base64 encoded JPEG overlay."""
    try:
        if target_layer is None:
            # For torchvision EfficientNet-B0: features[8] is the last conv block
            if hasattr(model, "features") and len(model.features) >= 9:
                target_layer = model.features[8]
            elif hasattr(model, "features"):
                target_layer = model.features[-1]
            else:
                return None

        activations = []
        gradients = []

        def forward_hook(module, inp, out):
            activations.append(out)

        def backward_hook(module, grad_in, grad_out):
            gradients.append(grad_out[0])

        h_forward = target_layer.register_forward_hook(forward_hook)
        h_backward = target_layer.register_full_backward_hook(backward_hook)

        try:
            # Ensure input requires grad
            tensor_clone = input_tensor.clone().detach()
            tensor_clone.requires_grad_(True)

            model.eval()
            model.zero_grad()

            output = model(tensor_clone)
            if output.ndim == 2:
                score = output[0, target_class_idx]
            else:
                score = output[target_class_idx]

            score.backward()

            if not activations or not gradients:
                return None

            act = activations[0].detach()
            grad = gradients[0].detach()

            # Global average pooling over spatial dimensions
            weights = grad.mean(dim=(2, 3), keepdim=True)
            cam = (weights * act).sum(dim=1, keepdim=True)
            cam = torch.relu(cam).squeeze().cpu().numpy()

            # Normalize to 0..1
            cam_min, cam_max = cam.min(), cam.max()
            if cam_max - cam_min > 1e-8:
                cam = (cam - cam_min) / (cam_max - cam_min)
            else:
                cam = np.zeros_like(cam)

            # Resize heatmap to match original image dimensions
            orig_rgb = original_image.convert("RGB")
            cam_img = Image.fromarray((cam * 255).astype(np.uint8)).resize(orig_rgb.size, Image.BILINEAR)
            cam_arr = np.array(cam_img) / 255.0

            # Apply jet colormap
            try:
                import matplotlib
                colormap = matplotlib.colormaps["jet"]
            except Exception:
                try:
                    colormap = cm.get_cmap("jet")
                except Exception:
                    colormap = cm.jet

            heatmap = colormap(cam_arr)[:, :, :3]
            heatmap = (heatmap * 255).astype(np.uint8)

            # Blend with original leaf: 55% original + 45% heatmap
            orig_arr = np.array(orig_rgb)
            overlay = (0.55 * orig_arr + 0.45 * heatmap).astype(np.uint8)
            blended_img = Image.fromarray(overlay)

            # Encode as base64 JPEG
            buf = io.BytesIO()
            blended_img.save(buf, format="JPEG", quality=85)
            return base64.b64encode(buf.getvalue()).decode("utf-8")

        finally:
            h_forward.remove()
            h_backward.remove()

    except Exception as exc:
        print(f"[Grad-CAM Warning] Heatmap generation bypassed: {exc}")
        return None
