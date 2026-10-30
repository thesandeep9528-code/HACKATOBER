from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def file_hashes(root: Path) -> dict[str, list[str]]:
    """Detect exact byte duplicates within a supplied split before fitting."""
    from concurrent.futures import ThreadPoolExecutor

    def hash_file(path: Path) -> tuple[str, str]:
        return hashlib.sha256(path.read_bytes()).hexdigest(), str(path)

    files = [p for p in root.rglob("*") if p.is_file()]
    result: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=16) as ex:
        for digest, path_str in ex.map(hash_file, files):
            result.setdefault(digest, []).append(path_str)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a reproducible AgriSmart classifier on permitted train/val data.")
    parser.add_argument("--train-dir", required=True)
    parser.add_argument("--val-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--pretrained-weights", default=None, help="Path to checkpoint weights to warm-start fine-tuning")
    parser.add_argument("--resume", action="store_true", help="Resume training from existing checkpoint in output_dir")
    args = parser.parse_args()

    import numpy as np
    import torch
    from sklearn.metrics import f1_score
    from torch import nn
    from torch.utils.data import DataLoader
    from torchvision import datasets
    from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
    from torchvision.transforms import v2

    train_dir, val_dir, output = Path(args.train_dir), Path(args.val_dir), Path(args.output_dir)
    if not train_dir.is_dir() or not val_dir.is_dir():
        raise SystemExit("Both --train-dir and --val-dir must exist. Never pass the organizer-held-out field test set.")
    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    output.mkdir(parents=True, exist_ok=True)
    print("Auditing dataset splits for exact duplicates...", flush=True)
    train_hashes, val_hashes = file_hashes(train_dir), file_hashes(val_dir)
    overlap = set(train_hashes) & set(val_hashes)
    duplicate_report = {"within_train": sum(len(v) > 1 for v in train_hashes.values()), "within_val": sum(len(v) > 1 for v in val_hashes.values()), "cross_split_exact_duplicates": len(overlap)}
    (output / "duplicate_audit.json").write_text(json.dumps(duplicate_report, indent=2), encoding="utf-8")
    print(f"Duplicate audit report: {duplicate_report}", flush=True)
    if overlap:
        raise SystemExit("Exact image duplicates occur across train and validation; fix the split before training.")

    train_tf = v2.Compose([
        v2.Resize((256, 256)),
        v2.RandomResizedCrop((224, 224), scale=(0.65, 1.0)),
        v2.RandomHorizontalFlip(),
        v2.RandomRotation(25),
        v2.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.06),
        v2.RandomApply([v2.GaussianBlur(3)], p=0.15),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        v2.RandomErasing(p=0.2, scale=(0.02, 0.2), value="random")
    ])
    val_tf = v2.Compose([v2.Resize((224, 224)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True), v2.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    train_ds, val_ds = datasets.ImageFolder(train_dir, transform=train_tf), datasets.ImageFolder(val_dir, transform=val_tf)
    if train_ds.classes != val_ds.classes:
        raise SystemExit("Train and validation class directories must be identical exact organizer labels.")
    classes = train_ds.classes
    if len(classes) < 2:
        raise SystemExit("At least two label directories are required.")
    (output / "class_names.json").write_text(json.dumps(classes, indent=2), encoding="utf-8")
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, generator=generator)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)
    counts = Counter(train_ds.targets)
    weights = torch.tensor([len(train_ds) / (len(classes) * counts[i]) for i in range(len(classes))], dtype=torch.float32)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device} | Classes: {len(classes)} | Train images: {len(train_ds)} | Val images: {len(val_ds)}", flush=True)
    backbone = efficientnet_b0(weights=EfficientNet_B0_Weights.DEFAULT)
    backbone.classifier[1] = nn.Linear(backbone.classifier[1].in_features, len(classes))
    model = backbone.to(device)

    best_f1, history, start_epoch = -1.0, [], 1
    if args.resume and (output / "best_model.pt").is_file():
        print(f"Resuming from existing checkpoint: {output / 'best_model.pt'}", flush=True)
        checkpoint_state = torch.load(output / "best_model.pt", map_location=device, weights_only=True)
        model.load_state_dict(checkpoint_state)
        if (output / "history.json").is_file():
            try:
                history = json.loads((output / "history.json").read_text(encoding="utf-8"))
                start_epoch = len(history) + 1
                best_f1 = max((h["val_macro_f1"] for h in history), default=-1.0)
                print(f"Loaded existing history ({len(history)} epochs completed, best Macro-F1: {best_f1:.4f})", flush=True)
            except Exception as e:
                print(f"Could not parse history.json: {e}", flush=True)
    elif args.pretrained_weights and Path(args.pretrained_weights).is_file():
        print(f"Warm-starting from pretrained checkpoint: {args.pretrained_weights}", flush=True)
        checkpoint_state = torch.load(args.pretrained_weights, map_location=device, weights_only=True)
        model.load_state_dict(checkpoint_state)

    loss_fn = nn.CrossEntropyLoss(weight=weights.to(device), label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-6)
    scaler = torch.cuda.amp.GradScaler(enabled=(device == "cuda"))

    for _ in range(1, start_epoch):
        scheduler.step()

    if start_epoch > args.epochs:
        print(f"Already completed {len(history)} epochs (target: {args.epochs}). Nothing to train.", flush=True)

    for epoch in range(start_epoch, args.epochs + 1):
        cur_lr = optimizer.param_groups[0]['lr']
        print(f"\nStarting epoch {epoch}/{args.epochs} (LR: {cur_lr:.6f})...", flush=True)
        model.train(); running = 0.0
        for batch_idx, (images, targets) in enumerate(train_loader, 1):
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
                logits = model(images.to(device))
                loss = loss_fn(logits, targets.to(device))
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            running += float(loss.detach()) * len(targets)
            if batch_idx % 150 == 0 or batch_idx == len(train_loader):
                print(f"  [Epoch {epoch}] Batch {batch_idx}/{len(train_loader)} - Batch Loss: {loss.item():.4f}", flush=True)

        model.eval(); actual, outputs = [], []
        print(f"Evaluating epoch {epoch} on validation set ({len(val_ds)} images)...", flush=True)
        with torch.inference_mode():
            for images, targets in val_loader:
                with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
                    preds = model(images.to(device)).argmax(dim=1).cpu().tolist()
                outputs.extend(preds); actual.extend(targets.tolist())
        macro_f1 = f1_score(actual, outputs, average="macro", zero_division=0)
        history.append({"epoch": epoch, "train_loss": running / len(train_ds), "val_macro_f1": macro_f1})
        (output / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
        print(f"Epoch {epoch} Result: {json.dumps(history[-1])}", flush=True)
        if macro_f1 > best_f1:
            best_f1 = macro_f1
            torch.save(model.cpu().state_dict(), output / "best_model.pt")
            model.to(device)
            print(f"New best model saved! (Macro-F1: {best_f1:.4f})", flush=True)
        scheduler.step()

    config = vars(args) | {"created_at": datetime.now(timezone.utc).isoformat(), "classes": classes, "device": device, "best_validation_macro_f1": best_f1, "class_counts": {classes[i]: counts[i] for i in range(len(classes))}, "augmentation": "crop/flip/rotation/color/blur", "held_out_test_used": False}
    (output / "training_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps({"best_validation_macro_f1": best_f1, "artifact": str(output / "best_model.pt")}))


if __name__ == "__main__":
    main()
