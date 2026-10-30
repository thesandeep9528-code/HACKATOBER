"""Create a reproducible stratified train/validation layout from PlantVillage raw/color.

The source remains untouched. Output images are NTFS hard links when supported,
so the split does not double disk usage. This public baseline is not an official
SIH split and must never be presented as organizer-held-out performance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

VALID_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def stable_order(paths: list[Path], seed: int) -> list[Path]:
    return sorted(paths, key=lambda path: hashlib.sha256(f"{seed}:{path.name}".encode()).hexdigest())


def link_or_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True, help="PlantVillage raw/color directory")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--max-per-class", type=int, default=0, help="Use only for a fast baseline; 0 means all images.")
    args = parser.parse_args()
    if not 0 < args.val_fraction < 1:
        raise SystemExit("--val-fraction must be between 0 and 1")
    source, output = Path(args.source_dir), Path(args.output_dir)
    classes = sorted(directory.name for directory in source.iterdir() if directory.is_dir())
    if len(classes) < 2:
        raise SystemExit("Expected PlantVillage class directories under --source-dir")
    manifest: dict[str, dict[str, int]] = defaultdict(dict)
    seen_hashes: set[str] = set()
    total_skipped_duplicates = 0
    for label in classes:
        raw_images = [path for path in (source / label).iterdir() if path.is_file() and path.suffix.lower() in VALID_SUFFIXES]
        raw_images = stable_order(raw_images, args.seed)
        images: list[Path] = []
        for path in raw_images:
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            if h in seen_hashes:
                total_skipped_duplicates += 1
                continue
            seen_hashes.add(h)
            images.append(path)
        if args.max_per_class:
            images = images[: args.max_per_class]
        if len(images) < 2:
            raise SystemExit(f"{label} has fewer than two images")
        val_count = max(1, round(len(images) * args.val_fraction))
        for split, paths in (("val", images[:val_count]), ("train", images[val_count:])):
            for path in paths:
                link_or_copy(path, output / split / label / path.name)
            manifest[label][split] = len(paths)
    metadata = {
        "source": str(source),
        "source_dataset": "PlantVillage raw/color",
        "seed": args.seed,
        "val_fraction": args.val_fraction,
        "max_per_class": args.max_per_class or None,
        "labels": classes,
        "counts": manifest,
        "deduplicated_images_removed": total_skipped_duplicates,
        "organizer_held_out_test_used": False,
    }
    (output / "public_baseline_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"classes": len(classes), "train_images": sum(row["train"] for row in manifest.values()), "val_images": sum(row["val"] for row in manifest.values()), "duplicates_removed": total_skipped_duplicates}))


if __name__ == "__main__":
    main()
