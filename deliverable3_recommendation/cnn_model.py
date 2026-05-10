import numpy as np
from PIL import Image
import io
import os
import logging

logger = logging.getLogger(__name__)

CLASSES = ["Blackheads", "Cyst", "Papules", "Pustules", "Whiteheads"]
IMG_SIZE = (224, 224)

CNN_TO_DERM_MAP = {
    "Blackheads": "Comedonal",
    "Whiteheads": "Comedonal",
    "Cyst":       "Cystic",
    "Papules":    "Inflammatory",
    "Pustules":   "Inflammatory",
}

SEVERITY_MAP = {
    "Blackheads": {"label": "Mild",     "level": 1, "color": "mild"},
    "Whiteheads": {"label": "Mild",     "level": 1, "color": "mild"},
    "Papules":    {"label": "Moderate", "level": 2, "color": "moderate"},
    "Pustules":   {"label": "Moderate", "level": 2, "color": "moderate"},
    "Cyst":       {"label": "Severe",   "level": 3, "color": "severe"},
}

ACNE_DESCRIPTIONS = {
    "Blackheads": "Open comedones caused by clogged hair follicles. The dark color is from oxidized melanin, not dirt.",
    "Whiteheads": "Closed comedones — small, flesh-colored bumps formed when pores are blocked by dead skin cells and sebum.",
    "Cyst":       "Deep, painful lesions filled with pus. The most severe form of acne, often causing scarring if untreated.",
    "Papules":    "Small, raised, red bumps caused by inflamed or infected hair follicles. Tender to the touch.",
    "Pustules":   "Similar to papules but topped with white or yellow pus. A hallmark of inflammatory acne.",
}


class CNNModel:

    def __init__(self, model_path: str = "models/acne_cnn_model.keras"):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self):
        THIS_DIR    = os.path.dirname(os.path.abspath(__file__))   # .../utils/
        PROJECT_DIR = os.path.dirname(THIS_DIR)                    # .../Deliverable 3/

        def abs_candidates(rel_path):
            
            return [rel_path,
                    os.path.join(PROJECT_DIR, rel_path),
                    os.path.join(THIS_DIR, rel_path)]

        candidates = []
        for rel in [
            self.model_path,
            "models/acne_cnn_model.keras",
            "models/acne_cnn_model.h5",
            "models/phaseB_best.keras",
            "models/skinmeta_efficientnetb0_final.keras",
            "models/skinmeta_cnn.keras",
            "checkpoints/phaseB_best.keras",
            "checkpoints/phaseA_best.keras",
        ]:
            candidates.extend(abs_candidates(rel))

        for path in candidates:
            if os.path.exists(path):
                self.model_path = path
                break
        else:
            logger.warning(
                "No CNN model file found. Running in DEMO mode.\n"
                "To use real predictions, place your trained model at:\n"
                "  models/acne_cnn_model.keras  (or phaseB_best.keras)\n"
                "The model must be an EfficientNetB0 trained with preprocess_input()."
            )
            return

        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path)
            logger.info(f"CNN model loaded from: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load CNN model: {e}")
            self.model = None


    def _preprocess(self, image_bytes: bytes) -> "np.ndarray":
        
        from tensorflow.keras.applications.efficientnet import preprocess_input  # type: ignore

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE, Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)          # [0, 255] float
        arr = preprocess_input(arr)                     # → [-1, 1] range
        return np.expand_dims(arr, axis=0)              # (1, 224, 224, 3)


    def _is_skin_image(self, image_bytes: bytes) -> tuple:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((128, 128), Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)

        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        mean_r = float(r.mean())
        mean_g = float(g.mean())
        mean_b = float(b.mean())
        global_std = float(arr.std())

        if global_std < 15:
            return False, "Image appears to be a solid colour or plain background."

        near_white = (mean_r > 190) and (mean_g > 190) and (mean_b > 190)
        if near_white:
            return False, "Image looks like a document or screenshot. Please upload a skin photo."

        near_black = (mean_r < 20) and (mean_g < 20) and (mean_b < 20)
        if near_black:
            return False, "Image is too dark. Please upload a well-lit photo of your skin."

        white_ratio = float((lum > 200).sum()) / lum.size
        black_ratio = float((lum < 40).sum())  / lum.size
        if white_ratio > 0.40 and black_ratio > 0.05:
            return False, "Image appears to contain text or a document. Please upload a skin photo."

        rg_diff = float(np.abs(r - g).mean())
        rb_diff = float(np.abs(r - b).mean())
        gb_diff = float(np.abs(g - b).mean())
        channel_spread = (rg_diff + rb_diff + gb_diff) / 3.0
        if channel_spread < 6.0:
            return False, "Image appears to be greyscale or a text document. Please upload a colour skin photo."

        blue_dominant  = (mean_b > mean_r + 30) and (mean_b > mean_g + 15)
        green_dominant = (mean_g > mean_r + 30) and (mean_g > mean_b + 15)
        if blue_dominant:
            return False, "Image does not appear to contain skin (strong blue tones detected)."
        if green_dominant:
            return False, "Image does not appear to contain skin (strong green tones detected)."

        r_dom     = (r > g) & (r > b)
        rg_gap    = (r - g) >= 10        # tightened from 8
        rb_gap    = (r - b) >= 10        # tightened from 8
        lum_gate  = (lum > 40) & (lum < 240)   # exclude ink-black & blown-white
        not_grey  = (r - g) > 5          # exclude true-grey pixels
        skin_mask = r_dom & rg_gap & rb_gap & lum_gate & not_grey
        skin_ratio = float(skin_mask.sum()) / skin_mask.size

        if skin_ratio < 0.15:            # raised from 0.08
            return False, (
                "No skin tones detected in this image. "
                "Please upload a clear photo of your face or the affected skin area."
            )

        return True, "ok"


    def _simulate_prediction(self, image_bytes: bytes) -> dict:
       
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img, dtype=np.float32)

        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        lum = 0.299 * r + 0.587 * g + 0.114 * b

        mean_r   = float(r.mean())
        mean_g   = float(g.mean())
        mean_b   = float(b.mean())
        std_lum  = float(lum.std())

        redness      = mean_r - mean_g        
        brightness   = (mean_r + mean_g + mean_b) / 3.0

        bright_ratio = float((lum > 220).sum()) / lum.size   

        scores = np.ones(5)  

        if mean_r <= 70 and mean_g <= 70 and mean_b <= 70 and redness < 25:
            dark_score = (70 - brightness) * 3  
            scores[0] = max(dark_score, 10.0)

    
        if brightness > 170 and redness < 30:
            wh_score = (brightness - 170) * 2 + (30 - redness) * 1.5
            scores[4] = max(wh_score, 10.0)

    
        if mean_r > 140 and redness > 50 and bright_ratio < 0.005:
            pap_score = redness * 2.0
            scores[2] = max(pap_score, 10.0)

       
        if mean_r > 140 and redness > 50 and bright_ratio >= 0.005:
            pus_score = redness * (1 + bright_ratio * 80)
            scores[3] = max(pus_score, 10.0)

        
        if 110 < mean_r < 200 and mean_g < 100 and std_lum > 40:
            cyst_score = redness * std_lum / 40.0
            scores[1] = max(cyst_score, 10.0)

        log_s = np.log(scores)
        exp_s = np.exp(log_s - log_s.max())
        probs = exp_s / exp_s.sum()

        pred_idx = int(np.argmax(scores))

        return {
            "class_idx":   pred_idx,
            "class_name":  CLASSES[pred_idx],
            "probabilities": {cls: float(p) for cls, p in zip(CLASSES, probs)},
            "demo_mode":   True,
        }


    def predict(self, image_bytes: bytes) -> dict:
        
        is_skin, reason = self._is_skin_image(image_bytes)
        if not is_skin:
            raise ValueError(f"NOT_SKIN: {reason}")

        if self.model is None:
            raw = self._simulate_prediction(image_bytes)
        else:
            try:
                arr = self._preprocess(image_bytes)
                raw_probs = self.model.predict(arr, verbose=0)[0]

                temperature = 1.8
                logits = np.log(raw_probs + 1e-8) / temperature

                
                class_weights = np.array([
                    0.60,   # Blackheads — most frequent, penalise
                    1.40,   # Cyst       — rare, boost
                    1.50,   # Papules    — under-represented, boost (was 1.35)
                    0.60,   # Pustules   — frequent, penalise
                    1.60,   # Whiteheads — under-represented, boost (was 1.35)
                ])
                logits = logits * class_weights

                exp_logits = np.exp(logits - logits.max())
                probs = exp_logits / exp_logits.sum()

                pred_idx = int(np.argmax(probs))
                raw = {
                    "class_idx":     pred_idx,
                    "class_name":    CLASSES[pred_idx],
                    "probabilities": {cls: float(p) for cls, p in zip(CLASSES, probs)},
                    "demo_mode":     False,
                }
            except Exception as e:
                logger.error(f"Inference error: {e}. Falling back to demo mode.")
                raw = self._simulate_prediction(image_bytes)

        cls_name   = raw["class_name"]
        sev_info   = SEVERITY_MAP.get(cls_name, {"label": "Moderate", "level": 2, "color": "moderate"})
        derm_type  = CNN_TO_DERM_MAP.get(cls_name, "General")
        confidence = raw["probabilities"][cls_name]

        return {
            "acne_type":      cls_name,
            "acne_class":     cls_name,
            "derm_type":      derm_type,
            "severity":       sev_info["label"],
            "severity_level": sev_info["level"],
            "severity_color": sev_info["color"],
            "confidence":     confidence,
            "probabilities":  raw["probabilities"],
            "description":    ACNE_DESCRIPTIONS.get(cls_name, ""),
            "demo_mode":      raw.get("demo_mode", False),
        }