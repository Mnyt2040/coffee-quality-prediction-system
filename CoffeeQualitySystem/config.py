# config.py
"""
Configuration settings for the Coffee Quality System
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.absolute()

# Allow overrides via environment variables for deployment flexibility
MODELS_DIR = os.getenv("COFFEE_MODELS_DIR", os.path.join(BASE_DIR, "models"))
DATA_DIR = os.getenv("COFFEE_DATA_DIR", os.path.join(BASE_DIR, "data"))
UPLOAD_DIR = os.getenv("COFFEE_UPLOAD_DIR", os.path.join(DATA_DIR, "uploads"))
REPORTS_DIR = os.getenv("COFFEE_REPORTS_DIR", os.path.join(BASE_DIR, "reports"))

# Create directories if they don't exist
for dir_path in [MODELS_DIR, DATA_DIR, UPLOAD_DIR, REPORTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Database configuration
DATABASE_PATH = os.getenv(
    "COFFEE_DATABASE_PATH", os.path.join(BASE_DIR, "coffee_system.db")
)

# Model configuration
MODEL_PATH = os.path.join(MODELS_DIR, "coffee_quality_model_reloaded.ubj")
MODEL_COMPONENTS_PATH = os.path.join(MODELS_DIR, "model_components.pkl")
DEFAULT_MODEL = "coffee_quality_model_reloaded.ubj"

# App configuration
APP_NAME = "Coffee Quality Prediction System"
APP_VERSION = "2.0.0"
APP_ICON = "☕"

# Quality categories
QUALITY_CATEGORIES = {
    'Excellent': (85, 100),
    'Good': (80, 84.99),
    'Average': (75, 79.99),
    'Below Average': (0, 74.99)
}

# SCAA flavor wheel attributes
FLAVOR_ATTRIBUTES = [
    "Aroma",
    "Flavor",
    "Aftertaste",
    "Acidity",
    "Body",
    "Balance",
    "Uniformity",
    "Clean Cup",
    "Sweetness",
    "Overall",
]

# User roles
USER_ROLES = ["admin", "user", "farmer", "viewer"]

# Your model's feature columns (canonical order)
YOUR_MODEL_FEATURES = [
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
    "Overall_Sensory_Score",
    "Balance_Acidity_Ratio",
    "Flavor_Body_Product",
    "Aroma_Aftertaste_Product",
]


def find_model_file() -> str:
    """Find the model file in common locations."""
    possible_paths = [
        MODEL_PATH,
        os.path.join(MODELS_DIR, "coffee_quality_model.pkl"),
        os.path.join(MODELS_DIR, "coffee_quality_model.json"),
        os.path.join(MODELS_DIR, "coffee_quality_model.ubj"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Fallback to default even if missing; caller should check existence
    return MODEL_PATH