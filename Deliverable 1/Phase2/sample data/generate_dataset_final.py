
import pandas as pd
import numpy as np
import random
import os

random.seed(42)
np.random.seed(42)

os.makedirs("data/raw", exist_ok=True)


ACNE_TYPES = ["Blackheads", "Cyst", "Papules", "Pustules", "Whiteheads"]

ACNE_TYPE_WEIGHTS = [0.30, 0.20, 0.22, 0.20, 0.08]

SKIN_TYPES = ["Oily", "Dry", "Combination", "Sensitive", "Normal"]

ACNE_SEVERITIES = ["Mild", "Moderate", "Severe"]

BREAKOUT_LOCATIONS = [
    "T-Zone (forehead/nose)",
    "Cheeks and jawline",
    "All over face",
    "Jawline and chin"      
]

PRODUCT_SENSITIVITIES = [
    "Often reacts",
    "Sometimes reacts",
    "Rarely reacts"
]

ALLERGENS = ["Fragrance", "Alcohol", "Sulfates", "Parabens", "None"]

SKIN_CONCERNS = [
    "Acne and breakouts",
    "Oily/Shiny skin",
    "Dryness or flakiness",
    "Dark spots/Uneven tone",
    "Large pores",
    "Anti-aging"
]

HUMIDITY_LEVELS    = ["Low", "Medium", "High"]
POLLUTION_LEVELS   = ["Low", "Medium", "High"]
TEMPERATURES       = ["Cold", "Moderate", "Hot"]

AGE_GROUPS = ["13-17", "18-24", "25-34", "35-44", "45+"]

HORMONAL_PHASES = ["Menstrual", "Follicular", "Ovulation", "Luteal", "None"]
HORMONAL_WEIGHTS = [0.15, 0.25, 0.10, 0.25, 0.25]  # None = ~25% (male/not entered)

# ─────────────────────────────────────────
# RECOMMENDATION LABELS
# Maps to your existing ProdCategories:
# Cleanser, Moisturizer, Serum, Sunscreen, Toner
# Plus treatment type for ingredient recommendation
# ─────────────────────────────────────────

TREATMENT_LABELS = [
    "Salicylic Acid Cleanser",      # oily + blackheads/papules
    "Benzoyl Peroxide Treatment",   # cystic / severe
    "BHA Exfoliant",                # blackheads + combination
    "Gentle Hydrating Cleanser",    # dry / sensitive
    "Niacinamide Serum",            # hormonal / oily
    "Soothing Cleanser",            # sensitive / allergic
    "Retinoid Treatment",           # moderate-severe / aging concern
    "Oil Control Moisturizer",      # oily / high humidity
]

# ─────────────────────────────────────────
# DERMATOLOGY RULE ENGINE
# Based on clinical dermatology guidelines
# Model will LEARN these patterns from data
# ─────────────────────────────────────────

def assign_treatment(row):
    skin      = row["skin_type"]
    acne      = row["acne_type"]
    severity  = row["acne_severity"]
    location  = row["breakout_location"]
    allergy   = row["allergen"]
    concern   = row["skin_concern"]
    humidity  = row["humidity"]
    hormonal  = row["hormonal_phase"]
    sensitive = row["product_sensitivity"]

    # Cystic or severe → strongest treatments
    if acne == "Cyst" or severity == "Severe":
        if sensitive == "Often reacts" or allergy != "None":
            return "Retinoid Treatment"
        return "Benzoyl Peroxide Treatment"

    # Sensitive skin or strong product reaction → soothing
    if skin == "Sensitive" or sensitive == "Often reacts":
        return "Soothing Cleanser"

    # Hormonal signal: jawline/chin location + hormonal phase
    if location == "Jawline and chin" or hormonal in ["Luteal", "Menstrual"]:
        return "Niacinamide Serum"

    # Oily + blackheads/whiteheads → BHA
    if skin == "Oily" and acne in ["Blackheads", "Whiteheads"]:
        return "BHA Exfoliant"

    # Oily + papules/pustules → Salicylic Acid
    if skin == "Oily" and acne in ["Papules", "Pustules"]:
        return "Salicylic Acid Cleanser"

    # Dry skin → hydrating
    if skin == "Dry":
        return "Gentle Hydrating Cleanser"

    # Combination + blackheads → BHA
    if skin == "Combination" and acne == "Blackheads":
        return "BHA Exfoliant"

    # High humidity + oily/combination → oil control
    if humidity == "High" and skin in ["Oily", "Combination"]:
        return "Oil Control Moisturizer"

    # Aging concern + moderate acne → retinoid
    if concern == "Anti-aging" and severity == "Moderate":
        return "Retinoid Treatment"

    # Moderate papules/pustules → salicylic acid
    if severity == "Moderate" and acne in ["Papules", "Pustules"]:
        return "Salicylic Acid Cleanser"

    # Default
    return "Gentle Hydrating Cleanser"


# ─────────────────────────────────────────
# GENERATE REALISTIC SEVERITY
# Based on acne type (clinical reality)
# ─────────────────────────────────────────

def get_severity(acne_type):
    if acne_type == "Blackheads":
        return random.choices(["Mild", "Moderate", "Severe"], weights=[0.6, 0.35, 0.05])[0]
    elif acne_type == "Whiteheads":
        return random.choices(["Mild", "Moderate", "Severe"], weights=[0.55, 0.38, 0.07])[0]
    elif acne_type == "Papules":
        return random.choices(["Mild", "Moderate", "Severe"], weights=[0.35, 0.45, 0.20])[0]
    elif acne_type == "Pustules":
        return random.choices(["Mild", "Moderate", "Severe"], weights=[0.30, 0.45, 0.25])[0]
    elif acne_type == "Cyst":
        return random.choices(["Mild", "Moderate", "Severe"], weights=[0.10, 0.40, 0.50])[0]
    return "Mild"


# ─────────────────────────────────────────
# GENERATE RECORDS
# ─────────────────────────────────────────

def generate_dataset(n=1500):
    records = []
    for i in range(n):
        acne_type   = random.choices(ACNE_TYPES, weights=ACNE_TYPE_WEIGHTS)[0]
        severity    = get_severity(acne_type)
        horm_phase  = random.choices(HORMONAL_PHASES, weights=HORMONAL_WEIGHTS)[0]

        row = {
            "user_id":              f"U{i+1:04d}",
            "age_group":            random.choice(AGE_GROUPS),

            # From questionnaire
            "skin_type":            random.choice(SKIN_TYPES),
            "acne_severity":        severity,
            "breakout_location":    random.choice(BREAKOUT_LOCATIONS),
            "product_sensitivity":  random.choice(PRODUCT_SENSITIVITIES),
            "allergen":             random.choice(ALLERGENS),
            "skin_concern":         random.choice(SKIN_CONCERNS),

            # From CNN image detection
            "acne_type":            acne_type,

            # From OpenWeatherMap API
            "humidity":             random.choice(HUMIDITY_LEVELS),
            "pollution":            random.choice(POLLUTION_LEVELS),
            "temperature":          random.choice(TEMPERATURES),

            # From HormonalCycle.cs
            "hormonal_phase":       horm_phase,
        }

        row["recommended_treatment"] = assign_treatment(row)
        records.append(row)

    return pd.DataFrame(records)


def introduce_noise(df, missing_rate=0.04):
    """
    Add realistic missing values and duplicates.
    - hormonal_phase and allergen most likely to be missing
      (user skips cycle entry or has no known allergies)
    """
    df_noisy = df.copy()

    # These are most realistically missing
    nullable_cols = {
        "hormonal_phase":     0.10,   # 10% - many users won't enter cycle data
        "allergen":           0.05,   # 5%  - some users unsure
        "breakout_location":  0.03,   # 3%  - occasional skip
        "product_sensitivity":0.03,   # 3%  - occasional skip
    }

    for col, rate in nullable_cols.items():
        mask = np.random.random(len(df_noisy)) < rate
        df_noisy.loc[mask, col] = np.nan

    # ~2% duplicate rows (simulates re-submissions)
    n_dups = int(len(df_noisy) * 0.02)
    dups = df_noisy.sample(n=n_dups, random_state=7)
    df_noisy = pd.concat([df_noisy, dups], ignore_index=True)
    df_noisy = df_noisy.sample(frac=1, random_state=42).reset_index(drop=True)

    return df_noisy


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  SkinMeta Dataset Generator (Final Version)")
    print("=" * 55)

    print("\n[1] Generating 1500 user records...")
    df_clean = generate_dataset(1500)
    df_noisy = introduce_noise(df_clean)

    df_noisy.to_csv("data/raw/user_profiles_raw.csv", index=False)
    print(f"    Saved: data/raw/user_profiles_raw.csv ({len(df_noisy)} rows)")

    print("\n[2] Feature Summary:")
    print(f"    Total features  : 12")
    print(f"    From questionnaire : skin_type, acne_severity, breakout_location,")
    print(f"                         product_sensitivity, allergen, skin_concern")
    print(f"    From CNN           : acne_type")
    print(f"    From API           : humidity, pollution, temperature")
    print(f"    From DB            : age_group, hormonal_phase")

    print("\n[3] Label Distribution (recommended_treatment):")
    print(df_clean["recommended_treatment"].value_counts().to_string())

    print("\n[4] Acne Type Distribution (CNN output simulation):")
    print(df_clean["acne_type"].value_counts().to_string())

    print("\n[5] Missing values introduced (raw file):")
    print(df_noisy.isnull().sum()[df_noisy.isnull().sum() > 0].to_string())

    print("\n[6] Duplicates introduced:", df_noisy.duplicated().sum())
    print("\n✓ Dataset generation complete!")
