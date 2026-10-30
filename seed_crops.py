from app import app, db
from models import CropStandard

# Source: Crop Tracking Knowledge Base
# Contains all 57 crops classified by TNAU/ICAR standards.

def seed_database():
    crops_data = [
        # --- CEREALS ---
        {
            "name": "rice",
            "display_name": "Rice (Paddy)",
            "category": "Cereal",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 50.0, "avg_yield_unit_weight_g": 3.0,
                "total_duration_days": [115, 135],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Wet"},
                    "stage_2": {"label": "Flowering", "days_start": 46, "days_end": 85, "moisture": "Wet"},
                    "stage_3": {"label": "Maturity", "days_start": 86, "days_end": 135, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 90}
            }
        },
        {
            "name": "wheat",
            "display_name": "Wheat",
            "category": "Cereal",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 44.0, "avg_yield_unit_weight_g": 2.5,
                "total_duration_days": [100, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 71, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 55, "12": 85}
            }
        },
        {
            "name": "maize",
            "display_name": "Maize (Corn)",
            "category": "Cereal",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 6.6, "avg_yield_unit_weight_g": 250.0,
                "total_duration_days": [100, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Tasseling", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 120, "12": 180}
            }
        },

        # --- MILLETS ---
        {
            "name": "sorghum",
            "display_name": "Sorghum (Cholam)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 14.8, "avg_yield_unit_weight_g": 40.0,
                "total_duration_days": [100, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 90, "12": 200}
            }
        },
        {
            "name": "pearl_millet",
            "display_name": "Pearl Millet (Cumbu)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 14.8, "avg_yield_unit_weight_g": 30.0,
                "total_duration_days": [85, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 35, "8": 120, "12": 160}
            }
        },
        {
            "name": "ragi",
            "display_name": "Finger Millet (Ragi)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 66.0, "avg_yield_unit_weight_g": 15.0,
                "total_duration_days": [105, 120],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 80, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 81, "days_end": 120, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 50, "12": 80}
            }
        },
        {
            "name": "panivaragu",
            "display_name": "Proso Millet (Panivaragu)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 40.0, "avg_yield_unit_weight_g": 5.0,
                "total_duration_days": [65, 75],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 25, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 26, "days_end": 50, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 51, "days_end": 75, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 70}
            }
        },
        {
            "name": "samai",
            "display_name": "Little Millet (Samai)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 40.0, "avg_yield_unit_weight_g": 5.0,
                "total_duration_days": [75, 85],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 61, "days_end": 85, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 70, "12": 90}
            }
        },
        {
            "name": "thinai",
            "display_name": "Foxtail Millet (Thinai)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 45.0, "avg_yield_unit_weight_g": 8.0,
                "total_duration_days": [85, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 80, "12": 100}
            }
        },
        {
            "name": "varagu",
            "display_name": "Kodo Millet (Varagu)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 22.0, "avg_yield_unit_weight_g": 6.0,
                "total_duration_days": [110, 120],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 80, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 81, "days_end": 120, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 55, "12": 80}
            }
        },
        {
            "name": "kudiraivali",
            "display_name": "Barnyard Millet (Kudiraivali)",
            "category": "Millet",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 40.0, "avg_yield_unit_weight_g": 6.0,
                "total_duration_days": [90, 95],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 71, "days_end": 95, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 75, "12": 100}
            }
        },

        # --- PULSES ---
        {
            "name": "blackgram",
            "display_name": "Blackgram (Urad)",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.5,
                "total_duration_days": [65, 75],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 25, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 26, "days_end": 50, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 51, "days_end": 75, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 40, "12": 45}
            }
        },
        {
            "name": "greengram",
            "display_name": "Greengram (Moong)",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.0,
                "total_duration_days": [62, 70],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 25, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 26, "days_end": 50, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 51, "days_end": 70, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 45, "12": 55}
            }
        },
        {
            "name": "cowpea",
            "display_name": "Cowpea",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 14.8, "avg_yield_unit_weight_g": 5.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 71, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 60, "12": 80}
            }
        },
        {
            "name": "bengalgram",
            "display_name": "Bengalgram (Chickpea)",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.0,
                "total_duration_days": [90, 105],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 105, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 45, "12": 60}
            }
        },
        {
            "name": "horsegram",
            "display_name": "Horsegram (Kollu)",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.0,
                "total_duration_days": [100, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 75, "moisture": "Dry"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 15, "8": 35, "12": 40}
            }
        },
        {
            "name": "redgram",
            "display_name": "Redgram (Pigeonpea)",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 3.7, "avg_yield_unit_weight_g": 2.5,
                "total_duration_days": [170, 180],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 60, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 61, "days_end": 120, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 121, "days_end": 180, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 70, "12": 110}
            }
        },
        {
            "name": "soyabean",
            "display_name": "Soyabean",
            "category": "Pulse",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.5,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 50, "12": 65}
            }
        },

        # --- OILSEEDS ---
        {
            "name": "groundnut",
            "display_name": "Groundnut",
            "category": "Oilseed",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 33.0, "avg_yield_unit_weight_g": 1.0,
                "total_duration_days": [105, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Pegging", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 76, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 35, "12": 40}
            }
        },
        {
            "name": "sunflower",
            "display_name": "Sunflower",
            "category": "Oilseed",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 5.5, "avg_yield_unit_weight_g": 40.0,
                "total_duration_days": [85, 95],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 65, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 66, "days_end": 95, "moisture": "Dry"}
                },
                "height_milestones": {"4": 35, "8": 110, "12": 140}
            }
        },
        {
            "name": "gingely",
            "display_name": "Gingelly (Sesame)",
            "category": "Oilseed",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 11.0, "avg_yield_unit_weight_g": 0.5,
                "total_duration_days": [80, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 70, "12": 90}
            }
        },
        {
            "name": "castor",
            "display_name": "Castor",
            "category": "Oilseed",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.8, "avg_yield_unit_weight_g": 20.0,
                "total_duration_days": [150, 170],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 46, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 101, "days_end": 170, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 80, "12": 150}
            }
        },

        # --- FIBRE & SUGAR ---
        {
            "name": "cotton",
            "display_name": "Cotton",
            "category": "Fibre",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 3.7, "avg_yield_unit_weight_g": 4.5,
                "total_duration_days": [140, 160],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering/Boll", "days_start": 46, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 101, "days_end": 160, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 100}
            }
        },
        {
            "name": "jute",
            "display_name": "Jute",
            "category": "Fibre",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 80.0, "avg_yield_unit_weight_g": 50.0,
                "total_duration_days": [120, 130],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Wet"},
                    "stage_2": {"label": "Growth", "days_start": 41, "days_end": 90, "moisture": "Wet"},
                    "stage_3": {"label": "Harvest", "days_start": 91, "days_end": 130, "moisture": "Moist"}
                },
                "height_milestones": {"4": 40, "8": 120, "12": 250}
            }
        },
        {
            "name": "sugarcane",
            "display_name": "Sugarcane",
            "category": "Sugar",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 8.0, "avg_yield_unit_weight_g": 1200.0,
                "total_duration_days": [330, 360],
                "stages": {
                    "stage_1": {"label": "Formative", "days_start": 0, "days_end": 90, "moisture": "Moist"},
                    "stage_2": {"label": "Grand Growth", "days_start": 91, "days_end": 270, "moisture": "Wet"},
                    "stage_3": {"label": "Maturity", "days_start": 271, "days_end": 360, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 70, "12": 120}
            }
        },
        {
            "name": "sugarbeet",
            "display_name": "Sugarbeet",
            "category": "Sugar",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 10.0, "avg_yield_unit_weight_g": 800.0,
                "total_duration_days": [150, 160],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Root Dev", "days_start": 46, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 101, "days_end": 160, "moisture": "Moist"}
                },
                "height_milestones": {"4": 15, "8": 30, "12": 40}
            }
        },

        # --- VEGETABLES ---
        {
            "name": "tomato",
            "display_name": "Tomato",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 3.7, "avg_yield_unit_weight_g": 70.0,
                "total_duration_days": [135, 145],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 46, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 101, "days_end": 145, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 90}
            }
        },
        {
            "name": "onion",
            "display_name": "Onion (Bellary)",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 40.0, "avg_yield_unit_weight_g": 70.0,
                "total_duration_days": [90, 110],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Bulbing", "days_start": 46, "days_end": 80, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 81, "days_end": 110, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 45, "12": 50}
            }
        },
        {
            "name": "chillies",
            "display_name": "Chillies",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 3.7, "avg_yield_unit_weight_g": 3.0,
                "total_duration_days": [180, 210],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 150, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 151, "days_end": 210, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 45, "12": 70}
            }
        },
        {
            "name": "Cabbage",
            "display_name": "Cabbage",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 4.9, "avg_yield_unit_weight_g": 1200.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Head Form", "days_start": 31, "days_end": 70, "moisture": "Wet"},
                    "stage_3": {"label": "Maturity", "days_start": 71, "days_end": 100, "moisture": "Moist"}
                },
                "height_milestones": {"4": 15, "8": 30, "12": 35}
            }
        },
        {
            "name": "bhendi",
            "display_name": "Bhendi (Okra)",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 7.4, "avg_yield_unit_weight_g": 20.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 80, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 81, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 90}
            }
        },
        {
            "name": "brinjal",
            "display_name": "Brinjal",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 2.7, "avg_yield_unit_weight_g": 50.0,
                "total_duration_days": [140, 150],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 120, "moisture": "Wet"},
                    "stage_3": {"label": "Harvesting", "days_start": 121, "days_end": 150, "moisture": "Moist"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 80}
            }
        },
        {
            "name": "capsicum",
            "display_name": "Capsicum",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 3.7, "avg_yield_unit_weight_g": 100.0,
                "total_duration_days": [150, 160],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 120, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 121, "days_end": 160, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 50, "12": 75}
            }
        },

        # --- GOURDS & MELONS ---
        {
            "name": "pumpkin",
            "display_name": "Pumpkin",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.8, "avg_yield_unit_weight_g": 3000.0,
                "total_duration_days": [120, 130],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Fruiting", "days_start": 101, "days_end": 130, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 150, "12": 300}
            }
        },
        {
            "name": "snake_gourd",
            "display_name": "Snake Gourd",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.8, "avg_yield_unit_weight_g": 600.0,
                "total_duration_days": [130, 140],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 110, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 111, "days_end": 140, "moisture": "Dry"}
                },
                "height_milestones": {"4": 50, "8": 180, "12": 350}
            }
        },
        {
            "name": "ribbed_gourd",
            "display_name": "Ribbed Gourd",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.8, "avg_yield_unit_weight_g": 300.0,
                "total_duration_days": [120, 130],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 101, "days_end": 130, "moisture": "Dry"}
                },
                "height_milestones": {"4": 45, "8": 160, "12": 320}
            }
        },
        {
            "name": "bottle_gourd",
            "display_name": "Bottle Gourd",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.4, "avg_yield_unit_weight_g": 1000.0,
                "total_duration_days": [130, 140],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 110, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 111, "days_end": 140, "moisture": "Dry"}
                },
                "height_milestones": {"4": 50, "8": 200, "12": 400}
            }
        },
        {
            "name": "bitter_gourd",
            "display_name": "Bitter Gourd",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.8, "avg_yield_unit_weight_g": 150.0,
                "total_duration_days": [120, 130],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 100, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 101, "days_end": 130, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 150, "12": 300}
            }
        },
        {
            "name": "ash_gourd",
            "display_name": "Ash Gourd",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.4, "avg_yield_unit_weight_g": 4000.0,
                "total_duration_days": [140, 150],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 41, "days_end": 120, "moisture": "Moist"},
                    "stage_3": {"label": "Fruiting", "days_start": 121, "days_end": 150, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 160, "12": 350}
            }
        },
        {
            "name": "cucumber",
            "display_name": "Cucumber",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 2.2, "avg_yield_unit_weight_g": 300.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 70, "moisture": "Wet"},
                    "stage_3": {"label": "Harvesting", "days_start": 71, "days_end": 100, "moisture": "Moist"}
                },
                "height_milestones": {"4": 35, "8": 120, "12": 200}
            }
        },
        {
            "name": "watermelon",
            "display_name": "Watermelon",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.1, "avg_yield_unit_weight_g": 3500.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Fruiting", "days_start": 71, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 150, "12": 250}
            }
        },
        {
            "name": "muskmelon",
            "display_name": "Muskmelon",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.1, "avg_yield_unit_weight_g": 800.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Fruiting", "days_start": 71, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 35, "8": 130, "12": 220}
            }
        },
        {
            "name": "tinda",
            "display_name": "Tinda",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.1, "avg_yield_unit_weight_g": 60.0,
                "total_duration_days": [60, 70],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 25, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 26, "days_end": 50, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 51, "days_end": 70, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 80, "12": 120}
            }
        },
        {
            "name": "chowchow",
            "display_name": "Chowchow",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.2, "avg_yield_unit_weight_g": 300.0,
                "total_duration_days": [150, 180],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 60, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 61, "days_end": 120, "moisture": "Wet"},
                    "stage_3": {"label": "Harvesting", "days_start": 121, "days_end": 180, "moisture": "Moist"}
                },
                "height_milestones": {"4": 40, "8": 150, "12": 300}
            }
        },
        {
            "name": "cluster_bean",
            "display_name": "Cluster Bean",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 11.0, "avg_yield_unit_weight_g": 3.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 70, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 71, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 60, "12": 90}
            }
        },
        {
            "name": "vegetable_cowpea",
            "display_name": "Vegetable Cowpea",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 14.8, "avg_yield_unit_weight_g": 10.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 36, "days_end": 75, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 76, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 60, "12": 80}
            }
        },
        {
            "name": "french_bean",
            "display_name": "French Bean",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 16.6, "avg_yield_unit_weight_g": 6.0,
                "total_duration_days": [70, 80],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 25, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 26, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 61, "days_end": 80, "moisture": "Dry"}
                },
                "height_milestones": {"4": 25, "8": 45, "12": 50}
            }
        },
        {
            "name": "peas",
            "display_name": "Peas",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 5, "optimal_density": 22.0, "avg_yield_unit_weight_g": 5.0,
                "total_duration_days": [80, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 31, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 50, "12": 70}
            }
        },
        {
            "name": "annual_moringa",
            "display_name": "Annual Moringa",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 0.2, "avg_yield_unit_weight_g": 120.0,
                "total_duration_days": [160, 180],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 60, "moisture": "Moist"},
                    "stage_2": {"label": "Flowering", "days_start": 61, "days_end": 120, "moisture": "Dry"},
                    "stage_3": {"label": "Harvesting", "days_start": 121, "days_end": 180, "moisture": "Dry"}
                },
                "height_milestones": {"4": 40, "8": 120, "12": 200}
            }
        },
        {
            "name": "cauliflower",
            "display_name": "Cauliflower",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 3.7, "avg_yield_unit_weight_g": 600.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 30, "moisture": "Moist"},
                    "stage_2": {"label": "Curd Form", "days_start": 31, "days_end": 70, "moisture": "Wet"},
                    "stage_3": {"label": "Harvesting", "days_start": 71, "days_end": 100, "moisture": "Moist"}
                },
                "height_milestones": {"4": 15, "8": 35, "12": 45}
            }
        },
        {
            "name": "small_onion",
            "display_name": "Small Onion",
            "category": "Vegetable",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 50.0, "avg_yield_unit_weight_g": 15.0,
                "total_duration_days": [70, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Bulbing", "days_start": 36, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Harvesting", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 15, "8": 30, "12": 35}
            }
        },

        # --- TUBERS ---
        {
            "name": "carrot",
            "display_name": "Carrot",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 66.0, "avg_yield_unit_weight_g": 60.0,
                "total_duration_days": [90, 100],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 45, "moisture": "Moist"},
                    "stage_2": {"label": "Root Dev", "days_start": 46, "days_end": 80, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 81, "days_end": 100, "moisture": "Dry"}
                },
                "height_milestones": {"4": 15, "8": 30, "12": 35}
            }
        },
        {
            "name": "beetroot",
            "display_name": "Beetroot",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 33.0, "avg_yield_unit_weight_g": 100.0,
                "total_duration_days": [70, 90],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 35, "moisture": "Moist"},
                    "stage_2": {"label": "Bulking", "days_start": 36, "days_end": 60, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 61, "days_end": 90, "moisture": "Dry"}
                },
                "height_milestones": {"4": 15, "8": 30, "12": 35}
            }
        },
        {
            "name": "radish",
            "display_name": "Radish",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 33.0, "avg_yield_unit_weight_g": 80.0,
                "total_duration_days": [45, 60],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 20, "moisture": "Moist"},
                    "stage_2": {"label": "Root Dev", "days_start": 21, "days_end": 40, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 41, "days_end": 60, "moisture": "Dry"}
                },
                "height_milestones": {"4": 20, "8": 35, "12": 35}
            }
        },
        {
            "name": "sweet_potato",
            "display_name": "Sweet Potato",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 8.3, "avg_yield_unit_weight_g": 150.0,
                "total_duration_days": [110, 120],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 40, "moisture": "Moist"},
                    "stage_2": {"label": "Bulking", "days_start": 41, "days_end": 90, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 91, "days_end": 120, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 60, "12": 80}
            }
        },
        {
            "name": "tapoica",
            "display_name": "Tapioca (Cassava)",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.2, "avg_yield_unit_weight_g": 400.0,
                "total_duration_days": [270, 300],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 60, "moisture": "Moist"},
                    "stage_2": {"label": "Bulking", "days_start": 61, "days_end": 200, "moisture": "Dry"},
                    "stage_3": {"label": "Maturity", "days_start": 201, "days_end": 300, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 80, "12": 120}
            }
        },
        {
            "name": "elephant_foot_yam",
            "display_name": "Elephant Foot Yam",
            "category": "Tuber",
            "growth_config": {
                "optimal_lcc": 4, "optimal_density": 1.2, "avg_yield_unit_weight_g": 2000.0,
                "total_duration_days": [240, 270],
                "stages": {
                    "stage_1": {"label": "Vegetative", "days_start": 0, "days_end": 60, "moisture": "Moist"},
                    "stage_2": {"label": "Corm Dev", "days_start": 61, "days_end": 180, "moisture": "Moist"},
                    "stage_3": {"label": "Maturity", "days_start": 181, "days_end": 270, "moisture": "Dry"}
                },
                "height_milestones": {"4": 30, "8": 60, "12": 80}
            }
        }
    ]

    with app.app_context():
        print(f"[BioGrow Seed] Seeding {len(crops_data)} crops from TNAU Knowledge Base...")

        for crop in crops_data:
            existing = CropStandard.query.filter_by(crop_name=crop["name"]).first()
            if not existing:
                new_crop = CropStandard(
                    crop_name=crop["name"],
                    display_name=crop["display_name"],
                    category=crop["category"],
                    growth_config=crop["growth_config"]
                )
                db.session.add(new_crop)
                print(f"   [+] Added: {crop['display_name']}")
            else:
                existing.growth_config = crop["growth_config"]
                existing.display_name = crop["display_name"]
                existing.category = crop["category"]
                print(f"   [*] Updated: {crop['display_name']}")

        db.session.commit()
        print("[BioGrow Seed] Database Population Complete!")

if __name__ == '__main__':
    seed_database()