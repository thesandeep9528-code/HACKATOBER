"""One-time converter for the cloned reference's legacy MobileNetV2 H5 artifact.

This exists solely to make the local demonstration runnable before official data
arrives. Its 38 PlantVillage labels are not the SIH organizer label registry and
must never be reported as the official AgriSmart model.
"""
from __future__ import annotations

import json
from pathlib import Path


def _weights(group):
    import numpy as np

    values: dict[str, object] = {}

    def collect(name, obj):
        if hasattr(obj, "shape"):
            values[name.rsplit("/", 1)[-1].replace(":0", "")] = np.array(obj)

    group.visititems(collect)
    return values


def _copy_conv(target, values, *, depthwise=False):
    import torch

    kernel = torch.from_numpy(values["depthwise_kernel" if depthwise else "kernel"])
    if depthwise:
        kernel = kernel.permute(2, 3, 0, 1).reshape(target.weight.shape)
    else:
        kernel = kernel.permute(3, 2, 0, 1)
    target.weight.data.copy_(kernel)


def _copy_bn(target, values):
    import torch

    target.eps = 1e-3  # TensorFlow MobileNetV2 batch-normalisation epsilon.
    target.weight.data.copy_(torch.from_numpy(values["gamma"]))
    target.bias.data.copy_(torch.from_numpy(values["beta"]))
    target.running_mean.data.copy_(torch.from_numpy(values["moving_mean"]))
    target.running_var.data.copy_(torch.from_numpy(values["moving_variance"]))


def convert(h5_path: str | Path, categories_path: str | Path, output_dir: str | Path) -> tuple[Path, Path]:
    """Convert the known reference Functional(MobileNetV2 + GAP + Dense) model."""
    import h5py
    import torch
    from torchvision.models import mobilenet_v2

    h5_path, categories_path, output_dir = Path(h5_path), Path(categories_path), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    weights_path, labels_path = output_dir / "legacy_mobilenetv2.pt", output_dir / "legacy_class_names.json"
    if weights_path.is_file() and labels_path.is_file():
        return weights_path, labels_path
    classes_by_index = json.loads(categories_path.read_text(encoding="utf-8"))
    classes = [classes_by_index[str(index)] for index in range(len(classes_by_index))]
    model = mobilenet_v2(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(classes))
    with h5py.File(h5_path, "r") as source:
        root = source["model_weights"]
        base = root["mobilenetv2_1.00_224"]
        _copy_conv(model.features[0][0], _weights(base["Conv1"]))
        _copy_bn(model.features[0][1], _weights(base["bn_Conv1"]))
        first = model.features[1].conv
        _copy_conv(first[0][0], _weights(base["expanded_conv_depthwise"]), depthwise=True)
        _copy_bn(first[0][1], _weights(base["expanded_conv_depthwise_BN"]))
        _copy_conv(first[1], _weights(base["expanded_conv_project"]))
        _copy_bn(first[2], _weights(base["expanded_conv_project_BN"]))
        for block_index in range(1, 17):
            block = model.features[block_index + 1].conv
            prefix = f"block_{block_index}"
            _copy_conv(block[0][0], _weights(base[f"{prefix}_expand"]))
            _copy_bn(block[0][1], _weights(base[f"{prefix}_expand_BN"]))
            _copy_conv(block[1][0], _weights(base[f"{prefix}_depthwise"]), depthwise=True)
            _copy_bn(block[1][1], _weights(base[f"{prefix}_depthwise_BN"]))
            _copy_conv(block[2], _weights(base[f"{prefix}_project"]))
            _copy_bn(block[3], _weights(base[f"{prefix}_project_BN"]))
        _copy_conv(model.features[18][0], _weights(base["Conv_1"]))
        _copy_bn(model.features[18][1], _weights(base["Conv_1_bn"]))
        dense = _weights(root["dense"])
        model.classifier[1].weight.data.copy_(torch.from_numpy(dense["kernel"].T))
        model.classifier[1].bias.data.copy_(torch.from_numpy(dense["bias"]))
    torch.save(model.state_dict(), weights_path)
    labels_path.write_text(json.dumps(classes, indent=2), encoding="utf-8")
    return weights_path, labels_path
