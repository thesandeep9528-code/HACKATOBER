import os
import joblib
import pandas as pd
import numpy as np

# Format: 'Crop Name': [Nitrogen (N), Phosphorus (P), Potassium (K)]
optimal_nutrient_dict = {
    'Cabbage': [124, 80, 100],
    'pearl_millet': [50, 30, 30],
    'annual_moringa': [101, 50, 50],
    'ash_gourd': [80, 60, 80],
    'beetroot': [79, 50, 50],
    'bengalgram': [50, 30, 30],
    'bhendi': [126, 80, 100],
    'bitter_gourd': [80, 60, 80],
    'blackgram': [30, 30, 30],
    'bottle_gourd': [80, 60, 80],
    'brinjal': [125, 60, 100],
    'capsicum': [124, 60, 100],
    'carrot': [100, 79, 80],
    'castor': [60, 30, 30],
    'cauliflower': [100, 50, 50],
    'chillies': [126, 59, 101],
    'chowchow': [80, 50, 50],
    'cluster_bean': [80, 50, 50],
    'cotton': [100, 50, 50],
    'cowpea': [45, 30, 30],
    'cucumber': [80, 50, 50],
    'elephant_foot_yam': [80, 50, 50],
    'french_bean': [79, 50, 50],
    'gingely': [30, 30, 30],
    'greengram': [30, 30, 30],
    'groundnut': [65, 50, 50],
    'horsegram': [50, 30, 30],
    'jute': [79, 40, 40],
    'kudiraivali': [50, 30, 30],
    'maize': [150, 75, 75],
    'muskmelon': [100, 50, 80],
    'onion': [125, 60, 100],
    'panivaragu': [35, 25, 25],
    'peas': [100, 50, 50],
    'pumpkin': [80, 60, 81],
    'radish': [80, 50, 50],
    'ragi': [35, 25, 25],
    'redgram': [50, 30, 30],
    'ribbed_gourd': [80, 60, 80],
    'rice': [90, 50, 50],
    'samai': [35, 25, 25],
    'small_onion': [80, 50, 50],
    'snake_gourd': [80, 60, 80],
    'sorghum': [70, 50, 50],
    'soyabean': [65, 30, 30],
    'sugarbeet': [125, 70, 70],
    'sugarcane': [175, 80, 135],
    'sunflower': [60, 30, 30],
    'sweet_potato': [100, 50, 50],
    'tapoica': [80, 50, 50],
    'thinai': [35, 25, 25],
    'tinda': [80, 50, 50],
    'tomato': [126, 60, 100],
    'varagu': [35, 25, 25],
    'vegetable_cowpea': [79, 50, 50],
    'watermelon': [99, 50, 80],
    'wheat': [100, 50, 50],
}

optimal_nutrient_dict_lower = {k.lower(): v for k, v in optimal_nutrient_dict.items()}

_cached_model = None

def load_model():
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'crop_app.pkl')
    if not os.path.exists(model_path):
        from utils.train_crop_model import train_and_save_model
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Crop_recommendation_dataset_fixed.csv')
        _cached_model = train_and_save_model(csv_path=csv_path, output_path=model_path)
    else:
        _cached_model = joblib.load(model_path)
    return _cached_model

def get_prediction(n, p, k, ph, temp, humidity, soil_type):
    model = load_model()

    soil_columns = [
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

    soil_vector = [0] * len(soil_columns)
    input_soil_col = f"SOIL_{soil_type}"

    if input_soil_col in soil_columns:
        index = soil_columns.index(input_soil_col)
        soil_vector[index] = 1

    features = [n, p, k, ph, temp, humidity] + soil_vector
    final_columns = ['N', 'P', 'K', 'SOIL_PH', 'TEMP', 'RELATIVE_HUMIDITY'] + soil_columns
    input_df = pd.DataFrame([features], columns=final_columns)

    prediction = model.predict(input_df)
    probabilities = model.predict_proba(input_df)
    match_percentage = round(float(np.max(probabilities)) * 100, 2)
    return str(prediction[0]), match_percentage

def recommend_fertilizer(crop_name, current_n, current_p, current_k):
    crop_name = crop_name.strip().lower()

    if crop_name not in optimal_nutrient_dict_lower:
        return [
            f"Standard optimal NPK for {crop_name.capitalize()}: Maintain balanced N-P-K (100:50:50 kg/ha).",
            "Apply compost/organic matter to improve overall soil texture and fertility."
        ]

    target_n, target_p, target_k = optimal_nutrient_dict_lower[crop_name]
    recommendations = []

    # 1. Nitrogen Check
    if current_n < target_n:
        diff = round(target_n - current_n, 1)
        recommendations.append(f"Nitrogen (N) is LOW by {diff} kg/ha. Recommendation: Apply Urea or Ammonium Sulfate in split doses.")
    elif current_n > target_n:
        recommendations.append(f"Nitrogen (N) is SUFFICIENT/HIGH. Avoid additional nitrogen fertilizer to prevent vegetative excess.")
    else:
        recommendations.append("Nitrogen (N) levels are optimal for this crop.")

    # 2. Phosphorus Check
    if current_p < target_p:
        diff = round(target_p - current_p, 1)
        recommendations.append(f"Phosphorus (P) is LOW by {diff} kg/ha. Recommendation: Apply Single Superphosphate (SSP) or DAP as basal dose.")
    elif current_p > target_p:
        recommendations.append("Phosphorus (P) is SUFFICIENT. No additional phosphorus fertilizer needed.")
    else:
        recommendations.append("Phosphorus (P) levels are optimal.")

    # 3. Potassium Check
    if current_k < target_k:
        diff = round(target_k - current_k, 1)
        recommendations.append(f"Potassium (K) is LOW by {diff} kg/ha. Recommendation: Apply Muriate of Potash (MOP) to boost disease resistance and grain filling.")
    elif current_k > target_k:
        recommendations.append("Potassium (K) is SUFFICIENT. No additional potash needed.")
    else:
        recommendations.append("Potassium (K) levels are optimal.")

    return recommendations