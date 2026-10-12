"""Loads the trained models once at startup and runs the two-stage prediction."""
import joblib

from app.config import BINARY_MODEL_PATH, ATTACK_MODEL_PATH, LABEL_ENCODER_PATH


class ModelBundle:
    def __init__(self):
        self.binary = joblib.load(BINARY_MODEL_PATH)
        self.attack = joblib.load(ATTACK_MODEL_PATH)
        self.encoder = joblib.load(LABEL_ENCODER_PATH)

    def predict(self, features):
        """Return (is_malicious: bool, attack_type: str | None)."""
        is_malicious = int(self.binary.predict(features)[0]) == 1
        if not is_malicious:
            return False, None
        code = self.attack.predict(features)[0]
        return True, str(self.encoder.inverse_transform([code])[0])
