from __future__ import annotations
import logging
import re

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {
    "cleanser", "face wash", "gel cleanser", "foam cleanser", "micellar water",
    "micellar", "cleansing", "facial cleanser", "facial wash",
    "toner", "essence", "serum", "facial serum",
    "treatment", "spot treatment", "acne treatment", "acne cream",
    "moisturizer", "moisturiser", "face cream", "facial cream",
    "gel moisturizer", "lotion", "facial lotion", "face lotion",
    "sunscreen", "spf", "sun protection", "sunblock",
    "eye cream", "eye serum",
    "face mask", "sheet mask", "clay mask", "peel mask",
    "facial oil", "face oil",
    "exfoliant", "exfoliator", "chemical exfoliant",
    "retinol", "retinoid", "aha", "bha",
    "peel", "resurfacing",
    "primer",  # skin prep primer (not makeup in context)
}

BLOCK_KEYWORDS = [
    "body lotion", "body cream", "body wash", "body scrub", "body butter",
    "body oil", "body spray", "body gel", "body milk",
    "hand cream", "hand lotion", "hand wash", "hand sanitizer",
    "foot cream", "foot lotion", "foot scrub", "foot spray",
    "hair", "shampoo", "conditioner", "hair mask", "hair oil",
    "hair serum", "scalp", "dry shampoo",
    "lip balm", "lip gloss", "lipstick", "lip liner", "lip mask",
    "foundation", "bb cream", "cc cream", "mascara",
    "eyeshadow", "eyeliner", "blush", "bronzer", "highlighter",
    "concealer", "powder", "setting spray",
    "perfume", "fragrance", "cologne", "body mist",
    "deodorant", "antiperspirant",
    "supplement", "vitamin pill", "capsule", "tablet",
    "nail", "cuticle",
    "wax", "hair removal", "depilatory",
    "beard", "shaving", "aftershave",
    "bubble bath", "bath bomb", "bath salt", "bath oil",
    "intimate", "feminine wash",
    "baby", "infant",
    "toothpaste", "mouthwash",
    "sunscreen body", "body sunscreen",  # distinguish from face SPF
]

SKIN_TYPE_CONFLICTS = {
    "sensitive": {
        "avoid": [
            "benzoyl peroxide", "glycolic acid", "lactic acid",
            "physical scrub", "alcohol denat", "fragrance", "parfum",
            "essential oils", "menthol", "eucalyptus",
        ],
        "prefer": ["ceramide", "centella", "panthenol", "hyaluronic acid", "niacinamide"],
        "note":   "Sensitive skin — strong actives and fragrance removed.",
    },
    "dry": {
        "avoid": ["salicylic acid", "alcohol denat", "benzoyl peroxide"],
        "prefer": ["ceramide", "hyaluronic acid", "squalane", "glycerin"],
        "note":   "Dry skin — astringents and drying actives removed.",
    },
    "oily": {
        "avoid": ["heavy oils", "shea butter", "coconut oil", "petrolatum", "mineral oil"],
        "prefer": ["salicylic acid", "niacinamide", "zinc pca"],
        "note":   "Oily skin — heavy occlusives removed.",
    },
    "combination": {
        "avoid": [],
        "prefer": ["niacinamide", "hyaluronic acid"],
        "note":   "Combination skin — balanced formulation.",
    },
    "normal": {
        "avoid": [],
        "prefer": [],
        "note":   "Normal skin — no restrictions.",
    },
}

SENSITIVITY_CONFLICTS = {
    "high": {
        "avoid": [
            "benzoyl peroxide", "glycolic acid", "lactic acid",
            "alcohol denat", "fragrance", "parfum", "retinol",
            "adapalene", "salicylic acid", "mandelic acid",
        ],
        "note": "High sensitivity — most actives removed. Barrier-support only.",
    },
    "moderate": {
        "avoid": ["high-strength benzoyl peroxide", "strong acids"],
        "note": "Moderate sensitivity — high-strength actives reduced.",
    },
    "low": {
        "avoid": [],
        "note": "Low sensitivity — no additional restrictions.",
    },
}


def _contains_blocked_keyword(text: str) -> bool:
    text_lower = text.lower()
    for kw in BLOCK_KEYWORDS:
        # Match whole words/phrases to avoid false positives
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text_lower):
            return True
    return False


def _is_facial_product(product: dict) -> bool:
    name     = str(product.get("name", "")).lower()
    brand    = str(product.get("brand", "")).lower()
    category = str(product.get("category", "")).lower()
    combined = f"{name} {category}"

    if _contains_blocked_keyword(combined):
        logger.debug(f"BLOCKED (keyword): {product.get('name')}")
        return False

    for valid in VALID_CATEGORIES:
        if valid in category or valid in name:
            return True

    if not category or category in ("nan", "none", "unknown", ""):
        return True

    logger.debug(f"BLOCKED (category mismatch): {product.get('name')} | cat={category}")
    return False


def _ingredient_conflict(product: dict, avoid_list: list[str]) -> bool:
    prod_ings = " ".join(str(i).lower() for i in product.get("key_ingredients", []))
    for avoid in avoid_list:
        if avoid.lower() in prod_ings:
            return True
    return False


class ProductFilter:

    def filter(
        self,
        products: list[dict],
        profile: dict,
        max_per_category: int = 3,
    ) -> list[dict]:
        skin_type   = profile.get("skin_type", "Normal").lower()
        sensitivity = profile.get("sensitivity", "Low").lower()

        avoid = list(SKIN_TYPE_CONFLICTS.get(skin_type, {}).get("avoid", []))
        avoid += SENSITIVITY_CONFLICTS.get(sensitivity, {}).get("avoid", [])
        avoid = list(set(avoid))

        passed = []
        rejected_log = []

        for prod in products:
            if not _is_facial_product(prod):
                rejected_log.append(f"Non-facial: {prod.get('name', '?')}")
                continue

            if avoid and _ingredient_conflict(prod, avoid):
                rejected_log.append(f"Ingredient conflict: {prod.get('name', '?')}")
                continue

            passed.append(prod)

        if rejected_log:
            logger.info(f"Filtered out {len(rejected_log)} products: {rejected_log[:5]}")

        filtered = self._cap_per_category(passed, max_per_category)

        if not filtered and passed:
            filtered = passed[:9]
        elif not filtered:
            filtered = self._safe_fallback(skin_type)

        return filtered

    @staticmethod
    def _cap_per_category(products: list[dict], max_n: int) -> list[dict]:
        """Keep up to max_n products per category."""
        counts: dict[str, int] = {}
        result = []
        for p in products:
            cat = str(p.get("category", "General")).lower().strip()
            counts[cat] = counts.get(cat, 0) + 1
            if counts[cat] <= max_n:
                result.append(p)
        return result

    @staticmethod
    def _safe_fallback(skin_type: str) -> list[dict]:
        base = [
            {
                "id": "fallback_1",
                "name": "Gentle Hydrating Cleanser",
                "brand": "CeraVe",
                "category": "Cleanser",
                "key_ingredients": ["Ceramide", "Hyaluronic Acid"],
                "acne_types": ["General"],
                "skin_types": ["All"],
                "why_recommended": "Gentle barrier-safe cleanser suitable for all skin types.",
                "usage": "Use morning and evening.",
                "match_score": 0.80,
            },
            {
                "id": "fallback_2",
                "name": "Niacinamide 10% + Zinc 1%",
                "brand": "The Ordinary",
                "category": "Serum",
                "key_ingredients": ["Niacinamide", "Zinc PCA"],
                "acne_types": ["General", "Inflammatory", "Comedonal"],
                "skin_types": ["All"],
                "why_recommended": "Sebum control and pore minimizing. Well-tolerated by all skin types.",
                "usage": "Apply morning and/or evening.",
                "match_score": 0.85,
            },
        ]
        return base


def validate_product(product: dict) -> tuple[bool, str]:
    """
    Validate a single product.
    Returns (is_valid, reason).
    """
    if not _is_facial_product(product):
        cat = product.get("category", "unknown")
        return False, f"Not a facial product (category: {cat})"
    return True, "OK"