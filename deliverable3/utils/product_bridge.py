from __future__ import annotations

import os
import re
import json
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "cleanser", "face wash", "gel cleanser", "foam cleanser", "micellar water",
    "toner", "essence", "serum", "treatment", "spot treatment", "acne treatment",
    "moisturizer", "moisturiser", "face cream", "gel moisturizer", "lotion",
    "sunscreen", "spf", "eye cream", "face mask", "facial oil", "primer",
    "exfoliant", "exfoliator", "retinol", "aha", "bha", "peel",
}

BLOCK_KEYWORDS = {
    "body", "hand", "foot", "hair", "shampoo", "conditioner",
    "bath", "shower", "nail", "lip", "lipstick", "foundation",
    "mascara", "eyeshadow", "blush", "bronzer", "perfume", "fragrance spray",
    "deodorant", "supplement", "vitamin pill", "capsule",
}

FALLBACK_PRODUCTS = [
    {
        "id": "p001", "name": "Foaming Facial Cleanser",
        "brand": "CeraVe", "category": "Cleanser",
        "key_ingredients": ["Ceramide", "Hyaluronic Acid", "Niacinamide"],
        "acne_types": ["Comedonal", "Inflammatory", "General"],
        "skin_types": ["Oily", "Combination", "Normal"],
        "why_recommended": "Removes excess oil without stripping the skin barrier. Contains ceramides for barrier support.",
        "usage": "Use morning and evening. Wet face, apply a small amount, rinse thoroughly.",
        "match_score": 0.88,
    },
    {
        "id": "p002", "name": "Salicylic Acid Cleanser",
        "brand": "Paula's Choice", "category": "Cleanser",
        "key_ingredients": ["Salicylic Acid", "Green Tea Extract"],
        "acne_types": ["Comedonal", "Inflammatory"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "BHA cleanser that penetrates pores to dissolve blackheads and excess sebum.",
        "usage": "Use once daily. Leave on skin 30 seconds before rinsing for deeper cleanse.",
        "match_score": 0.92,
    },
    {
        "id": "p003", "name": "Gentle Skin Cleanser",
        "brand": "Cetaphil", "category": "Cleanser",
        "key_ingredients": ["Panthenol", "Niacinamide", "Glycerin"],
        "acne_types": ["General", "Inflammatory"],
        "skin_types": ["Sensitive", "Dry", "Normal"],
        "why_recommended": "Ultra-gentle formula that cleanses without irritation, ideal for sensitive or reactive skin.",
        "usage": "Use morning and evening. Suitable for daily use.",
        "match_score": 0.85,
    },
    {
        "id": "p004", "name": "Niacinamide 10% + Zinc 1%",
        "brand": "The Ordinary", "category": "Serum",
        "key_ingredients": ["Niacinamide", "Zinc PCA"],
        "acne_types": ["Comedonal", "Inflammatory", "General"],
        "skin_types": ["Oily", "Combination", "Normal"],
        "why_recommended": "High-strength niacinamide regulates sebum, minimizes pores, and fades post-acne marks.",
        "usage": "Apply 2–3 drops morning and/or evening before moisturizer.",
        "match_score": 0.95,
    },
    {
        "id": "p005", "name": "AHA 30% + BHA 2% Peeling Solution",
        "brand": "The Ordinary", "category": "Treatment",
        "key_ingredients": ["Glycolic Acid", "Salicylic Acid", "Lactic Acid"],
        "acne_types": ["Comedonal", "Inflammatory"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "Combined AHA/BHA exfoliant that clears pores, resurfaces texture, and reduces blackheads.",
        "usage": "Use once weekly at night. Leave on 10 minutes, rinse. Avoid sensitive skin.",
        "match_score": 0.87,
    },
    {
        "id": "p006", "name": "Azelaic Acid Suspension 10%",
        "brand": "The Ordinary", "category": "Treatment",
        "key_ingredients": ["Azelaic Acid"],
        "acne_types": ["Inflammatory", "Cystic", "Comedonal"],
        "skin_types": ["All"],
        "why_recommended": "Brightens, reduces redness, fights bacteria, and fades post-acne hyperpigmentation.",
        "usage": "Apply pea-sized amount morning and/or evening. Safe for sensitive skin.",
        "match_score": 0.90,
    },
    {
        "id": "p007", "name": "Benzoyl Peroxide 5% Gel",
        "brand": "Epiduo", "category": "Spot Treatment",
        "key_ingredients": ["Benzoyl Peroxide"],
        "acne_types": ["Inflammatory", "Cystic"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "Kills acne-causing bacteria directly. Effective for inflamed pustules and cysts.",
        "usage": "Apply thin layer to affected areas only. Start 3x/week to assess tolerance.",
        "match_score": 0.88,
    },
    {
        "id": "p008", "name": "Differin Adapalene Gel 0.1%",
        "brand": "Differin", "category": "Treatment",
        "key_ingredients": ["Adapalene"],
        "acne_types": ["Cystic", "Comedonal", "Inflammatory"],
        "skin_types": ["Oily", "Combination", "Normal"],
        "why_recommended": "OTC retinoid that normalizes cell turnover, prevents clogged pores, and treats cystic acne.",
        "usage": "Apply pea-sized amount every night. Expect 8–12 weeks for full results. Use SPF daily.",
        "match_score": 0.93,
    },
    {
        "id": "p009", "name": "PM Facial Moisturizing Lotion",
        "brand": "CeraVe", "category": "Moisturizer",
        "key_ingredients": ["Ceramide", "Hyaluronic Acid", "Niacinamide"],
        "acne_types": ["General", "Inflammatory", "Cystic"],
        "skin_types": ["All"],
        "why_recommended": "Non-comedogenic barrier repair moisturizer with ceramides and hyaluronic acid.",
        "usage": "Apply every night after treatments.",
        "match_score": 0.86,
    },
    {
        "id": "p010", "name": "Oil-Free Moisturizer with SPF 35",
        "brand": "Neutrogena", "category": "Moisturizer",
        "key_ingredients": ["Zinc Oxide", "Hyaluronic Acid"],
        "acne_types": ["General", "Comedonal"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "Lightweight, oil-free formula with built-in SPF protection. Non-comedogenic.",
        "usage": "Apply every morning as the last skincare step.",
        "match_score": 0.84,
    },
    {
        "id": "p011", "name": "Ultra Facial Moisturizer",
        "brand": "Kiehl's", "category": "Moisturizer",
        "key_ingredients": ["Squalane", "Glacial Glycoprotein", "Vitamin E"],
        "acne_types": ["General"],
        "skin_types": ["Dry", "Sensitive", "Normal"],
        "why_recommended": "Lightweight, long-lasting hydration ideal for dry or dehydrated acne-prone skin.",
        "usage": "Apply morning and evening to clean skin.",
        "match_score": 0.80,
    },
    {
        "id": "p012", "name": "Ultra Light Daily UV Defense SPF 50",
        "brand": "Kiehl's", "category": "Sunscreen",
        "key_ingredients": ["Zinc Oxide", "Vitamin E", "Vitamin C"],
        "acne_types": ["General", "Inflammatory"],
        "skin_types": ["All"],
        "why_recommended": "Essential daily SPF to prevent UV darkening of acne marks. Lightweight, non-greasy.",
        "usage": "Apply as last AM step. Reapply every 2 hours outdoors.",
        "match_score": 0.87,
    },
    {
        "id": "p013", "name": "Invisible Fluid SPF 50+",
        "brand": "La Roche-Posay", "category": "Sunscreen",
        "key_ingredients": ["Mexoryl SX", "Mexoryl XL", "Tinosorb S"],
        "acne_types": ["General", "Comedonal"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "Ultra-fluid, matte-finish sunscreen that won't clog pores. Perfect for acne-prone skin.",
        "usage": "Apply generously every morning. Last step in AM routine.",
        "match_score": 0.91,
    },
    {
        "id": "p014", "name": "Skin Perfecting 2% BHA Liquid Exfoliant",
        "brand": "Paula's Choice", "category": "Toner",
        "key_ingredients": ["Salicylic Acid", "Green Tea"],
        "acne_types": ["Comedonal", "Inflammatory"],
        "skin_types": ["Oily", "Combination"],
        "why_recommended": "Leave-on BHA toner that exfoliates inside pores, reducing blackheads and breakouts.",
        "usage": "Apply with cotton pad or fingertips after cleansing. Use once daily to start.",
        "match_score": 0.89,
    },
    {
        "id": "p015", "name": "Pore Tightening Toner",
        "brand": "Pyunkang Yul", "category": "Toner",
        "key_ingredients": ["Centella Asiatica", "Witch Hazel", "Niacinamide"],
        "acne_types": ["General", "Inflammatory"],
        "skin_types": ["All"],
        "why_recommended": "Balances skin pH, minimizes pores, and calms post-acne redness.",
        "usage": "Apply after cleansing with cotton pad or press into skin with hands.",
        "match_score": 0.82,
    },
    {
        "id": "p016", "name": "Retinol 0.2% in Squalane",
        "brand": "The Ordinary", "category": "Treatment",
        "key_ingredients": ["Retinol", "Squalane"],
        "acne_types": ["Cystic", "Comedonal", "General"],
        "skin_types": ["Normal", "Dry", "Combination"],
        "why_recommended": "Entry-level retinol to boost cell turnover, prevent breakouts, and smooth skin texture.",
        "usage": "Apply every 3rd night initially, building to nightly use. Always follow with SPF next morning.",
        "match_score": 0.85,
    },
    {
        "id": "p017", "name": "Centella Cica Cream",
        "brand": "Dr. Jart+", "category": "Moisturizer",
        "key_ingredients": ["Centella Asiatica", "Ceramide", "Panthenol"],
        "acne_types": ["Inflammatory", "General"],
        "skin_types": ["Sensitive", "Dry", "All"],
        "why_recommended": "Centella-rich formula repairs damaged skin barrier, soothes redness and post-acne irritation.",
        "usage": "Apply morning and/or night as moisturizing layer.",
        "match_score": 0.83,
    },
    {
        "id": "p018", "name": "Vitamin C Serum 15%",
        "brand": "SkinCeuticals", "category": "Serum",
        "key_ingredients": ["Ascorbic Acid", "Ferulic Acid", "Vitamin E"],
        "acne_types": ["General", "Inflammatory"],
        "skin_types": ["Normal", "Combination", "Oily"],
        "why_recommended": "Antioxidant serum that fades dark spots and post-acne hyperpigmentation in the morning routine.",
        "usage": "Apply 4–5 drops every morning before SPF. Avoid with benzoyl peroxide.",
        "match_score": 0.79,
    },
]

INGREDIENT_PRODUCT_MAP = {
    "salicylic acid":   ["p002", "p005", "p014"],
    "niacinamide":      ["p004", "p001", "p015"],
    "benzoyl peroxide": ["p007"],
    "azelaic acid":     ["p006"],
    "glycolic acid":    ["p005"],
    "adapalene":        ["p008"],
    "retinol":          ["p016"],
    "zinc pca":         ["p004"],
    "ceramide":         ["p001", "p009", "p017"],
    "hyaluronic acid":  ["p009", "p010", "p001"],
    "centella asiatica":["p015", "p017"],
    "panthenol":        ["p003", "p017"],
    "tea tree":         ["p014"],
    "vitamin c":        ["p018"],
    "zinc gluconate":   ["p004"],
}


def _is_facial_product(row: dict) -> bool:
    cat = str(row.get("category", "")).lower()
    name = str(row.get("name", "")).lower()
    combined = cat + " " + name

    for block in BLOCK_KEYWORDS:
        if block in combined:
            return False

    for valid in VALID_CATEGORIES:
        if valid in combined:
            return True

    return True


def _score_product(product: dict, rec_ingredients: list[str]) -> float:
    prod_ings = [i.lower() for i in product.get("key_ingredients", [])]
    if not rec_ingredients or not prod_ings:
        return product.get("match_score", 0.70)

    overlap = sum(
        1 for ri in rec_ingredients
        if any(ri.lower() in pi or pi in ri.lower() for pi in prod_ings)
    )
    
    if overlap == 0:
        return product.get("match_score", 0.65)
    
    ingredient_score = overlap / max(len(rec_ingredients), 1)
    base_score = product.get("match_score", 0.75)
    return round(min(base_score * 0.4 + ingredient_score * 0.6, 1.0), 3)


class ProductBridge:
    def __init__(self):
        self._products: list[dict] = []
        self._tfidf = None
        self._product_matrix = None
        self._try_load_csv()
        self._try_load_tfidf()

    def _try_load_csv(self):
        """Try to load acne_products_tagged.csv from common locations."""
        candidates = [
            "acne_products_tagged.csv",
            "data/acne_products_tagged.csv",
            "data/products.csv",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    self._products = self._df_to_products(df)
                    logger.info(f"Loaded {len(self._products)} products from {path}")
                    return
                except Exception as e:
                    logger.warning(f"Could not parse {path}: {e}")
        logger.info("No product CSV found — using built-in fallback catalogue.")
        self._products = FALLBACK_PRODUCTS

    def _try_load_tfidf(self):
        """Try to load tfidf_product_bridge.pkl for ML-based similarity."""
        candidates = [
            "tfidf_product_bridge.pkl",
            "models/tfidf_product_bridge.pkl",
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as f:
                        self._tfidf = pickle.load(f)
                    # Rebuild product matrix
                    texts = [self._product_text(p) for p in self._products]
                    self._product_matrix = self._tfidf.transform(texts)
                    logger.info(f"TF-IDF bridge loaded from {path}")
                    return
                except Exception as e:
                    logger.warning(f"TF-IDF load failed: {e}")

    def _df_to_products(self, df: pd.DataFrame) -> list[dict]:

        def _parse_list(val):
            if isinstance(val, list):
                return val
            if pd.isna(val) or str(val).strip() in ("", "[]"):
                return []
            try:
                return json.loads(str(val).replace("'", '"'))
            except Exception:
                cleaned = re.sub(r"[\[\]'\"]", "", str(val))
                return [x.strip() for x in cleaned.split(",") if x.strip()]

        name_col = next((c for c in df.columns if c.lower() in
                         ("product_name", "name", "title")), df.columns[0])
        brand_col = next((c for c in df.columns if "brand" in c.lower()), None)
        type_col = next((c for c in df.columns if any(
            k in c.lower() for k in ("type", "category", "label"))), None)
        ing_col = next((c for c in df.columns if "ing" in c.lower()), None)
        acne_col = next((c for c in df.columns if "acne_type" in c.lower()), None)

        products = []
        for _, row in df.iterrows():
            key_ings = _parse_list(row.get("acne_ings_present", row.get(ing_col, [])))
            acne_types = _parse_list(row.get("acne_types", row.get(acne_col, ["General"])))
            cat = str(row.get(type_col, "Treatment")) if type_col else "Treatment"
            prod = {
                "id": str(row.name),
                "name": str(row.get(name_col, "Unknown Product")),
                "brand": str(row.get(brand_col, "Unknown Brand")) if brand_col else "Unknown Brand",
                "category": cat,
                "key_ingredients": key_ings,
                "acne_types": acne_types,
                "skin_types": ["All"],
                "why_recommended": f"Contains {', '.join(key_ings[:3])} for {', '.join(acne_types[:2])} acne.",
                "usage": "Apply as directed on packaging.",
                "match_score": 0.75,
            }
            if _is_facial_product(prod):
                products.append(prod)

        return products if products else FALLBACK_PRODUCTS


    @staticmethod
    def _product_text(product: dict) -> str:
        parts = [
            product.get("name", ""),
            product.get("brand", ""),
            product.get("category", ""),
            " ".join(product.get("key_ingredients", [])),
            " ".join(product.get("acne_types", [])),
        ]
        return " ".join(filter(None, parts)).lower()

    # ── Core: Get Products ────────────────────────────────────────────────────

    def get_products(
        self,
        formula: str,
        acne_type: str = "General",
        skin_type: str = "Normal",
        top_n: int = 9,
    ) -> list[dict]:

        rec_ingredients = self._parse_formula(formula)

        if self._tfidf is not None and self._product_matrix is not None:
            candidates = self._tfidf_rank(rec_ingredients, top_n=top_n * 4)
        else:
            candidates = list(self._products)

        candidates = [p for p in candidates if _is_facial_product(p)]

        derm_type = self._cnn_to_derm(acne_type)
        scored = []
        for prod in candidates:
            score = _score_product(prod, rec_ingredients)

            # Boost products that match acne type
            prod_acne = [t.lower() for t in prod.get("acne_types", [])]
            if derm_type.lower() in prod_acne or acne_type.lower() in prod_acne:
                score = min(score + 0.10, 1.0)

            # Boost products that match skin type
            prod_skin = [s.lower() for s in prod.get("skin_types", [])]
            if skin_type.lower() in prod_skin or "all" in prod_skin:
                score = min(score + 0.05, 1.0)

            prod_copy = dict(prod)
            prod_copy["match_score"] = round(score, 3)
            scored.append(prod_copy)

        scored.sort(key=lambda x: -x["match_score"])
        
        category_counts = {}
        category_max = max(2, top_n // 5)  # Allow up to ~2 products per category
        seen_names = set()
        results = []
        
        for p in scored:
            key = p["name"].lower().strip()
            if key in seen_names:
                continue
                
            category = p.get("category", "Treatment").lower()
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Allow multiple products from high-relevance categories, but diversify
            if category_counts[category] <= category_max:
                seen_names.add(key)
                results.append(p)
            
            if len(results) >= top_n:
                break

        if not results:
            results = self._ingredient_fallback(rec_ingredients, top_n)

        return results

    # ── TF-IDF Ranking ────────────────────────────────────────────────────────

    def _tfidf_rank(self, rec_ingredients: list[str], top_n: int) -> list[dict]:
        """Use TF-IDF cosine similarity to pre-rank products."""
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            query = self._tfidf.transform([" ".join(rec_ingredients)])
            sims = cosine_similarity(query, self._product_matrix).flatten()
            top_idx = np.argsort(sims)[::-1][:top_n]
            return [self._products[i] for i in top_idx if i < len(self._products)]
        except Exception as e:
            logger.warning(f"TF-IDF ranking failed: {e}")
            return list(self._products)


    @staticmethod
    def _parse_formula(formula: str) -> list[str]:
        """Parse '+' separated formula string to lowercase ingredient list."""
        parts = re.split(r"\s*\+\s*", formula)
        cleaned = []
        for p in parts:
            p = re.sub(r"\(.*?\)", "", p).strip().lower()
            p = re.sub(r"[^a-z0-9 ]", "", p).strip()
            if p:
                cleaned.append(p)
        return cleaned

    @staticmethod
    def _cnn_to_derm(acne_type: str) -> str:
        mapping = {
            "Blackheads": "Comedonal",
            "Whiteheads": "Comedonal",
            "Papules": "Inflammatory",
            "Pustules": "Inflammatory",
            "Cyst": "Cystic",
        }
        return mapping.get(acne_type, "General")

    def _ingredient_fallback(self, rec_ingredients: list[str], top_n: int) -> list[dict]:
        product_ids: list[str] = []
        for ing in rec_ingredients:
            for key, ids in INGREDIENT_PRODUCT_MAP.items():
                if key in ing or ing in key:
                    product_ids.extend(ids)

        seen = set()
        ordered_ids = []
        for pid in product_ids:
            if pid not in seen:
                seen.add(pid)
                ordered_ids.append(pid)

        id_to_product = {p["id"]: p for p in FALLBACK_PRODUCTS if "id" in p}
        results = [id_to_product[pid] for pid in ordered_ids if pid in id_to_product]

        if len(results) < top_n:
            extras = [p for p in FALLBACK_PRODUCTS if p not in results]
            results.extend(extras[:top_n - len(results)])

        return results[:top_n]