"""
SkinMeta AI — CNN Model Test Dataset Generator & Evaluator
===========================================================
Generates a synthetic labeled test dataset from publicly available
acne image URLs, or uses programmatically generated synthetic images
with ground-truth labels to validate the CNN prediction pipeline.

Classes: Blackheads, Cyst, Papules, Pustules, Whiteheads

Usage:
    python test_cnn_model.py

Outputs:
    - test_results.csv      : per-image prediction vs ground truth
    - confusion_matrix.png  : visual confusion matrix
    - evaluation_report.txt : full metrics report
"""

import os
import sys
import json
import random
import warnings
import argparse
import urllib.request
from pathlib import Path
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image, ImageDraw, ImageFilter
from collections import defaultdict, Counter
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)

warnings.filterwarnings("ignore")

# ── Configuration ──────────────────────────────────────────────────────────────
CLASSES = ["Blackheads", "Cyst", "Papules", "Pustules", "Whiteheads"]
IMG_SIZE = (224, 224)
OUTPUT_DIR = Path("test_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Ground-truth labeled image URLs (Wikimedia Commons / public domain) ────────
# These are documented, publicly licensed acne reference images.
# Each entry: (url, true_class, description)
REFERENCE_IMAGES = [
    # ── Blackheads ──
    # Open comedones - dark plugged pores, typically on nose/chin
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Blackheads_on_nose.jpg/320px-Blackheads_on_nose.jpg",
        "Blackheads",
        "Open comedones on nose — classic blackhead presentation",
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Comedone_au_niveau_de_la_joue.jpg/320px-Comedone_au_niveau_de_la_joue.jpg",
        "Blackheads",
        "Comedone on cheek — open plugged follicle",
    ),

    # ── Whiteheads ──
    # Closed comedones - flesh-colored or white small bumps
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Milia.jpg/320px-Milia.jpg",
        "Whiteheads",
        "Milia/closed comedones — small white closed plugs",
    ),

    # ── Papules ──
    # Small red/pink raised bumps without pus
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Acne_vulgaris_on_the_back.jpg/320px-Acne_vulgaris_on_the_back.jpg",
        "Papules",
        "Inflammatory papules — red raised bumps",
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Hormonal_acne.jpg/320px-Hormonal_acne.jpg",
        "Papules",
        "Hormonal acne papules — red inflamed spots",
    ),

    # ── Pustules ──
    # Red base with white/yellow pus-filled center
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Acne_vulgaris_case_report.jpg/320px-Acne_vulgaris_case_report.jpg",
        "Pustules",
        "Acne vulgaris with pustules — pus-filled lesions",
    ),

    # ── Cysts ──
    # Deep, painful nodular lesions
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Nodulocystic_acne.jpg/320px-Nodulocystic_acne.jpg",
        "Cyst",
        "Nodulocystic acne — deep painful cysts",
    ),
    (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/Cystic_acne.jpg/320px-Cystic_acne.jpg",
        "Cyst",
        "Cystic acne — severe deep lesions",
    ),
]

# ── Synthetic image generators (fallback when URLs fail) ──────────────────────
# Each generator creates a 224x224 RGB image that mimics the visual
# characteristics of the acne type, allowing testing without real photos.

def make_skin_base(size=(224, 224), tone="medium"):
    """Generate a realistic skin-tone base image."""
    tones = {
        "light":  (235, 200, 175),
        "medium": (200, 155, 120),
        "tan":    (175, 130, 95),
        "dark":   (120, 85, 60),
    }
    base_rgb = tones.get(tone, tones["medium"])
    arr = np.zeros((*size, 3), dtype=np.float32)
    for c in range(3):
        noise = np.random.normal(0, 8, size)
        arr[:, :, c] = np.clip(base_rgb[c] + noise, 0, 255)
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    return img


def generate_blackhead_image(seed=42):
    """Blackheads: dark plugged pores, low redness, high dark-spot density."""
    random.seed(seed); np.random.seed(seed)
    img = make_skin_base(tone="medium")
    draw = ImageDraw.Draw(img)
    arr = np.array(img)

    # Add 8-15 small dark circular pores
    n_pores = random.randint(8, 15)
    for _ in range(n_pores):
        x = random.randint(20, 204)
        y = random.randint(20, 204)
        r = random.randint(2, 5)
        # Very dark brown-black fill
        darkness = random.randint(15, 45)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(darkness, darkness // 2, darkness // 3),
                     outline=(darkness - 5, darkness // 3, 0))

    # Add sebaceous texture (slightly raised ring around each pore)
    for _ in range(n_pores):
        x = random.randint(20, 204)
        y = random.randint(20, 204)
        r = random.randint(6, 10)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=None,
                     outline=(160, 120, 90, 80))

    img = img.filter(ImageFilter.GaussianBlur(0.5))
    return img


def generate_whitehead_image(seed=42):
    """Whiteheads: small bright closed bumps, low redness, flesh-colored skin."""
    random.seed(seed); np.random.seed(seed)
    img = make_skin_base(tone="light")
    draw = ImageDraw.Draw(img)

    # 5-10 small bright domed bumps
    n_bumps = random.randint(5, 10)
    for _ in range(n_bumps):
        x = random.randint(20, 204)
        y = random.randint(20, 204)
        r = random.randint(4, 8)
        # Bright white/cream colored
        brightness = random.randint(215, 240)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(brightness, brightness - 5, brightness - 15))
        # Subtle outline (flesh tone rim)
        draw.ellipse([x - r - 1, y - r - 1, x + r + 1, y + r + 1],
                     fill=None, outline=(200, 165, 135))

    img = img.filter(ImageFilter.GaussianBlur(0.8))
    return img


def generate_papule_image(seed=42):
    """Papules: red raised bumps, significant redness, no pus center."""
    random.seed(seed); np.random.seed(seed)
    img = make_skin_base(tone="medium")
    draw = ImageDraw.Draw(img)

    # 4-8 red inflamed bumps
    n_papules = random.randint(4, 8)
    for _ in range(n_papules):
        x = random.randint(25, 199)
        y = random.randint(25, 199)
        r = random.randint(8, 15)

        # Red inflamed base
        red_intensity = random.randint(185, 220)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(red_intensity, random.randint(70, 100), random.randint(70, 100)))

        # Slightly lighter raised dome center (but still red, no pus)
        r2 = r - 3
        if r2 > 0:
            draw.ellipse([x - r2, y - r2, x + r2, y + r2],
                         fill=(min(red_intensity + 20, 255), 90, 80))

        # Inflammation ring
        draw.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3],
                     fill=None, outline=(red_intensity - 30, 60, 60))

    img = img.filter(ImageFilter.GaussianBlur(0.7))
    return img


def generate_pustule_image(seed=42):
    """Pustules: red base + bright white/yellow pus center — key differentiator."""
    random.seed(seed); np.random.seed(seed)
    img = make_skin_base(tone="medium")
    draw = ImageDraw.Draw(img)

    # 3-6 pustules with visible pus
    n_pustules = random.randint(3, 6)
    for _ in range(n_pustules):
        x = random.randint(25, 199)
        y = random.randint(25, 199)
        r = random.randint(9, 16)

        # Red inflamed ring
        red_val = random.randint(180, 215)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(red_val, 75, 65))

        # Inflammation halo
        draw.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4],
                     fill=None, outline=(red_val - 40, 55, 45))

        # Pus center — white/yellowish (KEY feature)
        r_pus = max(r - 4, 3)
        pus_brightness = random.randint(220, 248)
        pus_yellow = random.randint(200, 230)  # slight yellow tint
        draw.ellipse([x - r_pus, y - r_pus, x + r_pus, y + r_pus],
                     fill=(pus_brightness, pus_yellow, 180))

    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img


def generate_cyst_image(seed=42):
    """Cysts: large deep nodular lesions, high local contrast, significant redness."""
    random.seed(seed); np.random.seed(seed)
    img = make_skin_base(tone="medium")
    draw = ImageDraw.Draw(img)

    # 1-3 large deep cysts
    n_cysts = random.randint(1, 3)
    for _ in range(n_cysts):
        x = random.randint(35, 189)
        y = random.randint(35, 189)
        r = random.randint(18, 30)  # Much larger than papules/pustules

        # Deep tissue color — dark red/purple (deep nodule)
        base_r = random.randint(160, 190)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(base_r, 55, 75))

        # Outer large inflammation zone
        draw.ellipse([x - r - 8, y - r - 8, x + r + 8, y + r + 8],
                     fill=None, outline=(base_r - 30, 45, 55))
        draw.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5],
                     fill=None, outline=(base_r - 15, 50, 60))

        # Texture within cyst (shows depth)
        for _ in range(8):
            tx = x + random.randint(-r + 3, r - 3)
            ty = y + random.randint(-r + 3, r - 3)
            tr = random.randint(2, 5)
            draw.ellipse([tx - tr, ty - tr, tx + tr, ty + tr],
                         fill=(base_r - random.randint(20, 50),
                               random.randint(40, 70),
                               random.randint(55, 80)))

    # Heavier blur to simulate depth/swelling
    img = img.filter(ImageFilter.GaussianBlur(1.8))
    return img


GENERATORS = {
    "Blackheads": generate_blackhead_image,
    "Whiteheads": generate_whitehead_image,
    "Papules":    generate_papule_image,
    "Pustules":   generate_pustule_image,
    "Cyst":       generate_cyst_image,
}


# ── Image loading helpers ──────────────────────────────────────────────────────

def try_download_image(url, timeout=8):
    """Try to download image from URL. Returns PIL Image or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception as e:
        return None


def build_test_dataset(
    n_synthetic_per_class=10,
    use_online=True,
    seed=2025,
    min_per_class=3,
):
    """
    Build a labeled test dataset.

    Strategy:
      1. Try to download reference images from URLs.
      2. Ensure minimum images per class (fallback synthetic if needed).
      3. Pad with additional synthetic images to reach n_synthetic_per_class.

    Args:
        n_synthetic_per_class: target number of synthetic images per class (target)
        use_online: whether to attempt online downloads
        seed: random seed
        min_per_class: minimum guaranteed images per class (fallback trigger)

    Returns:
        list of (pil_image, true_label, source, description)
    """
    random.seed(seed)
    dataset = []

    # Step 1: Download real reference images
    if use_online:
        print("\n📥 Attempting to download reference images...")
        downloaded = defaultdict(int)
        for url, true_class, desc in REFERENCE_IMAGES:
            img = try_download_image(url)
            if img is not None:
                dataset.append((img, true_class, "online", desc))
                downloaded[true_class] += 1
                print(f"  ✅  {true_class:<15} — {desc[:55]}")
            else:
                print(f"  ⚠️   {true_class:<15} — download failed (will use synthetic)")
    else:
        downloaded = defaultdict(int)

    # Step 2: Generate synthetic images (with fallback guarantee)
    print(f"\n🎨 Generating synthetic images (min {min_per_class}, target {n_synthetic_per_class} per class)...")
    for cls in CLASSES:
        have = downloaded.get(cls, 0)
        # Ensure at least min_per_class (fallback if downloads failed)
        need_min = max(min_per_class - have, 0)
        # Then pad to target count
        need_total = max(need_min, n_synthetic_per_class - have)
        
        for i in range(need_total):
            s = seed + hash(cls) % 1000 + i * 7
            img = GENERATORS[cls](seed=s)
            dataset.append((
                img, cls, "synthetic",
                f"Synthetic {cls} sample #{have + i + 1} (seed={s})"
            ))
        total = have + need_total
        print(f"  {cls:<15} → {have} online + {need_total} synthetic = {total} total")

    print(f"\n✅ Dataset ready: {len(dataset)} labeled images across {len(CLASSES)} classes")
    return dataset


# ── CNN Prediction ─────────────────────────────────────────────────────────────

def run_predictions(dataset, model_path=None, verbose=True):
    """
    Run CNN predictions on each image in the dataset.

    Returns:
        list of dicts with prediction details
    """
    # Import from project
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from utils.cnn_model import CNNModel
        model = CNNModel(model_path=model_path or "models/acne_cnn_model.keras")
        print(f"\n🤖 Model loaded. Demo mode: {model.model is None}")
    except ImportError as e:
        print(f"⚠️  Could not import cnn_model: {e}")
        print("   Make sure cnn_model.py is in utils/ directory.")
        return []

    results = []
    print(f"\n🔬 Running predictions on {len(dataset)} images...")
    print("-" * 70)

    for i, (img, true_label, source, desc) in enumerate(dataset):
        # Convert PIL image → bytes
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=92)
        img_bytes = buf.getvalue()

        try:
            pred = model.predict(img_bytes)
            pred_class = pred["acne_type"]
            confidence = pred["confidence"]
            probs = pred["probabilities"]
            correct = (pred_class == true_label)

            results.append({
                "index":          i + 1,
                "true_label":     true_label,
                "pred_label":     pred_class,
                "correct":        correct,
                "confidence":     round(confidence, 4),
                "source":         source,
                "description":    desc,
                "demo_mode":      pred.get("demo_mode", True),
                **{f"prob_{c}": round(probs.get(c, 0), 4) for c in CLASSES},
            })

            status = "✅" if correct else "❌"
            if verbose or not correct:
                print(f"  [{i+1:3d}] {status}  True: {true_label:<15} Pred: {pred_class:<15}"
                      f"  Conf: {confidence:.2%}  [{source}]")

        except Exception as e:
            print(f"  [{i+1:3d}] ERROR: {e}")
            results.append({
                "index": i + 1, "true_label": true_label,
                "pred_label": "ERROR", "correct": False,
                "confidence": 0.0, "source": source,
                "description": desc, "demo_mode": True,
                **{f"prob_{c}": 0.0 for c in CLASSES},
            })

    return results


# ── Evaluation & Visualisation ─────────────────────────────────────────────────

def evaluate(results):
    """Compute classification metrics."""
    df = pd.DataFrame(results)
    df = df[df["pred_label"] != "ERROR"]

    y_true = df["true_label"].tolist()
    y_pred = df["pred_label"].tolist()

    acc = accuracy_score(y_true, y_pred)
    f1  = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, labels=CLASSES,
                            average=None, zero_division=0)
    report = classification_report(y_true, y_pred, labels=CLASSES,
                                   zero_division=0, output_dict=True)

    return {
        "accuracy":       acc,
        "f1_weighted":    f1,
        "f1_per_class":   dict(zip(CLASSES, f1_per_class)),
        "report_dict":    report,
        "report_text":    classification_report(y_true, y_pred, labels=CLASSES, zero_division=0),
        "cm":             confusion_matrix(y_true, y_pred, labels=CLASSES),
        "y_true":         y_true,
        "y_pred":         y_pred,
        "df":             df,
    }


def plot_confusion_matrix(cm, title="Confusion Matrix"):
    """Plot and save a styled confusion matrix."""
    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor("#FAFAFA")

    im = ax.imshow(cm, cmap="YlOrRd", aspect="auto")
    plt.colorbar(im, ax=ax, shrink=0.8)

    ax.set_xticks(range(len(CLASSES)))
    ax.set_yticks(range(len(CLASSES)))
    ax.set_xticklabels(CLASSES, rotation=35, ha="right", fontsize=10)
    ax.set_yticklabels(CLASSES, fontsize=10)

    # Annotate cells
    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            val = cm[i, j]
            color = "white" if val > cm.max() * 0.6 else "black"
            ax.text(j, i, str(val), ha="center", va="center",
                    color=color, fontweight="bold", fontsize=12)

    ax.set_xlabel("Predicted Class", fontsize=12, fontweight="bold")
    ax.set_ylabel("True Class", fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()

    path = OUTPUT_DIR / "confusion_matrix.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Confusion matrix saved: {path}")
    return path


def plot_per_class_metrics(metrics_dict):
    """Bar chart of per-class F1, precision, recall."""
    report = metrics_dict["report_dict"]
    classes_data = {
        cls: {
            "Precision": report.get(cls, {}).get("precision", 0),
            "Recall":    report.get(cls, {}).get("recall", 0),
            "F1":        report.get(cls, {}).get("f1-score", 0),
        }
        for cls in CLASSES
    }

    df_plot = pd.DataFrame(classes_data).T
    x = np.arange(len(CLASSES))
    w = 0.26

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#FAFAFA")

    bars_p = ax.bar(x - w, df_plot["Precision"], w, label="Precision",
                    color="#2196F3", edgecolor="white", linewidth=1.2)
    bars_r = ax.bar(x,     df_plot["Recall"],    w, label="Recall",
                    color="#4CAF50", edgecolor="white", linewidth=1.2)
    bars_f = ax.bar(x + w, df_plot["F1"],        w, label="F1-Score",
                    color="#FF9800", edgecolor="white", linewidth=1.2)

    for bars in [bars_p, bars_r, bars_f]:
        for bar in bars:
            h = bar.get_height()
            if h > 0.01:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                        f"{h:.2f}", ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(CLASSES, fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title("Per-Class Classification Metrics", fontsize=14, fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    ax.set_facecolor("#F8F8F8")

    # Overall metrics in corner
    acc  = metrics_dict["accuracy"]
    f1w  = metrics_dict["f1_weighted"]
    ax.text(0.98, 0.97, f"Overall Accuracy: {acc:.1%}\nWeighted F1: {f1w:.1%}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=10, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#CCCCCC"))

    plt.tight_layout()
    path = OUTPUT_DIR / "per_class_metrics.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Per-class metrics chart saved: {path}")
    return path


def plot_confidence_distribution(df):
    """Violin/box chart of confidence scores split by correct/wrong."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor("#FAFAFA")

    # Left: confidence by correctness
    correct_conf   = df[df["correct"] == True]["confidence"]
    incorrect_conf = df[df["correct"] == False]["confidence"]

    axes[0].hist(correct_conf, bins=20, alpha=0.75, color="#4CAF50",
                 edgecolor="white", label=f"Correct ({len(correct_conf)})")
    axes[0].hist(incorrect_conf, bins=20, alpha=0.75, color="#F44336",
                 edgecolor="white", label=f"Incorrect ({len(incorrect_conf)})")
    axes[0].axvline(correct_conf.mean() if len(correct_conf) else 0.5,
                    color="#2E7D32", linestyle="--", linewidth=2,
                    label=f"Correct mean: {correct_conf.mean():.2f}")
    axes[0].axvline(incorrect_conf.mean() if len(incorrect_conf) else 0.5,
                    color="#B71C1C", linestyle="--", linewidth=2,
                    label=f"Incorrect mean: {incorrect_conf.mean():.2f}")
    axes[0].set_xlabel("Confidence Score", fontweight="bold")
    axes[0].set_ylabel("Count", fontweight="bold")
    axes[0].set_title("Confidence Distribution\n(Correct vs Incorrect)", fontweight="bold")
    axes[0].legend(fontsize=9)
    axes[0].set_facecolor("#F8F8F8")

    # Right: per-class confidence
    class_conf = [df[df["true_label"] == c]["confidence"].tolist() for c in CLASSES]
    colors_bp = ["#1565C0", "#6A1B9A", "#E65100", "#C62828", "#1B5E20"]
    bp = axes[1].boxplot(class_conf, labels=CLASSES, patch_artist=True, notch=False)
    for patch, color in zip(bp["boxes"], colors_bp):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    for median_line in bp["medians"]:
        median_line.set_color("white")
        median_line.set_linewidth(2)
    axes[1].set_xlabel("Class", fontweight="bold")
    axes[1].set_ylabel("Confidence", fontweight="bold")
    axes[1].set_title("Confidence Range by Class", fontweight="bold")
    axes[1].set_xticklabels(CLASSES, rotation=25, ha="right")
    axes[1].set_facecolor("#F8F8F8")

    plt.tight_layout()
    path = OUTPUT_DIR / "confidence_distribution.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Confidence distribution saved: {path}")
    return path


def plot_sample_grid(dataset, results, n_per_class=2):
    """Grid of sample images with true/pred labels overlaid."""
    fig_h = n_per_class * len(CLASSES)
    fig, axes = plt.subplots(len(CLASSES), n_per_class,
                             figsize=(n_per_class * 3.5, fig_h * 3.2))
    fig.suptitle("Sample Images: True Label vs Prediction",
                 fontsize=14, fontweight="bold", y=1.01)
    fig.patch.set_facecolor("#FAFAFA")

    results_by_class = defaultdict(list)
    for r in results:
        results_by_class[r["true_label"]].append(r)

    for row_idx, cls in enumerate(CLASSES):
        cls_results = results_by_class[cls][:n_per_class]

        for col_idx in range(n_per_class):
            ax = axes[row_idx][col_idx] if n_per_class > 1 else axes[row_idx]

            if col_idx < len(cls_results):
                r = cls_results[col_idx]
                img_idx = r["index"] - 1
                img, true_lbl, src, desc = dataset[img_idx]

                ax.imshow(img)
                correct = r["correct"]
                color = "#2E7D32" if correct else "#C62828"
                status = "✓" if correct else "✗"
                ax.set_title(
                    f"True: {true_lbl}\nPred: {r['pred_label']} {status}  ({r['confidence']:.0%})",
                    fontsize=8, color=color, fontweight="bold", pad=4
                )
                # Source badge
                badge_col = "#E3F2FD" if src == "online" else "#FFF9C4"
                ax.text(0.02, 0.02, src, transform=ax.transAxes,
                        fontsize=6, color="#333",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor=badge_col, alpha=0.8))
            else:
                ax.text(0.5, 0.5, "N/A", ha="center", va="center",
                        fontsize=12, color="gray")

            ax.axis("off")

        # Row label
        axes[row_idx][0].set_ylabel(cls, fontsize=11, fontweight="bold",
                                    rotation=0, labelpad=65)

    plt.tight_layout()
    path = OUTPUT_DIR / "sample_predictions.png"
    plt.savefig(path, dpi=140, bbox_inches="tight")
    plt.close()
    print(f"  📊 Sample grid saved: {path}")
    return path


def save_report(metrics_dict, results, output_path):
    """Write a full text evaluation report."""
    df = metrics_dict["df"]
    acc = metrics_dict["accuracy"]
    f1w = metrics_dict["f1_weighted"]

    lines = [
        "=" * 70,
        "  SKINMETA AI — CNN MODEL EVALUATION REPORT",
        "=" * 70,
        "",
        f"  Model:      EfficientNetB0 (5-class acne classifier)",
        f"  Classes:    {', '.join(CLASSES)}",
        f"  Test images:{len(results)} total",
        f"  Online:     {sum(1 for r in results if r['source'] == 'online')}",
        f"  Synthetic:  {sum(1 for r in results if r['source'] == 'synthetic')}",
        f"  Demo mode:  {results[0]['demo_mode'] if results else 'N/A'}",
        "",
        "-" * 70,
        "  OVERALL PERFORMANCE",
        "-" * 70,
        f"  Accuracy (overall)   : {acc:.4f}  ({acc:.1%})",
        f"  F1-Score (weighted)  : {f1w:.4f}  ({f1w:.1%})",
        "",
        "-" * 70,
        "  PER-CLASS METRICS",
        "-" * 70,
        metrics_dict["report_text"],
        "",
        "-" * 70,
        "  CONFUSION MATRIX",
        "-" * 70,
        "  Rows = True Class | Columns = Predicted Class",
        "",
        "  " + "  ".join(f"{c[:6]:>8}" for c in CLASSES),
    ]

    cm = metrics_dict["cm"]
    for i, cls in enumerate(CLASSES):
        row_str = "  ".join(f"{cm[i, j]:>8}" for j in range(len(CLASSES)))
        lines.append(f"  {cls[:12]:<12}  {row_str}")

    lines += [
        "",
        "-" * 70,
        "  PER-PREDICTION DETAIL",
        "-" * 70,
    ]
    for r in results:
        status = "OK" if r["correct"] else "FAIL"
        lines.append(
            f"  [{r['index']:3d}] {status:<4} | True: {r['true_label']:<15} "
            f"Pred: {r['pred_label']:<15} Conf: {r['confidence']:.2%} | {r['source']}"
        )

    lines += [
        "",
        "=" * 70,
        "  INTERPRETATION NOTES",
        "=" * 70,
        "",
        "  If using demo mode (no trained model file):",
        "  - Predictions are heuristic-based (RGB/texture analysis).",
        "  - Expect 40-65% accuracy on synthetic images.",
        "  - To use the real CNN, place model at: models/acne_cnn_model.keras",
        "",
        "  If using a trained model:",
        "  - EfficientNetB0 trained on tiswan14/acne-dataset-image",
        "  - Uses preprocess_input() (NOT /255 normalization) — critical.",
        "  - Expected accuracy: 75-90% on real test images.",
        "",
        "  Low confidence scores (< 55%) suggest:",
        "  - Ambiguous image (e.g. mixed acne types)",
        "  - Wrong normalization applied to real model",
        "  - Image quality issues (blur, lighting, no face visible)",
        "",
        "=" * 70,
    ]

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  📄 Report saved: {output_path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SkinMeta CNN Model Tester")
    parser.add_argument("--no-online",    action="store_true",  help="Skip online image downloads")
    parser.add_argument("--synthetic",    type=int, default=10, help="Synthetic images per class (default: 10)")
    parser.add_argument("--model",        type=str, default=None, help="Path to .keras model file")
    parser.add_argument("--quiet",        action="store_true",  help="Suppress per-image logs")
    args = parser.parse_args()

    print("=" * 70)
    print("  SkinMeta AI — CNN Model Test Suite")
    print("=" * 70)
    print(f"  Classes          : {', '.join(CLASSES)}")
    print(f"  Synthetic/class  : {args.synthetic}")
    print(f"  Online images    : {'disabled' if args.no_online else 'enabled (with fallback)'}")
    print(f"  Output dir       : {OUTPUT_DIR}/")

    # Step 1: Build dataset
    dataset = build_test_dataset(
        n_synthetic_per_class=args.synthetic,
        use_online=not args.no_online,
        min_per_class=3,  # Ensure at least 3 images per class even if --synthetic 0
    )

    # Step 2: Run predictions
    results = run_predictions(
        dataset,
        model_path=args.model,
        verbose=not args.quiet,
    )

    if not results:
        print("\n❌ No results — check that cnn_model.py is in the same directory.")
        return

    # Step 3: Evaluate
    print("\n📈 Computing evaluation metrics...")
    metrics = evaluate(results)

    print(f"\n  Overall Accuracy : {metrics['accuracy']:.1%}")
    print(f"  Weighted F1      : {metrics['f1_weighted']:.1%}")
    print("\n  Per-class F1:")
    for cls, f1 in metrics["f1_per_class"].items():
        bar = "█" * int(f1 * 20) + "░" * (20 - int(f1 * 20))
        print(f"    {cls:<15} {bar} {f1:.1%}")

    # Step 4: Save outputs
    print("\n💾 Saving outputs...")
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_DIR / "test_results.csv", index=False)
    print(f"  📄 test_results.csv saved ({len(df_results)} rows)")

    plot_confusion_matrix(metrics["cm"], title="Confusion Matrix — Acne Classification")
    plot_per_class_metrics(metrics)
    plot_confidence_distribution(metrics["df"])
    plot_sample_grid(dataset, results, n_per_class=2)
    save_report(metrics, results, OUTPUT_DIR / "evaluation_report.txt")

    print("\n" + "=" * 70)
    print("  TEST COMPLETE")
    print("=" * 70)
    print(f"\n  All outputs saved to: {OUTPUT_DIR}/")
    print("  Files:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        size = f.stat().st_size
        print(f"    {f.name:<35} ({size // 1024} KB)")

    # ── Quick sanity summary ──
    print(f"\n  {'✅' if metrics['accuracy'] > 0.6 else '⚠️ '} Accuracy:  {metrics['accuracy']:.1%}")
    demo = results[0].get("demo_mode", True) if results else True
    if demo:
        print("\n  ⚠️  Running in DEMO MODE (no trained model file found).")
        print("     Predictions use heuristic image analysis, not deep learning.")
        print("     Place your trained model at: models/acne_cnn_model.keras")
        print("     The model must be EfficientNetB0 with preprocess_input() preprocessing.")
    else:
        print("\n  ✅  Running with real trained CNN model.")


if __name__ == "__main__":
    main()