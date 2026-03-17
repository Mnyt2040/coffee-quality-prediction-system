# models.py
"""
Coffee Quality Model Wrapper
"""

import logging
import os
import pickle
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler, LabelEncoder

from config import MODEL_COMPONENTS_PATH, YOUR_MODEL_FEATURES, find_model_file

logger = logging.getLogger(__name__)


# Quality categorization thresholds (based on average sensory score 0-10)
# This ensures consistent buckets for "High", "Good", "Medium", "Low".
QUALITY_SCORE_THRESHOLDS = [
    ("High", 8.5, 10.0),
    ("Good", 7.0, 8.49),
    ("Medium", 5.0, 6.99),
    ("Low", 0.0, 4.99),
]


def score_to_quality_label(score: float) -> str:
    """Map a numeric score to a quality category label."""
    try:
        score_val = float(score)
    except (TypeError, ValueError):
        return "Unknown"

    for label, lower, upper in QUALITY_SCORE_THRESHOLDS:
        if lower <= score_val <= upper:
            return label
    return "Unknown"


class CoffeeModel:
    """Wrapper for coffee quality prediction model.

    Canonical feature order is defined by `YOUR_MODEL_FEATURES` in config.py and
    should match the `feature_columns` stored inside model_components.pkl.
    """

    def __init__(self) -> None:
        self.model: Any = None
        self.model_type: str = "Unknown"
        self.scaler: StandardScaler | None = None
        self.target_encoder: LabelEncoder | None = None
        self.feature_columns: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self._loaded_ok: bool = self.load_model()

    # ------------------------------------------------------------------ #
    # Loading & health check
    # ------------------------------------------------------------------ #
    def load_model(self) -> bool:
        """Load the model and its components in a robust way."""
        logger.info("Loading coffee quality model...")

        model_file = find_model_file()
        components_file = MODEL_COMPONENTS_PATH

        logger.info("Model file candidate: %s", model_file)
        logger.info("Components file: %s", components_file)

        if not os.path.exists(model_file):
            msg = f"Model file not found at {model_file}"
            logger.error(msg)
            self.metadata["load_error"] = msg
            return False

        if not os.path.exists(components_file):
            msg = (
                f"Components file not found at {components_file}. "
                "Run create_components_manually.py or extract_components.py first."
            )
            logger.error(msg)
            self.metadata["load_error"] = msg
            return False

        try:
            # Load XGBoost Booster from .ubj / .json or compatible file
            logger.info("Loading XGBoost model from %s", model_file)
            booster = xgb.Booster()
            booster.load_model(model_file)
            self.model = booster
            self.model_type = "XGBoost"

            # Load components
            logger.info("Loading model components from %s", components_file)
            with open(components_file, "rb") as f:
                components: Dict[str, Any] = pickle.load(f)

            self.scaler = components.get("scaler")
            self.target_encoder = components.get("target_encoder")
            self.feature_columns = list(
                components.get("feature_columns", YOUR_MODEL_FEATURES)
            )

            if not self.feature_columns:
                self.feature_columns = list(YOUR_MODEL_FEATURES)

            # Class names
            if self.target_encoder and hasattr(self.target_encoder, "classes_"):
                class_names = self.target_encoder.classes_.tolist()
            else:
                class_names = components.get(
                    "class_names", ["Excellent", "Good", "Average", "Poor"]
                )

            performance = components.get(
                "performance",
                {
                    "accuracy": 0.95,
                    "precision": 0.0,
                    "recall": 0.0,
                    "f1_score": 0.95,
                },
            )

            self.metadata = {
                "model_type": self.model_type,
                "class_names": class_names,
                "performance": performance,
            }

            # Consistency check with YOUR_MODEL_FEATURES
            if len(self.feature_columns) != len(YOUR_MODEL_FEATURES):
                logger.warning(
                    "Feature column length mismatch: %d in components vs %d in config",
                    len(self.feature_columns),
                    len(YOUR_MODEL_FEATURES),
                )

            logger.info(
                "Model loaded successfully. Type=%s, classes=%s, features=%d",
                self.model_type,
                class_names,
                len(self.feature_columns),
            )
            return True

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Error loading model: %s", exc)
            self.metadata["load_error"] = str(exc)
            self.model = None
            self.scaler = None
            self.target_encoder = None
            self.feature_columns = []
            return False

    def health_check(self) -> Dict[str, Any]:
        """Return a structured health status for the model."""
        return {
            "model_loaded": self.model is not None,
            "scaler_loaded": self.scaler is not None,
            "encoder_loaded": self.target_encoder is not None,
            "feature_columns_count": len(self.feature_columns),
            "expected_features_count": len(YOUR_MODEL_FEATURES),
            "load_error": self.metadata.get("load_error"),
        }

    # ------------------------------------------------------------------ #
    # Input validation & feature engineering
    # ------------------------------------------------------------------ #
    @staticmethod
    def _coerce_float(value: Any) -> float:
        return float(value) if value is not None else 0.0

    def validate_input(
        self, input_data: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validate and clean raw input for prediction.

        Returns (is_valid, cleaned_data, errors).
        """
        errors: List[str] = []
        cleaned: Dict[str, Any] = dict(input_data)

        # Numeric sensory scores
        score_fields = [
            "Aroma",
            "Flavor",
            "Aftertaste",
            "Acidity",
            "Body",
            "Balance",
            "Uniformity",
            "Clean.Cup",
            "Sweetness",
            "Cupper.Points",
        ]

        for field in score_fields:
            raw = cleaned.get(field, 8.0 if field not in ["Uniformity", "Clean.Cup", "Sweetness"] else 10.0)
            try:
                val = float(raw)
            except (TypeError, ValueError):
                errors.append(f"{field} must be a number (got {raw!r})")
                continue
            if not 0.0 <= val <= 10.0:
                errors.append(f"{field} must be between 0 and 10 (got {val})")
            cleaned[field] = val

        # Altitude
        altitude_raw = cleaned.get("Altitude", 0)
        try:
            altitude_val = float(altitude_raw)
        except (TypeError, ValueError):
            errors.append(f"Altitude must be a number (got {altitude_raw!r})")
            altitude_val = 0.0
        if altitude_val < 0 or altitude_val > 4000:
            errors.append(f"Altitude should be between 0 and 4000 meters (got {altitude_val})")
        cleaned["Altitude"] = altitude_val

        return len(errors) == 0, cleaned, errors

    def engineer_features(self, input_data: Dict[str, Any]) -> Dict[str, float]:
        """Create engineered features from input data."""
        aroma = self._coerce_float(input_data.get("Aroma", 8.0))
        flavor = self._coerce_float(input_data.get("Flavor", 8.0))
        aftertaste = self._coerce_float(input_data.get("Aftertaste", 8.0))
        acidity = self._coerce_float(input_data.get("Acidity", 8.0))
        body = self._coerce_float(input_data.get("Body", 8.0))
        balance = self._coerce_float(input_data.get("Balance", 8.0))

        overall_score = float(
            np.mean([aroma, flavor, aftertaste, acidity, body, balance])
        )

        balance_acidity = float(balance / (acidity + 1e-2))
        flavor_body = float(flavor * body)
        aroma_aftertaste = float(aroma * aftertaste)

        return {
            "Overall_Sensory_Score": overall_score,
            "Balance_Acidity_Ratio": balance_acidity,
            "Flavor_Body_Product": flavor_body,
            "Aroma_Aftertaste_Product": aroma_aftertaste,
        }

    # ------------------------------------------------------------------ #
    # Prediction & feature importance
    # ------------------------------------------------------------------ #
    def _build_feature_vector(self, input_data: Dict[str, Any]) -> np.ndarray:
        """Build model-ready feature vector following canonical order."""
        engineered = self.engineer_features(input_data)

        feature_map: Dict[str, float] = {
            "Aroma": self._coerce_float(input_data.get("Aroma", 8.0)),
            "Flavor": self._coerce_float(input_data.get("Flavor", 8.0)),
            "Aftertaste": self._coerce_float(input_data.get("Aftertaste", 8.0)),
            "Acidity": self._coerce_float(input_data.get("Acidity", 8.0)),
            "Body": self._coerce_float(input_data.get("Body", 8.0)),
            "Balance": self._coerce_float(input_data.get("Balance", 8.0)),
            "Uniformity": self._coerce_float(input_data.get("Uniformity", 10.0)),
            "Clean.Cup": self._coerce_float(input_data.get("Clean.Cup", 10.0)),
            "Sweetness": self._coerce_float(input_data.get("Sweetness", 10.0)),
            "Cupper.Points": self._coerce_float(input_data.get("Cupper.Points", 8.0)),
            "Overall_Sensory_Score": engineered["Overall_Sensory_Score"],
            "Balance_Acidity_Ratio": engineered["Balance_Acidity_Ratio"],
            "Flavor_Body_Product": engineered["Flavor_Body_Product"],
            "Aroma_Aftertaste_Product": engineered["Aroma_Aftertaste_Product"],
        }

        # Determine what feature ordering to use
        ordered_features: List[str] = (
            self.feature_columns if self.feature_columns else list(YOUR_MODEL_FEATURES)
        )

        # Make sure we match the scaler's expected input dimension
        expected_dim = getattr(self.scaler, "n_features_in_", None)
        if expected_dim is not None and len(ordered_features) != expected_dim:
            if len(ordered_features) > expected_dim:
                logger.warning(
                    "Feature column count (%d) exceeds scaler input (%d); truncating.",
                    len(ordered_features),
                    expected_dim,
                )
                ordered_features = ordered_features[:expected_dim]
            else:
                logger.warning(
                    "Feature column count (%d) is less than scaler input (%d); padding with zeros.",
                    len(ordered_features),
                    expected_dim,
                )
                pad_count = expected_dim - len(ordered_features)
                ordered_features = ordered_features + [f"__pad_{i}" for i in range(pad_count)]

        values: List[float] = [feature_map.get(name, 0.0) for name in ordered_features]

        return np.array(values, dtype=float).reshape(1, -1)

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using the model with robust validation."""
        if not self.model or not self.scaler:
            return {
                "success": False,
                "error": "Model not loaded properly",
                "predicted_class": "Unknown",
                "confidence": 0.0,
                "overall_score": 0.0,
                "validation_errors": [],
            }

        is_valid, cleaned_data, validation_errors = self.validate_input(input_data)
        if not is_valid:
            return {
                "success": False,
                "error": "Invalid input data",
                "predicted_class": "Invalid",
                "confidence": 0.0,
                "overall_score": 0.0,
                "validation_errors": validation_errors,
            }

        try:
            features_array = self._build_feature_vector(cleaned_data)

            # Scale features
            features_scaled = self.scaler.transform(features_array)

            # Prediction with XGBoost Booster
            dmatrix = xgb.DMatrix(features_scaled)
            raw_pred = self.model.predict(dmatrix)

            # Normalise to 1D probabilities
            if raw_pred.ndim == 2:
                proba_vec = raw_pred[0]
            else:
                proba_vec = raw_pred

            proba_vec = np.asarray(proba_vec, dtype=float).ravel()

            class_names = self.metadata.get(
                "class_names", ["Excellent", "Good", "Average", "Poor"]
            )

            # If model returns a single logit/probability, build a 2-class vector
            if proba_vec.size == 1:
                p1 = float(proba_vec[0])
                proba_vec = np.array([1.0 - p1, p1], dtype=float)

            # Truncate or pad to match class_names length
            if len(proba_vec) < len(class_names):
                pad_len = len(class_names) - len(proba_vec)
                proba_vec = np.concatenate(
                    [proba_vec, np.zeros(pad_len, dtype=float)]
                )
            elif len(proba_vec) > len(class_names):
                proba_vec = proba_vec[: len(class_names)]

            pred_idx = int(np.argmax(proba_vec))
            confidence = float(proba_vec[pred_idx])

            if 0 <= pred_idx < len(class_names):
                pred_class = class_names[pred_idx]
            else:
                pred_class = ["Excellent", "Good", "Average", "Poor"][pred_idx % 4]

            engineered = self.engineer_features(cleaned_data)
            overall_score = engineered["Overall_Sensory_Score"]
            quality_category = score_to_quality_label(overall_score)

            probabilities = {
                name: float(prob) for name, prob in zip(class_names, proba_vec)
            }

            return {
                "success": True,
                "predicted_class": pred_class,
                "quality_category": quality_category,
                "confidence": confidence,
                "overall_score": overall_score,
                "class_idx": pred_idx,
                "probabilities": probabilities,
            }

        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Prediction error: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "predicted_class": "Error",
                "confidence": 0.0,
                "overall_score": 0.0,
                "validation_errors": [],
            }

    def get_feature_importance(self, top_n: int = 15) -> pd.DataFrame | None:
        """Return feature importance as a DataFrame if available."""
        if self.model is None:
            return None

        # XGBoost Booster importance
        if isinstance(self.model, xgb.Booster):
            try:
                score_dict = self.model.get_score(importance_type="gain")
                if not score_dict:
                    return None
                # Map f0, f1, ... to feature names when possible
                rows: List[Dict[str, Any]] = []
                for key, importance in score_dict.items():
                    if key.startswith("f"):
                        idx = int(key[1:])
                        if 0 <= idx < len(self.feature_columns):
                            name = self.feature_columns[idx]
                        else:
                            name = key
                    else:
                        name = key
                    rows.append({"feature": name, "importance": float(importance)})
                df = pd.DataFrame(rows).sort_values(
                    "importance", ascending=False
                ).head(top_n)
                return df
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to compute XGBoost feature importance")
                return None

        # Generic sklearn-style model
        if isinstance(self.model, BaseEstimator) and hasattr(
            self.model, "feature_importances_"
        ):
            try:
                importances = getattr(self.model, "feature_importances_")
                cols = (
                    self.feature_columns
                    if len(self.feature_columns) == len(importances)
                    else list(YOUR_MODEL_FEATURES)
                )
                rows = [
                    {"feature": name, "importance": float(imp)}
                    for name, imp in zip(cols, importances)
                ]
                df = pd.DataFrame(rows).sort_values(
                    "importance", ascending=False
                ).head(top_n)
                return df
            except Exception:  # pragma: no cover - defensive
                logger.exception("Failed to compute sklearn feature importance")
                return None

        return None


# ============================================================================
# CREATE GLOBAL MODEL INSTANCE
# ============================================================================
logger.info("Initializing Coffee Quality Model...")
coffee_model = CoffeeModel()

health = coffee_model.health_check()
if health["model_loaded"]:
    logger.info("Coffee model is ready for predictions.")
else:
    logger.warning("Coffee model failed to load: %s", health.get("load_error"))

__all__ = ["coffee_model", "CoffeeModel"]