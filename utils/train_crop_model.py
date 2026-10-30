import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

SOIL_COLUMNS = [
    'SOIL_Alluvial Soil', 'SOIL_Black Cotton Soil', 'SOIL_Black Soil',
    'SOIL_Brown Loamy Soil', 'SOIL_Clay Loamy Soil', 'SOIL_Clay Soil',
    'SOIL_Cotton Soil', 'SOIL_Deep Soil', 'SOIL_Friable Soil',
    'SOIL_Heavy Black Soil', 'SOIL_Heavy Soil', 'SOIL_Laterite Soil',
    'SOIL_Light Loamy Soil', 'SOIL_Light Soil', 'SOIL_Loamy Soil',
    'SOIL_Medium Black Soil', 'SOIL_Red Lateritic Loamy Soil',
    'SOIL_Red Loamy Soil', 'SOIL_Red Soil', 'SOIL_Rich Red Loamy Soil',
    'SOIL_Salty Clay Loamy Soil', 'SOIL_Sandy Clay Loamy Soil',
    'SOIL_Sandy Loamy Soil', 'SOIL_Sandy Soil',
    'SOIL_Shallow Black Soil', 'SOIL_Silty Loamy Soil',
    'SOIL_Well-Drained Loamy Soil', 'SOIL_Well-Drained Soil',
    'SOIL_Well-Grained Deep Loamy Moist Soil'
]

def train_and_save_model(csv_path="Crop_recommendation_dataset_fixed.csv", output_path="crop_app.pkl"):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset {csv_path} not found.")

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Feature extraction matching prediction_model.ipynb
    soil_dummies = pd.get_dummies(df['SOIL'], prefix='SOIL')

    # Ensure all required soil columns are present
    for col in SOIL_COLUMNS:
        if col not in soil_dummies.columns:
            soil_dummies[col] = 0

    soil_dummies = soil_dummies[SOIL_COLUMNS]

    feature_cols = ['N', 'P', 'K', 'SOIL_PH', 'TEMP', 'RELATIVE_HUMIDITY']
    X = pd.concat([df[feature_cols], soil_dummies], axis=1)
    y = df['CROPS']

    print(f"Training RandomForestClassifier on {len(X)} samples with {len(y.unique())} crop classes...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    joblib.dump(clf, output_path)
    print(f"Model saved successfully to {output_path}")
    return clf

if __name__ == "__main__":
    train_and_save_model()
