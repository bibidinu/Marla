import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import joblib

def train_ai():
    """Addestra l'AI per il trading e la salva per l'uso nel bot."""
    print("📡 Caricamento del dataset per l'addestramento...")
    data = pd.read_csv("training_data.csv")
    print(f"🔎 Colonne disponibili nel dataset: {list(data.columns)}")

    # ✅ Fix del warning "SettingWithCopyWarning"
    features = ["RSI", "ATR", "MACD", "MACD_Signal", "BB_Upper", "BB_Lower",
                "VWAP", "ADX", "SuperTrend", "EMA_50", "EMA_200", "trend", "MFI", "CCI",
                "Stoch", "WilliamsR"]
    target_col = "target"

    missing_features = [feat for feat in features if feat not in data.columns]
    if missing_features:
        print(f"❌ Errore: Feature mancanti nel dataset: {missing_features}")
        return

    X = data[features].copy()
    y = data[target_col]

    # ✅ Gestione NaN
    X.fillna(X.median(), inplace=True)

    # ✅ Normalizzazione
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ✅ Bilanciamento dati con SMOTE
    smote = SMOTE(sampling_strategy="auto", random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_scaled, y)

    # ✅ Divisione training/testing
    X_train, X_test, y_train, y_test = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)

    # ✅ Ottimizzazione automatica del modello con GridSearchCV
    param_grid = {
        "n_estimators": [300, 500],
        "learning_rate": [0.05, 0.1],
        "max_depth": [6, 8]
    }
    xgb = XGBClassifier()
    grid_search = GridSearchCV(xgb, param_grid, cv=3, scoring="accuracy")
    grid_search.fit(X_train, y_train)
    model = grid_search.best_estimator_

    accuracy = model.score(X_test, y_test) * 100
    print(f"🎯 AI addestrata con successo! Precisione: {accuracy:.2f}%")

    # ✅ Salvataggio modello e scaler
    joblib.dump(model, "ai_model.pkl")
    joblib.dump(scaler, "scaler.pkl")
    print("✅ Modello AI e scaler salvati per il trading!")

if __name__ == "__main__":
    train_ai()
