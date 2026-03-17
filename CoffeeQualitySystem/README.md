## Coffee Quality Prediction System

This project is a Streamlit-based web application for predicting and analyzing coffee quality using a machine learning model, with per-user history, batch predictions, and analytics.

### Features

- **Single prediction**: interactive form for sensory and origin attributes, with charts and recommendations.
- **Batch prediction**: CSV upload, per-row predictions, downloadable results, and error report.
- **Analytics**: dashboards for prediction distribution, confidence trends, altitude vs score, and more.
- **User accounts**: basic authentication with roles and an admin account.

### Requirements

- Python 3.9+ recommended.
- Dependencies are listed in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

### Running the app

From the project root:

```bash
streamlit run app.py
```

The app will open in your browser on a local port (typically `http://localhost:8501`).

### Model files

The application expects a trained model and its components in the `models` directory:

- `models/coffee_quality_model_reloaded.ubj` – XGBoost model (preferred name).
- `models/model_components.pkl` – contains scaler, label encoder, feature columns, and performance metrics.

If these files are missing, you can:

- Use `create_components_manually.py` to generate a minimal `model_components.pkl`.
- Use `extract_components.py` to extract components from an existing pickle model.
- Use `recover_model.py` to generate a temporary fallback model.

### Configuration

Key paths are defined in `config.py`. For deployment, you can override them with environment variables:

- `COFFEE_MODELS_DIR` – custom models directory.
- `COFFEE_DATA_DIR` – base data directory.
- `COFFEE_UPLOAD_DIR` – upload directory.
- `COFFEE_REPORTS_DIR` – reports directory.
- `COFFEE_DATABASE_PATH` – SQLite database file path.

### Authentication

- A default admin user is created on first run:
  - **Username**: `admin`
  - **Password**: `admin123`
- New passwords are stored with bcrypt; older accounts using SHA-256 hashes are still accepted and transparently upgraded.

### Tests

There is currently no dedicated test suite. A good starting point is to add `pytest` tests for:

- `CoffeeModel.engineer_features` and `CoffeeModel.predict` using dummy data.
- `Database` methods such as `create_user`, `authenticate`, and `save_prediction`.

