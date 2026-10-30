from __future__ import annotations

import argparse
import hashlib
import io
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image

PLANTDOC_TO_PLANTVILLAGE: dict[str, str] = {
    "Apple Scab Leaf": "Apple___Apple_scab",
    "Apple leaf": "Apple___healthy",
    "Apple rust leaf": "Apple___Cedar_apple_rust",
    "Bell_pepper leaf spot": "Pepper,_bell___Bacterial_spot",
    "Bell_pepper leaf": "Pepper,_bell___healthy",
    "Blueberry leaf": "Blueberry___healthy",
    "Cherry leaf": "Cherry_(including_sour)___healthy",
    "Corn Gray leaf spot": "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn leaf blight": "Corn_(maize)___Northern_Leaf_Blight",
    "Corn rust leaf": "Corn_(maize)___Common_rust_",
    "Peach leaf": "Peach___healthy",
    "Potato leaf early blight": "Potato___Early_blight",
    "Potato leaf late blight": "Potato___Late_blight",
    "Raspberry leaf": "Raspberry___healthy",
    "Soyabean leaf": "Soybean___healthy",
    "Squash Powdery mildew leaf": "Squash___Powdery_mildew",
    "Strawberry leaf": "Strawberry___healthy",
    "Tomato Early blight leaf": "Tomato___Early_blight",
    "Tomato Septoria leaf spot": "Tomato___Septoria_leaf_spot",
    "Tomato leaf bacterial spot": "Tomato___Bacterial_spot",
    "Tomato leaf late blight": "Tomato___Late_blight",
    "Tomato leaf mosaic virus": "Tomato___Tomato_mosaic_virus",
    "Tomato leaf yellow virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato leaf": "Tomato___healthy",
    "Tomato mold leaf": "Tomato___Leaf_Mold",
    "Tomato two spotted spider mites leaf": "Tomato___Spider_mites Two-spotted_spider_mite",
    "grape leaf black rot": "Grape___Black_rot",
    "grape leaf": "Grape___healthy",
}


def compute_file_hash(path: Path) -> tuple[str, Path]:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest(), path


def get_existing_hashes(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        return {}
    files = [p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    with ThreadPoolExecutor(max_workers=16) as pool:
        return dict(pool.map(compute_file_hash, files))


def extract_git_blob(repo_dir: Path, blob_sha: str) -> bytes:
    cmd = ["git", "-C", str(repo_dir), "cat-file", "-p", blob_sha]
    return subprocess.check_output(cmd)


def ingest_from_git_tree(
    repo_dir: Path,
    train_dir: Path,
    val_dir: Path,
    all_existing_hashes: set[str],
) -> tuple[int, int, int]:
    """Read git tree objects directly from local repo, bypassing Windows NTFS filename limits."""
    ls_out = subprocess.check_output(
        ["git", "-C", str(repo_dir), "ls-tree", "-r", "HEAD"],
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    added_train = added_val = skipped_dupe = skipped_corrupt = 0

    for line in ls_out.strip().splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            continue
        _mode, obj_type, blob_sha, git_path = parts
        if obj_type != "blob":
            continue

        path_parts = Path(git_path).parts
        if len(path_parts) < 3:
            continue
        split_name = path_parts[0].lower()
        category_name = path_parts[1]
        filename = path_parts[-1]

        # Determine target split
        if split_name == "train":
            target_root = train_dir
        elif split_name in ("test", "val"):
            target_root = val_dir
        else:
            continue

        # Match category to PlantVillage ontology
        mapped_class = PLANTDOC_TO_PLANTVILLAGE.get(category_name)
        if not mapped_class:
            for k, v in PLANTDOC_TO_PLANTVILLAGE.items():
                if k.lower() == category_name.lower():
                    mapped_class = v
                    break
        if not mapped_class:
            continue

        target_class_dir = target_root / mapped_class
        target_class_dir.mkdir(parents=True, exist_ok=True)

        try:
            blob_bytes = extract_git_blob(repo_dir, blob_sha)
        except Exception as e:
            skipped_corrupt += 1
            continue

        # Validate with PIL
        try:
            with Image.open(io.BytesIO(blob_bytes)) as im:
                im.verify()
        except Exception:
            skipped_corrupt += 1
            continue

        img_hash = hashlib.sha256(blob_bytes).hexdigest()
        if img_hash in all_existing_hashes:
            skipped_dupe += 1
            continue

        all_existing_hashes.add(img_hash)
        dest_file = target_class_dir / f"plantdoc_{img_hash[:12]}.jpg"

        try:
            with Image.open(io.BytesIO(blob_bytes)) as im:
                rgb_im = im.convert("RGB")
                rgb_im.save(dest_file, "JPEG", quality=95)
            if split_name == "train":
                added_train += 1
            else:
                added_val += 1
        except Exception as err:
            print(f"Failed to write image {filename}: {err}")
            skipped_corrupt += 1

    return added_train, added_val, skipped_dupe, skipped_corrupt


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PlantDoc in-field dataset directly from local git tree.")
    parser.add_argument("--plantdoc-dir", default="data/plantdoc_raw", help="Path to cloned PlantDoc repo")
    parser.add_argument("--train-dir", default="data/train", help="Path to project train directory")
    parser.add_argument("--val-dir", default="data/val", help="Path to project val directory")
    args = parser.parse_args()

    plantdoc_root = Path(args.plantdoc_dir)
    train_dir = Path(args.train_dir)
    val_dir = Path(args.val_dir)

    print("Auditing existing train and validation images...")
    train_hashes = set(get_existing_hashes(train_dir).keys())
    val_hashes = set(get_existing_hashes(val_dir).keys())
    all_existing = train_hashes | val_hashes
    print(f"Existing: {len(train_hashes)} train images, {len(val_hashes)} val images.")

    print("\nExtracting and ingesting PlantDoc in-field images from git tree...")
    a_tr, a_val, d_skip, err_skip = ingest_from_git_tree(plantdoc_root, train_dir, val_dir, all_existing)
    print(f"PlantDoc Ingest Complete: {a_tr} added to train, {a_val} added to val, {d_skip} duplicates skipped, {err_skip} corrupt skipped.")

    # Cross-split duplicate verification
    print("\nVerifying zero data leakage across splits...")
    final_train = set(get_existing_hashes(train_dir).keys())
    final_val = set(get_existing_hashes(val_dir).keys())
    overlap = final_train & final_val
    print(f"Updated Dataset: {len(final_train)} train images | {len(final_val)} val images.")
    print(f"Cross-split duplicates: {len(overlap)}")
    if overlap:
        raise SystemExit(f"CRITICAL: Found {len(overlap)} cross-split duplicates!")
    print("Zero-leakage verified successfully!")


if __name__ == "__main__":
    main()
