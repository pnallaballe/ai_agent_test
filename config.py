"""
Configuration file for Banana Crop Grading AI Agent
Contains all settings, paths, and thresholds
"""

import os
from datetime import timedelta

# ============================================================================
# BASIC SETTINGS
# ============================================================================

# App Settings
DEBUG = True
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
DATABASE_PATH = os.path.join(os.getcwd(), 'data', 'grades.db')
MODELS_FOLDER = os.path.join(os.getcwd(), 'models')

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(MODELS_FOLDER, exist_ok=True)

# ============================================================================
# GRADING CRITERIA
# ============================================================================

# Grade thresholds (confidence scores)
GRADING_THRESHOLDS = {
    'GRADE_A': 0.90,      # 90-100% quality
    'GRADE_B': 0.75,      # 75-89% quality
    'GRADE_C': 0.60,      # 60-74% quality
    'REJECT': 0.0         # Below 60% quality
}

# Quality parameters and their importance
QUALITY_PARAMETERS = {
    'color': {'weight': 0.25, 'good': 0.8},           # Bright yellow = good
    'defects': {'weight': 0.30, 'good': 0.9},         # No blemishes = good
    'disease': {'weight': 0.25, 'good': 0.95},        # Disease-free = good
    'size_shape': {'weight': 0.20, 'good': 0.85}      # Normal shape = good
}

# ============================================================================
# BATCH REQUIREMENTS (Fraud Prevention)
# ============================================================================

# Minimum samples required per batch
BATCH_SETTINGS = {
    'min_images': 20,                    # Minimum 20 images per batch
    'min_images_per_angle': 3,           # At least 3 angles
    'min_time_gap': 5,                   # 5 min gap between uploads (in seconds)
    'max_batch_age': timedelta(days=7)   # Batch must be graded within 7 days
}

# ============================================================================
# FRAUD DETECTION THRESHOLDS
# ============================================================================

FRAUD_DETECTION = {
    # Statistical anomaly detection
    'PERFECT_GRADE_THRESHOLD': 0.85,     # If > 85% Grade A = suspicious
    'VARIANCE_THRESHOLD': 0.05,          # Low variance = might be duplicate images
    
    # Time-based anomalies
    'MIN_UPLOAD_TIME_PER_IMAGE': 10,     # Should take min 10 sec per image (in seconds)
    'MAX_UPLOADS_PER_HOUR': 100,         # Max 100 batches/hour per farmer
    
    # Image similarity detection
    'DUPLICATE_IMAGE_THRESHOLD': 0.95,   # 95% similar = probably duplicate
    
    # Location anomalies
    'LOCATION_VARIANCE_KM': 50,          # Should be within 50km of registered farm
    
    # Pattern anomalies
    'CONSECUTIVE_PERFECT_BATCHES': 10,   # If 10 consecutive perfect batches = flag
}

# ============================================================================
# AUDIT TRAIL SETTINGS
# ============================================================================

AUDIT_SETTINGS = {
    'log_all_grades': True,              # Log every single grade
    'track_location': True,              # GPS tracking enabled
    'track_user_agent': True,            # Track device/browser info
    'require_farmer_id': True,           # Must have farmer ID
    'require_batch_number': True,        # Must have batch number
    'store_images_metadata': True,       # Store EXIF data from images
}

# ============================================================================
# INSPECTION & VERIFICATION
# ============================================================================

INSPECTION_SETTINGS = {
    # Spot check percentage
    'spot_check_percentage': 10,         # Inspect 10% of batches randomly
    
    # Risk-based inspection
    'high_risk_percentage': 50,          # 50% of "suspicious" batches
    'medium_risk_percentage': 25,        # 25% of "medium-risk" batches
    
    # How many days to conduct physical inspection
    'inspection_deadline_days': 3,
    
    # Pass/fail criteria for physical inspection
    'physical_inspection_variance': 0.15, # +/- 15% difference acceptable
}

# ============================================================================
# API SETTINGS (For Boomi Integration)
# ============================================================================

API_SETTINGS = {
    'timeout': 300,                      # 5 minutes timeout
    'max_file_size': 100 * 1024 * 1024,  # 100MB max file size
    'allowed_image_formats': ['jpg', 'jpeg', 'png', 'tiff'],
    'allowed_video_formats': ['mp4', 'avi', 'mov', 'mkv'],
}

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

NOTIFICATION_SETTINGS = {
    'notify_on_fraud_detection': True,
    'notify_on_failed_inspection': True,
    'notify_on_batch_ready': False,
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

# Create logs directory
os.makedirs(os.path.dirname(LOGGING['audit_log_file']), exist_ok=True)

# ============================================================================
# MODEL SETTINGS
# ============================================================================

MODEL_SETTINGS = {
    'use_gpu': False,                    # Set to True if GPU available
    'confidence_threshold': 0.5,         # Minimum confidence for detection
    'image_size': (224, 224),            # Standard image size for processing
}
