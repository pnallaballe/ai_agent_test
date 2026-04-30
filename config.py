"""
Updated Configuration with Market-Specific Grading
Corrected for banana ripeness stages and export standards
"""

import os
from datetime import timedelta

# ============================================================================
# BASIC SETTINGS
# ============================================================================

DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
DATABASE_PATH = os.path.join(os.getcwd(), 'data', 'grades.db')
MODELS_FOLDER = os.path.join(os.getcwd(), 'models')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)

# ============================================================================
# BANANA RIPENESS STAGES
# ============================================================================

class RipenessStage:
    """Banana ripeness classification with color ranges"""
    
    STAGE_1_GREEN = {
        'name': 'Stage 1: Green (Unripe)',
        'ripeness_percentage': (0, 20),
        'rgb_range': {'r': (0, 100), 'g': (80, 150), 'b': (0, 80)},
        'visual_description': 'Completely green, no yellow',
        'days_to_consume': 10,
        'export_suitable': True,
        'export_distance_km': (5000, 15000),  # Long distance
        'score_multiplier': 1.0
    }
    
    STAGE_2_BREAKING = {
        'name': 'Stage 2: Breaking (Light Green-Yellow)',
        'ripeness_percentage': (20, 50),
        'rgb_range': {'r': (100, 180), 'g': (140, 200), 'b': (30, 100)},
        'visual_description': 'Green with yellow edges/patches <10%',
        'days_to_consume': 5,
        'export_suitable': True,
        'export_distance_km': (1000, 10000),  # Medium distance
        'score_multiplier': 0.95
    }
    
    STAGE_3_YELLOW = {
        'name': 'Stage 3: Yellow (Ripe)',
        'ripeness_percentage': (50, 70),
        'rgb_range': {'r': (200, 255), 'g': (180, 220), 'b': (0, 50)},
        'visual_description': 'Bright yellow, few or no brown spots',
        'days_to_consume': 2,
        'export_suitable': False,  # Will overripen during export
        'export_distance_km': (0, 1000),  # Local only
        'score_multiplier': 0.60  # Poor for export
    }
    
    STAGE_4_SPOTTED = {
        'name': 'Stage 4: Spotted (Over-ripe)',
        'ripeness_percentage': (70, 90),
        'rgb_range': {'r': (220, 255), 'g': (160, 200), 'b': (0, 50)},
        'visual_description': 'Yellow with brown/black spots',
        'days_to_consume': 1,
        'export_suitable': False,
        'export_distance_km': (0, 0),
        'score_multiplier': 0.20
    }
    
    STAGE_5_BROWN = {
        'name': 'Stage 5: Brown (Rotten)',
        'ripeness_percentage': (90, 100),
        'rgb_range': {'r': (139, 200), 'g': (69, 150), 'b': (19, 80)},
        'visual_description': 'Mostly brown/black',
        'days_to_consume': 0,
        'export_suitable': False,
        'export_distance_km': (0, 0),
        'score_multiplier': 0.0  # Reject
    }

# ============================================================================
# MARKET-SPECIFIC GRADING PROFILES
# ============================================================================

MARKET_PROFILES = {
    'USA_EUROPE_EXPORT': {
        'name': 'USA & European Export (Long Distance)',
        'journey_days': 14,
        'target_ripeness_stages': [1, 2],  # Stage 1-2 (Green to Light Yellow)
        'preferred_stage': 1,
        'color_requirements': {
            'preferred': 'GREEN',
            'acceptable': 'LIGHT_GREEN_YELLOW',
            'unacceptable': 'BRIGHT_YELLOW'
        },
        'quality_thresholds': {
            'GRADE_A': 0.92,  # Deep green, perfect
            'GRADE_B': 0.80,  # Green with minimal yellow
            'GRADE_C': 0.65,  # Acceptable but some yellow
            'REJECT': 0.60    # Too yellow for export
        },
        'spot_requirements': {
            'allowed_brown_spots': 0,
            'allowed_yellow_patches': '< 5%',
        },
        'blemish_tolerance': 'Strict (small defects acceptable)',
        'target_markets': ['USA', 'UK', 'Germany', 'France', 'Netherlands']
    },
    
    'MIDDLE_EAST_EXPORT': {
        'name': 'Middle East Export (Medium Distance)',
        'journey_days': 7,
        'target_ripeness_stages': [2, 3],  # Stage 2-3 (Light Green-Yellow to Yellow)
        'preferred_stage': 2,
        'color_requirements': {
            'preferred': 'LIGHT_GREEN_YELLOW',
            'acceptable': 'YELLOW',
            'unacceptable': 'BROWN'
        },
        'quality_thresholds': {
            'GRADE_A': 0.90,  # Light green-yellow, minimal yellow
            'GRADE_B': 0.78,  # Some yellow acceptable
            'GRADE_C': 0.65,  # Mostly yellow but acceptable
            'REJECT': 0.60    # Too ripe or diseased
        },
        'spot_requirements': {
            'allowed_brown_spots': '1-2 small spots',
            'allowed_yellow_patches': '< 15%',
        },
        'blemish_tolerance': 'Moderate',
        'target_markets': ['UAE', 'Saudi Arabia', 'Qatar', 'Kuwait']
    },
    
    'ASIA_EXPORT': {
        'name': 'Asian Markets Export (Variable Distance)',
        'journey_days': 10,
        'target_ripeness_stages': [1, 2, 3],  # Flexible
        'preferred_stage': 2,
        'color_requirements': {
            'preferred': 'LIGHT_GREEN_YELLOW',
            'acceptable': 'GREEN_OR_YELLOW',
            'unacceptable': 'BROWN'
        },
        'quality_thresholds': {
            'GRADE_A': 0.90,
            'GRADE_B': 0.77,
            'GRADE_C': 0.63,
            'REJECT': 0.60
        },
        'spot_requirements': {
            'allowed_brown_spots': '1-3 small spots',
            'allowed_yellow_patches': '< 20%',
        },
        'blemish_tolerance': 'Moderate to Lenient',
        'target_markets': ['Japan', 'India', 'Singapore', 'Malaysia']
    },
    
    'LOCAL_REGIONAL_MARKET': {
        'name': 'Local & Regional Markets (Short Distance)',
        'journey_days': 3,
        'target_ripeness_stages': [3, 4],  # Stage 3-4 (Yellow to Spotted)
        'preferred_stage': 3,
        'color_requirements': {
            'preferred': 'BRIGHT_YELLOW',
            'acceptable': 'YELLOW_WITH_SPOTS',
            'unacceptable': 'BROWN'
        },
        'quality_thresholds': {
            'GRADE_A': 0.88,  # Bright yellow, perfect
            'GRADE_B': 0.75,  # Yellow with few spots
            'GRADE_C': 0.60,  # Yellow with multiple spots but edible
            'REJECT': 0.50    # Brown/rotten
        },
        'spot_requirements': {
            'allowed_brown_spots': '< 5 spots',
            'allowed_yellow_patches': 'Unlimited (fully yellow expected)',
        },
        'blemish_tolerance': 'Lenient',
        'target_markets': ['Local', 'Regional Wholesale']
    }
}

# ============================================================================
# CORRECTED GRADING CRITERIA
# ============================================================================

QUALITY_PARAMETERS = {
    'color': {
        'weight': 0.35,  # Increased (most important for ripeness)
        'description': 'Color analysis (green to yellow progression)',
        'export_critical': True
    },
    'ripeness_stage': {
        'weight': 0.25,  # New parameter
        'description': 'Ripeness stage classification (1-5)',
        'export_critical': True
    },
    'defects': {
        'weight': 0.20,  # Reduced (less critical than before)
        'description': 'Physical damage, bruises, cuts',
        'export_critical': False
    },
    'disease': {
        'weight': 0.15,  # Reduced
        'description': 'Fungal spots, mold, rot indicators',
        'export_critical': False
    },
    'size_shape': {
        'weight': 0.05,  # Less critical for bananas
        'description': 'Shape and size uniformity',
        'export_critical': False
    }
}

# Color score mapping (0-1)
COLOR_SCORES = {
    'STAGE_1_GREEN': 1.0,           # Perfect for export (USA/EU)
    'STAGE_2_BREAKING': 0.95,       # Excellent for export
    'STAGE_3_YELLOW': 0.60,         # Poor for export (local only)
    'STAGE_4_SPOTTED': 0.30,        # Bad for export
    'STAGE_5_BROWN': 0.0            # Reject
}

# ============================================================================
# MARKET-SPECIFIC GRADING THRESHOLDS (CORRECTED)
# ============================================================================

GRADING_THRESHOLDS = {
    'USA_EUROPE_EXPORT': {
        'GRADE_A': 0.92,      # Deep green, no yellow
        'GRADE_B': 0.80,      # Green with minimal yellow
        'GRADE_C': 0.65,      # Some yellow but acceptable for export
        'REJECT': 0.0         # Too ripe or damaged
    },
    'MIDDLE_EAST_EXPORT': {
        'GRADE_A': 0.90,      # Light green-yellow
        'GRADE_B': 0.78,      # Some yellow acceptable
        'GRADE_C': 0.65,      # Mostly yellow but ok
        'REJECT': 0.0
    },
    'ASIA_EXPORT': {
        'GRADE_A': 0.90,      # Flexible on ripeness
        'GRADE_B': 0.77,
        'GRADE_C': 0.63,
        'REJECT': 0.0
    },
    'LOCAL_REGIONAL_MARKET': {
        'GRADE_A': 0.88,      # Bright yellow, few spots
        'GRADE_B': 0.75,      # Yellow with some spots
        'GRADE_C': 0.60,      # Yellow with multiple spots
        'REJECT': 0.0
    }
}

# ============================================================================
# BATCH REQUIREMENTS (FRAUD PREVENTION - UPDATED)
# ============================================================================

BATCH_SETTINGS = {
    'min_images': 20,                    # Minimum 20 images per batch
    'min_images_per_angle': 3,           # At least 3 angles
    'min_time_gap': 5,                   # 5 min gap between uploads (in seconds)
    'max_batch_age': timedelta(days=7),  # Batch must be graded within 7 days
    'required_ripeness_variance': 0.15,  # Batches should have ripeness variation
    'min_ripeness_variance': 0.05        # But not too much (>15% is suspicious)
}

# ============================================================================
# FRAUD DETECTION THRESHOLDS (UPDATED FOR RIPENESS)
# ============================================================================

FRAUD_DETECTION = {
    # Statistical anomalies - UPDATED
    'ALL_STAGE_1_SUSPICIOUS': True,     # All Stage 1? Suspicious (mix expected)
    'ALL_STAGE_3_PLUS_SUSPICIOUS': True, # All too ripe? Can't export
    'RIPENESS_VARIANCE_THRESHOLD': 0.20, # Too much variation = suspicious
    
    # Perfect grades still suspicious
    'PERFECT_GRADE_THRESHOLD': 0.85,     # If > 85% Grade A = suspicious
    'VARIANCE_THRESHOLD': 0.05,          # Low variance = might be duplicates
    
    # Time-based anomalies
    'MIN_UPLOAD_TIME_PER_IMAGE': 10,     # 10 sec per image minimum
    'MAX_UPLOADS_PER_HOUR': 100,         # Max 100 batches/hour
    
    # Image similarity
    'DUPLICATE_IMAGE_THRESHOLD': 0.95,
    
    # Location anomalies
    'LOCATION_VARIANCE_KM': 50,
    
    # Pattern anomalies
    'CONSECUTIVE_PERFECT_BATCHES': 10,
    
    # NEW: Ripeness anomalies
    'TOO_RIPE_FOR_EXPORT': {
        'stage': 3,  # Stage 3+ is too ripe for long-distance export
        'severity': 'HIGH',
        'message': 'Bananas too ripe - will spoil in transit'
    },
    'TOO_GREEN_FOR_LOCAL': {
        'stage': 1,  # Stage 1 is too green for local markets
        'severity': 'MEDIUM',
        'message': 'Bananas too green - may not ripen properly'
    }
}

# ============================================================================
# AUDIT TRAIL SETTINGS
# ============================================================================

AUDIT_SETTINGS = {
    'log_all_grades': True,
    'track_location': True,
    'track_user_agent': True,
    'require_farmer_id': True,
    'require_batch_number': True,
    'store_images_metadata': True,
    'track_ripeness_stage': True,  # NEW
    'track_market_profile': True,  # NEW
}

# ============================================================================
# INSPECTION & VERIFICATION (UPDATED)
# ============================================================================

INSPECTION_SETTINGS = {
    'spot_check_percentage': 10,
    'high_risk_percentage': 50,
    'medium_risk_percentage': 25,
    'inspection_deadline_days': 3,
    'physical_inspection_variance': 0.15,
    'ripeness_stage_variance_allowed': 0.5,
}

# ============================================================================
# API SETTINGS (For Boomi Integration)
# ============================================================================

API_SETTINGS = {
    'timeout': 300,
    'max_file_size': 100 * 1024 * 1024,
    'allowed_image_formats': ['jpg', 'jpeg', 'png', 'tiff'],
    'allowed_video_formats': ['mp4', 'avi', 'mov', 'mkv'],
    'require_market_profile': True,  # NEW - must specify market
}

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

NOTIFICATION_SETTINGS = {
    'notify_on_fraud_detection': True,
    'notify_on_failed_inspection': True,
    'notify_on_batch_ready': False,
    'notify_on_ripeness_mismatch': True,  # NEW - alert if wrong stage for market
    'email_alerts_enabled': False,
}

# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'audit_log_file': os.path.join(os.getcwd(), 'logs', 'audit.log'),
    'fraud_log_file': os.path.join(os.getcwd(), 'logs', 'fraud.log'),
}

os.makedirs(os.path.dirname(LOGGING['audit_log_file']), exist_ok=True)

# ============================================================================
# MODEL SETTINGS
# ============================================================================

MODEL_SETTINGS = {
    'use_gpu': False,
    'confidence_threshold': 0.5,
    'image_size': (224, 224),
    'detect_ripeness_stage': True,  # NEW - must detect ripeness
    'detect_color_distribution': True,  # NEW - analyze green/yellow ratio
}
