from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from model.predict import ArtifactPredictor


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate only a permitted labelled dataset.")
    parser.add_argument("--weights", required=True)
    parser.add_argument("--class-names", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    classes = json.loads(Path(args.class_names).read_text(encoding="utf-8"))
    root, output = Path(args.data_dir), Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    import torch
    from torch.utils.data import DataLoader
    from torchvision import datasets
    from torchvision.models import efficientnet_b0
    from torchvision.transforms import v2

    device = "cuda" if torch.cuda.is_available() else "cpu"
    val_tf = v2.Compose([v2.Resize((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    val_ds = datasets.ImageFolder(root, transform=val_tf)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0)

    model = efficientnet_b0(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(classes))
    model.load_state_dict(torch.load(args.weights, map_location=device, weights_only=True))
    model.to(device).eval()

    truth, predicted = [], []
    with torch.inference_mode():
        for images, targets in val_loader:
            preds = model(images.to(device)).argmax(dim=1).cpu().tolist()
            predicted.extend([classes[p] for p in preds])
            truth.extend([val_ds.classes[t] for t in targets.tolist()])
    if not truth:
        raise SystemExit("No labelled images found under --data-dir/<exact-label>/.")
    report = classification_report(truth, predicted, labels=classes, output_dict=True, zero_division=0)
    metrics = {"macro_f1": f1_score(truth, predicted, labels=classes, average="macro", zero_division=0), "accuracy": accuracy_score(truth, predicted), "per_class": report}
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    with (output / "per_class_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle); writer.writerow(["label", "precision", "recall", "f1", "support"])
        for label in classes:
            row = report[label]; writer.writerow([label, row["precision"], row["recall"], row["f1-score"], row["support"]])
    matrix = confusion_matrix(truth, predicted, labels=classes)
    np.savetxt(output / "confusion_matrix.csv", matrix, delimiter=",", fmt="%d")
    for normalized, name in ((False, "confusion_matrix.png"), (True, "confusion_matrix_normalized.png")):
        values = matrix.astype(float); values = values / np.maximum(values.sum(axis=1, keepdims=True), 1) if normalized else values
        fig, ax = plt.subplots(figsize=(max(8, len(classes)), max(7, len(classes))))
        ax.imshow(values, cmap="Blues"); ax.set(xticks=range(len(classes)), yticks=range(len(classes)), xticklabels=classes, yticklabels=classes)
        plt.setp(ax.get_xticklabels(), rotation=90, ha="center"); fig.tight_layout(); fig.savefig(output / name, dpi=180); plt.close(fig)


if __name__ == "__main__":
    main()
