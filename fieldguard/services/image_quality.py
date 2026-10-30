from __future__ import annotations

import numpy as np
from PIL import Image, ImageStat


def analyze_image_quality(
    image: Image.Image,
    confidence: float,
    alternatives: list[dict[str, float | str]] | None = None,
) -> tuple[bool, list[str]]:
    """Determine whether an image has plant/leaf characteristics or is out-of-distribution.

    Returns (is_valid_plant, warnings_list).
    """
    warnings: list[str] = []

    # 1. Blank, uniform, or solid-color image check
    rgb_image = image.convert("RGB")
    stat = ImageStat.Stat(rgb_image)
    if all(v < 12.0 for v in stat.var):
        return False, ["Blank or solid-color image detected. Please upload a clear photo of a crop leaf."]

    # 2. Plant foliage & chlorophyll color spectrum in HSV space
    hsv = rgb_image.convert("HSV")
    h, s, v = np.array(hsv).transpose(2, 0, 1)

    # Foliage green, yellow, brown/leaf necrosis
    # Hue: 18..115 (scale 0..255), Saturation >= 20, Value >= 20
    foliage_mask = (h >= 18) & (h <= 115) & (s >= 20) & (v >= 20)
    foliage_ratio = float(np.mean(foliage_mask))

    # Reject non-plant scenes with negligible foliage (< 6%)
    # This filters out people, cars, rooms, furniture, clothing, screens, etc.
    if foliage_ratio < 0.06:
        return False, [
            f"Non-plant image detected (only {foliage_ratio:.1%} plant foliage pixels found). Please upload a clear photo of a crop leaf."
        ]

    # Inspect crop families of top predictions
    crop1 = crop2 = None
    margin = 1.0
    if alternatives and len(alternatives) >= 1:
        crop1 = str(alternatives[0].get("label", "")).split("___")[0]
        if len(alternatives) >= 2:
            crop2 = str(alternatives[1].get("label", "")).split("___")[0]
            top1_conf = float(alternatives[0].get("confidence", confidence))
            top2_conf = float(alternatives[1].get("confidence", 0.0))
            margin = top1_conf - top2_conf

    is_same_crop = (crop1 is not None and crop2 is not None and crop1 == crop2)

    # 3. Non-plant rejection for marginal scenes (e.g. sports ground, park lawn in background of person):
    # If plant foliage is sparse (< 20%) AND model confidence is low (< 45%), or margin is tiny,
    # the subject is not a crop leaf.
    if foliage_ratio < 0.20 and (confidence < 0.45 or (not is_same_crop and margin < 0.15)):
        return False, [
            f"Ambiguous non-crop scene: Low crop foliage presence ({foliage_ratio:.1%}) with split predictions ({crop1} vs {crop2}). Please upload a close-up photo where the crop leaf fills most of the frame."
        ]

    # 4. Pure noise or completely unrecognized image check:
    if confidence < 0.25:
        return False, [
            f"Unrecognized subject or unsupported plant: Model confidence is only {confidence:.1%}. Please ensure the leaf belongs to one of the 14 supported crops and is clearly focused."
        ]

    # 5. Genuine crop leaves (foliage_ratio >= 0.20 or confidence >= 0.25):
    # ALWAYS accept and provide transparent diagnostic advisory:
    if confidence < 0.65:
        if is_same_crop and alternatives and len(alternatives) >= 2:
            alt_disease = str(alternatives[1].get("label", "")).replace("___", " ")
            warnings.append(
                f"Moderate confidence ({confidence:.1%}): Symptoms strongly suggest {crop1} disease, but closely resemble {alt_disease}. Inspect both upper and lower leaf surfaces."
            )
        elif not is_same_crop and alternatives and len(alternatives) >= 2:
            alt_crop = crop2
            warnings.append(
                f"Field lighting / lesion overlap ({confidence:.1%}): Primary diagnosis is {crop1}, with secondary possibility of {alt_crop} ({margin:.1%} margin). Verify lesion pattern against {crop1} symptoms."
            )
        else:
            warnings.append(
                f"Moderate confidence ({confidence:.1%}): for highest diagnosis accuracy, ensure the leaf is well-lit and fills at least 60% of the camera frame."
            )

    return True, warnings
