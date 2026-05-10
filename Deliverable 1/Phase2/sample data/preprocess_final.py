"""
SkinMeta - Data Cleaning, Preprocessing & EDA 
==============================================================
Handles the exact features from generate_dataset_final.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
import os, json

os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/eda_charts", exist_ok=True)

sns.set_theme(style="whitegrid")
PAL = "Set2"

# ═══════════════════════════════════════════════════
# 1. LOAD RAW DATA
# ═══════════════════════════════════════════════════
df = pd.read_csv("data/raw/user_profiles_raw.csv")
print("=" * 55)
print("  SkinMeta - Phase 2 Preprocessing (Final)")
print("=" * 55)
print(f"\nRaw shape      : {df.shape}")
print(f"Duplicates     : {df.duplicated().sum()}")
print(f"\nMissing values:\n{df.isnull().sum()[df.isnull().sum() > 0].to_string()}")

# ═══════════════════════════════════════════════════
# 2. REMOVE DUPLICATES
# ═══════════════════════════════════════════════════
before = len(df)
df = df.drop_duplicates()
print(f"\n[Dedup] Removed {before - len(df)} rows -> {len(df)} remain")

# ═══════════════════════════════════════════════════
# 3. HANDLE MISSING VALUES
# ═══════════════════════════════════════════════════
print("\n[Missing Values]")

# hormonal_phase: missing means user didn't enter cycle data
# Fill with "None" (valid category — male users or not entered)
if df["hormonal_phase"].isnull().sum() > 0:
    n = df["hormonal_phase"].isnull().sum()
    df["hormonal_phase"] = df["hormonal_phase"].fillna("None")
    print(f"  hormonal_phase  : {n} NaN -> filled with 'None' (not provided)")

# allergen: missing means user skipped — fill with "None" (no known allergy)
if df["allergen"].isnull().sum() > 0:
    n = df["allergen"].isnull().sum()
    df["allergen"] = df["allergen"].fillna("None")
    print(f"  allergen        : {n} NaN -> filled with 'None' (not provided)")

# breakout_location & product_sensitivity: fill with mode
for col in ["breakout_location", "product_sensitivity"]:
    if df[col].isnull().sum() > 0:
        n = df[col].isnull().sum()
        mode_val = df[col].mode()[0]
        df[col] = df[col].fillna(mode_val)
        print(f"  {col:<22}: {n} NaN -> mode = '{mode_val}'")

print(f"\n  Remaining missing: {df.isnull().sum().sum()}")

# ═══════════════════════════════════════════════════
# 4. ENCODE CATEGORICAL FEATURES
# ═══════════════════════════════════════════════════
CATEGORICAL_COLS = [
    "skin_type",
    "acne_type",
    "acne_severity",
    "breakout_location",
    "product_sensitivity",
    "allergen",
    "skin_concern",
    "humidity",
    "pollution",
    "temperature",
    "age_group",
    "hormonal_phase",
    "recommended_treatment",   # target
]

label_encoders = {}
df_enc = df.copy()

for col in CATEGORICAL_COLS:
    le = LabelEncoder()
    df_enc[col + "_enc"] = le.fit_transform(df[col].astype(str))
    label_encoders[col] = {
        "classes": list(le.classes_),
        "mapping": {str(c): int(i) for i, c in enumerate(le.classes_)}
    }

with open("data/processed/label_encoders.json", "w") as f:
    json.dump(label_encoders, f, indent=2)
print("\n[Encoding] Saved label_encoders.json")
print(f"  Encoded {len(CATEGORICAL_COLS)} categorical columns")

# ═══════════════════════════════════════════════════
# 5. FEATURE MATRIX FOR ML
# ═══════════════════════════════════════════════════
FEATURE_COLS = [
    "skin_type_enc",
    "acne_type_enc",            # from CNN
    "acne_severity_enc",        # from questionnaire Q2
    "breakout_location_enc",    # from questionnaire Q3
    "product_sensitivity_enc",  # from questionnaire Q4
    "allergen_enc",             # from questionnaire Q5
    "skin_concern_enc",         # from questionnaire Q6
    "humidity_enc",             # from API
    "pollution_enc",            # from API
    "temperature_enc",          # from API
    "age_group_enc",            # from Users table
    "hormonal_phase_enc",       # from HormonalCycle.cs
]
TARGET_COL = "recommended_treatment_enc"

X = df_enc[FEATURE_COLS]
y = df_enc[TARGET_COL]

# ═══════════════════════════════════════════════════
# 6. NORMALIZE (MinMaxScaler)
# ═══════════════════════════════════════════════════
scaler = MinMaxScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=FEATURE_COLS)
print(f"\n[Scaling] MinMaxScaler applied to {len(FEATURE_COLS)} features")

# ═══════════════════════════════════════════════════
# 7. SAVE FILES
# ═══════════════════════════════════════════════════
ml_df = X_scaled.copy()
ml_df["target"] = y.values
ml_df.to_csv("data/processed/ml_ready_dataset.csv", index=False)

readable_cols = ["user_id", "age_group", "skin_type", "acne_type",
                 "acne_severity", "breakout_location", "product_sensitivity",
                 "allergen", "skin_concern", "humidity", "pollution",
                 "temperature", "hormonal_phase", "recommended_treatment"]
df[readable_cols].to_csv("data/processed/user_profiles_clean.csv", index=False)

with open("data/processed/feature_cols.json", "w") as f:
    json.dump(FEATURE_COLS, f, indent=2)

print(f"\n[Saved] ml_ready_dataset.csv     : {ml_df.shape}")
print(f"[Saved] user_profiles_clean.csv  : {df[readable_cols].shape}")
print(f"[Saved] feature_cols.json")

# ═══════════════════════════════════════════════════
# 8. EDA CHARTS
# ═══════════════════════════════════════════════════
print("\n[EDA] Generating charts...")

# Chart 1 — Skin Type Distribution
fig, ax = plt.subplots(figsize=(9, 5))
counts = df["skin_type"].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Distribution of Skin Types", fontsize=14, fontweight="bold")
ax.set_xlabel("Skin Type"); ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/01_skin_type_distribution.png", dpi=150)
plt.close()

# Chart 2 — Acne Type Distribution (CNN output classes)
fig, ax = plt.subplots(figsize=(9, 5))
counts = df["acne_type"].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Acne Type Distribution  (CNN Output Classes)", fontsize=14, fontweight="bold")
ax.set_xlabel("Acne Type"); ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/02_acne_type_distribution.png", dpi=150)
plt.close()

# Chart 3 — Acne Severity Distribution
fig, ax = plt.subplots(figsize=(7, 5))
counts = df["acne_severity"].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Acne Severity Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Severity"); ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/03_acne_severity_distribution.png", dpi=150)
plt.close()

# Chart 4 — Recommended Treatment Distribution (TARGET)
fig, ax = plt.subplots(figsize=(12, 5))
counts = df["recommended_treatment"].value_counts()
bars = ax.barh(counts.index, counts.values,
               color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Recommended Treatment Distribution  (Target Variable)",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/04_treatment_distribution.png", dpi=150)
plt.close()

# Chart 5 — Skin Type vs Acne Severity Heatmap
pivot = pd.crosstab(df["skin_type"], df["acne_severity"])
fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd", ax=ax, linewidths=0.5)
ax.set_title("Skin Type vs Acne Severity", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("data/eda_charts/05_skintype_vs_severity.png", dpi=150)
plt.close()

# Chart 6 — Acne Type vs Recommended Treatment Heatmap
pivot2 = pd.crosstab(df["acne_type"], df["recommended_treatment"])
fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(pivot2, annot=True, fmt="d", cmap="Blues", ax=ax,
            linewidths=0.5, cbar_kws={"shrink": 0.8})
ax.set_title("Acne Type vs Recommended Treatment", fontsize=14, fontweight="bold")
plt.xticks(rotation=30, ha="right", fontsize=9)
plt.tight_layout()
plt.savefig("data/eda_charts/06_acnetype_vs_treatment.png", dpi=150)
plt.close()

# Chart 7 — Hormonal Phase Distribution
fig, ax = plt.subplots(figsize=(9, 5))
counts = df["hormonal_phase"].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Hormonal Phase Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Phase"); ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/07_hormonal_phase_distribution.png", dpi=150)
plt.close()

# Chart 8 — Breakout Location Distribution
fig, ax = plt.subplots(figsize=(10, 5))
counts = df["breakout_location"].value_counts()
bars = ax.barh(counts.index, counts.values,
               color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Breakout Location Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/08_breakout_location.png", dpi=150)
plt.close()

# Chart 9 — Allergen Distribution
fig, ax = plt.subplots(figsize=(9, 5))
counts = df["allergen"].value_counts()
bars = ax.bar(counts.index, counts.values,
              color=sns.color_palette(PAL, len(counts)))
ax.bar_label(bars, padding=3, fontsize=10)
ax.set_title("Allergen Distribution", fontsize=14, fontweight="bold")
ax.set_xlabel("Allergen"); ax.set_ylabel("Count")
plt.tight_layout()
plt.savefig("data/eda_charts/09_allergen_distribution.png", dpi=150)
plt.close()

# Chart 10 — Feature Correlation Heatmap
fig, ax = plt.subplots(figsize=(13, 10))
corr = X_scaled.corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="coolwarm",
            ax=ax, linewidths=0.5, vmin=-1, vmax=1,
            cbar_kws={"shrink": 0.8})
ax.set_title("Feature Correlation Heatmap", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("data/eda_charts/10_feature_correlation.png", dpi=150)
plt.close()

print(f"    10 EDA charts saved -> data/eda_charts/")
print("\n" + "=" * 55)
print("  Phase 2 Complete. Files ready:")
print("  data/raw/user_profiles_raw.csv")
print("  data/processed/ml_ready_dataset.csv")
print("  data/processed/user_profiles_clean.csv")
print("  data/processed/label_encoders.json")
print("  data/processed/feature_cols.json")
print("  data/eda_charts/  (10 charts)")
print("=" * 55)
