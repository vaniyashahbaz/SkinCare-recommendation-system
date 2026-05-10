from __future__ import annotations
import pickle
import os
import logging
import re

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DERM_KB = {
    "Comedonal": {
        "mild":     {"primary": ["Salicylic Acid", "Zinc PCA", "Niacinamide"],
                     "support": ["Hyaluronic Acid", "Aloe Vera"]},
        "moderate": {"primary": ["Salicylic Acid", "Niacinamide", "Glycolic Acid"],
                     "support": ["Zinc PCA", "Centella Asiatica"]},
        "severe":   {"primary": ["Salicylic Acid", "Glycolic Acid", "Azelaic Acid"],
                     "support": ["Niacinamide", "Ceramide"]},
    },
    "Inflammatory": {
        "mild":     {"primary": ["Niacinamide", "Azelaic Acid", "Tea Tree"],
                     "support": ["Zinc Gluconate", "Centella Asiatica"]},
        "moderate": {"primary": ["Benzoyl Peroxide", "Niacinamide", "Azelaic Acid"],
                     "support": ["Zinc PCA", "Panthenol"]},
        "severe":   {"primary": ["Benzoyl Peroxide", "Azelaic Acid", "Niacinamide"],
                     "support": ["Ceramide", "Centella Asiatica"]},
    },
    "Cystic": {
        "mild":     {"primary": ["Benzoyl Peroxide", "Niacinamide", "Azelaic Acid"],
                     "support": ["Zinc PCA", "Hyaluronic Acid"]},
        "moderate": {"primary": ["Benzoyl Peroxide", "Adapalene", "Azelaic Acid"],
                     "support": ["Niacinamide", "Ceramide"]},
        "severe":   {"primary": ["Adapalene", "Benzoyl Peroxide", "Azelaic Acid"],
                     "support": ["Ceramide", "Panthenol"]},
    },
    "General": {
        "mild":     {"primary": ["Niacinamide", "Hyaluronic Acid", "Ceramide"],
                     "support": ["Centella Asiatica", "Panthenol"]},
        "moderate": {"primary": ["Niacinamide", "Salicylic Acid", "Azelaic Acid"],
                     "support": ["Ceramide", "Hyaluronic Acid"]},
        "severe":   {"primary": ["Azelaic Acid", "Niacinamide", "Salicylic Acid"],
                     "support": ["Ceramide", "Centella Asiatica"]},
    },
}

CNN_TO_DERM = {
    "Blackheads": "Comedonal",
    "Whiteheads": "Comedonal",
    "Papules":    "Inflammatory",
    "Pustules":   "Inflammatory",
    "Cyst":       "Cystic",
}

DEFAULT_CONCENTRATIONS = {
    "salicylic acid":    {1: "0.5%", 2: "1%",    3: "2%"},
    "benzoyl peroxide":  {1: "2.5%", 2: "5%",    3: "10%"},
    "niacinamide":       {1: "5%",   2: "10%",   3: "10%"},
    "azelaic acid":      {1: "10%",  2: "15%",   3: "20%"},
    "glycolic acid":     {1: "5%",   2: "8%",    3: "10%"},
    "adapalene":         {1: "0.1%", 2: "0.1%",  3: "0.3%"},
    "zinc pca":          {1: "1%",   2: "2%",    3: "2%"},
    "hyaluronic acid":   {1: "1%",   2: "1%",    3: "2%"},
}

INGREDIENT_BENEFITS = {
    "Salicylic Acid":    "BHA exfoliant — unclogs pores and reduces blackheads",
    "Niacinamide":       "Reduces oil production, fades dark spots, strengthens skin barrier",
    "Benzoyl Peroxide":  "Kills acne-causing bacteria; reduces pustules and cysts",
    "Azelaic Acid":      "Anti-inflammatory; reduces redness and post-acne marks",
    "Glycolic Acid":     "AHA exfoliant — smooths texture and opens clogged pores",
    "Adapalene":         "Retinoid that normalizes skin cell turnover; prevents cysts",
    "Tea Tree":          "Natural antibacterial; calms inflamed blemishes",
    "Zinc PCA":          "Regulates sebum production; antibacterial properties",
    "Zinc Gluconate":    "Anti-inflammatory mineral that reduces acne activity",
    "Hyaluronic Acid":   "Deep hydration without clogging pores",
    "Ceramide":          "Repairs skin barrier; prevents moisture loss",
    "Centella Asiatica": "Soothes inflammation and accelerates healing",
    "Panthenol":         "Calms irritated skin; lightweight barrier support",
    "Aloe Vera":         "Soothing and anti-inflammatory for reactive skin",
}

PROFILE_ADJUSTMENTS = {
    "Sensitive": {
        "remove": ["Benzoyl Peroxide", "Glycolic Acid"],
        "add":    ["Ceramide", "Centella Asiatica", "Panthenol"],
        "reason": "Sensitive skin — harsh actives replaced with barrier-repair ingredients",
    },
    "Dry": {
        "remove": ["Salicylic Acid", "Glycolic Acid"],
        "add":    ["Hyaluronic Acid", "Ceramide"],
        "reason": "Dry skin — exfoliating acids replaced with hydration ingredients",
    },
    "Oily": {
        "remove": [],
        "add":    ["Zinc PCA", "Niacinamide"],
        "reason": "Oily skin — added sebum regulators",
    },
    "Combination": {
        "remove": [],
        "add":    ["Niacinamide", "Hyaluronic Acid"],
        "reason": "Combination skin — balancing actives added",
    },
    "Normal": {
        "remove": [],
        "add":    [],
        "reason": "Normal skin — standard formulation maintained",
    },
}

AM_PM_ROUTINE = {
    "am": [
        {"step": 1, "name": "Gentle Cleanser",    "description": "Remove overnight buildup without stripping skin",     "actives": []},
        {"step": 2, "name": "Toner / Essence",    "description": "Balance pH and prep skin for active ingredients",      "actives": ["Niacinamide"]},
        {"step": 3, "name": "Treatment Serum",    "description": "Target acne-causing bacteria and excess oil",          "actives": ["Salicylic Acid", "Azelaic Acid"]},
        {"step": 4, "name": "Lightweight Moisturizer", "description": "Hydrate and support the skin barrier",           "actives": ["Hyaluronic Acid", "Ceramide"]},
        {"step": 5, "name": "Broad-Spectrum SPF", "description": "Prevent UV darkening of acne marks · essential daily", "actives": []},
    ],
    "pm": [
        {"step": 1, "name": "Oil Cleanser (optional)", "description": "Remove sunscreen and pollutants",                "actives": []},
        {"step": 2, "name": "Gel / Foam Cleanser",    "description": "Second cleanse for fresh skin",                   "actives": []},
        {"step": 3, "name": "Active Treatment",       "description": "Apply prescription or OTC acne treatment",        "actives": ["Benzoyl Peroxide", "Adapalene"]},
        {"step": 4, "name": "Repair Moisturizer",     "description": "Richer barrier repair cream for overnight healing", "actives": ["Ceramide", "Panthenol"]},
    ],
    "notes": [
        "Always apply SPF 30+ every morning — UV exposure worsens post-acne marks.",
        "Introduce active ingredients one at a time to avoid irritation.",
        "Wait 15–20 minutes between active layers on sensitive nights.",
    ],
}


class RecommendationEngine:
    def __init__(self):
        self._try_load_ml_model()

    def _try_load_ml_model(self):
        self.ml_model = None
        paths = [
            "models/recommendation_model.pkl",
            "recommendation_model.pkl",
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, "rb") as f:
                        self.ml_model = pickle.load(f)
                    logger.info(f"Recommendation ML model loaded from {p}")
                    return
                except Exception as e:
                    logger.warning(f"Could not load rec model: {e}")
        logger.info("No ML recommendation model found — using dermatology knowledge base.")

    def _severity_label(self, level: int) -> str:
        return {1: "mild", 2: "moderate", 3: "severe"}.get(level, "moderate")

    def _get_concentration(self, ingredient: str, severity: int) -> str | None:
        key = ingredient.lower()
        return DEFAULT_CONCENTRATIONS.get(key, {}).get(min(severity, 3))

    def recommend(self, acne_type: str, severity: int, skin_profile: dict) -> dict:
        derm_type  = CNN_TO_DERM.get(acne_type, "General")
        sev_label  = self._severity_label(severity)
        skin_type  = skin_profile.get("skin_type", "Normal")
        sensitivity = skin_profile.get("sensitivity", "Low")

        kb = DERM_KB.get(derm_type, DERM_KB["General"]).get(sev_label, {})
        primary = list(kb.get("primary", []))
        support = list(kb.get("support", []))

        adjustments = []

        adj = PROFILE_ADJUSTMENTS.get(skin_type, PROFILE_ADJUSTMENTS["Normal"])
        for r in adj["remove"]:
            if r in primary:
                primary.remove(r)
                adjustments.append(f"Removed {r} — {adj['reason']}")
            if r in support:
                support.remove(r)

        for a in adj["add"]:
            if a not in primary and a not in support:
                support.append(a)
                if adj["reason"] and a == adj["add"][0]:
                    adjustments.append(f"Added {a} — {adj['reason']}")

        if sensitivity == "High":
            for ing in ["Benzoyl Peroxide", "Glycolic Acid"]:
                if ing in primary:
                    primary.remove(ing)
                    adjustments.append(f"Sensitivity: Removed {ing} for high-sensitivity skin")

        all_ings = primary + support[:2]

        formula_parts = []
        for ing in all_ings:
            conc = self._get_concentration(ing, severity)
            formula_parts.append({"name": ing, "concentration": conc or "",
                                   "benefit": INGREDIENT_BENEFITS.get(ing, "")})

        formula = " + ".join(
            f"{p['name']}({p['concentration']})" if p["concentration"] else p["name"]
            for p in formula_parts
        )

        ingredients_by_category = {
            "Primary Actives": [p for p in formula_parts if p["name"] in primary],
            "Support Actives": [p for p in formula_parts if p["name"] in support[:2]],
        }

        explanation = self._generate_explanation(derm_type, sev_label, acne_type, primary[:2], skin_type)

        return {
            "derm_type":   derm_type,
            "severity_label": sev_label,
            "formula":     formula,
            "formula_parts": formula_parts,
            "all_ingredients": all_ings,
            "ingredients_by_category": ingredients_by_category,
            "adjustments": adjustments,
            "routine":     AM_PM_ROUTINE,
            "explanation": explanation,
        }

    def _generate_explanation(self, derm_type: str, severity: str, acne_type: str, 
                               primary_ings: list[str], skin_type: str) -> str:
        acne_desc = {
            "Comedonal": "comedones (blackheads & whiteheads)",
            "Inflammatory": "inflammatory breakouts (papules & pustules)",
            "Cystic": "severe cystic acne",
            "General": "general acne",
        }
        
        severity_desc = {
            "mild": "mild",
            "moderate": "moderate",
            "severe": "severe",
        }
        
        acne_name = acne_desc.get(derm_type, "acne")
        sev_name = severity_desc.get(severity, "moderate")
        
        ing_reasons = []
        for ing in primary_ings[:2]:
            ing_reason = INGREDIENT_BENEFITS.get(ing, "")
            if ing_reason:
                ing_reasons.append(f"<strong>{ing}</strong> — {ing_reason}")
        
        ing_text = "; ".join(ing_reasons) if ing_reasons else "targeted acne actives"
        
        return f"Based on your {sev_name} {acne_name}, we recommend {ing_text}. Your {skin_type} skin profile helps us filter for compatible products."