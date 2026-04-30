"""
Main Flask Application for Banana Crop Grading AI Agent
Simple web interface for uploading and grading banana batches
"""

import logging
import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Import our custom modules
from agent.grading_agent import BananaGradingAgent
from agent.audit_manager import AuditManager, calculate_file_hash
import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.API_SETTINGS['max_file_size']
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

# Initialize AI Agent and Audit Manager
grading_agent = BananaGradingAgent()
audit_manager = AuditManager(config.LOGGING['audit_log_file'])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename, file_type='image'):
    """Check if file is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        return ext in config.API_SETTINGS['allowed_image_formats']
    elif file_type == 'video':
        return ext in config.API_SETTINGS['allowed_video_formats']
    
    return False

def get_market_profile(market_name):
    """Get market profile from config"""
    return config.MARKET_PROFILES.get(market_name, None)

# ============================================================================
# ROUTES - Web Interface
# ============================================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', markets=list(config.MARKET_PROFILES.keys()))

@app.route('/dashboard')
def dashboard():
    """Grading dashboard"""
    return render_template('dashboard.html')

# ============================================================================
# API ROUTES - For Integration
# ============================================================================

@app.route('/api/grade-batch', methods=['POST'])
def grade_batch():
    """
    Grade a batch of banana images
    
    Form Parameters:
    - farmer_id: Unique farmer identifier (required)
    - batch_number: Batch identifier (required)
    - market_profile: Target market (required)
    - files: List of image files (required, min 20)
    
    Returns:
    JSON with grading results
    """
    try:
        # Validate required fields
        farmer_id = request.form.get('farmer_id')
        batch_number = request.form.get('batch_number')
        market_profile = request.form.get('market_profile')
        
        if not all([farmer_id, batch_number, market_profile]):
            return jsonify({
                'status': 'ERROR',
                'message': 'Missing required fields: farmer_id, batch_number, market_profile'
            }), 400
        
        # Validate market profile
        if market_profile not in config.MARKET_PROFILES:
            return jsonify({
                'status': 'ERROR',
                'message': f'Invalid market profile. Allowed: {list(config.MARKET_PROFILES.keys())}'
            }), 400
        
        # Check files
        if 'files' not in request.files:
            return jsonify({
                'status': 'ERROR',
                'message': 'No files uploaded'
            }), 400
        
        files = request.files.getlist('files')
        
        if len(files) < config.BATCH_SETTINGS['min_images']:
            return jsonify({
                'status': 'ERROR',
                'message': f'Minimum {config.BATCH_SETTINGS["min_images"]} images required'
            }), 400
        
        # Save uploaded files
        uploaded_paths = []
        upload_hashes = []
        
        for file in files:
            if file and allowed_file(file.filename, 'image'):
                filename = secure_filename(f"{batch_number}_{len(uploaded_paths)}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_paths.append(filepath)
                
                # Calculate file hash for duplicate detection
                file_hash = calculate_file_hash(filepath)
                upload_hashes.append(file_hash)
                
                # Log upload
                audit_manager.log_upload(
                    farmer_id=farmer_id,
                    batch_number=batch_number,
                    file_name=filename,
                    file_hash=file_hash,
                    file_size=os.path.getsize(filepath),
                    upload_timestamp=datetime.now(),
                    location=request.form.get('location'),
                    device_info=request.form.get('device_info')
                )
        
        if not uploaded_paths:
            return jsonify({
                'status': 'ERROR',
                'message': 'No valid image files uploaded'
            }), 400
        
        # Check for duplicate images
        duplicates_found = []
        for file_hash in upload_hashes:
            is_dup, prev_upload = audit_manager.detect_duplicate_images(farmer_id, file_hash)
            if is_dup:
                duplicates_found.append(prev_upload)
        
        if duplicates_found:
            return jsonify({
                'status': 'ERROR',
                'message': f'Duplicate images detected: {len(duplicates_found)} images',
                'duplicate_uploads': duplicates_found
            }), 400
        
        # Grade the batch
        logger.info(f"Grading batch {batch_number} for farmer {farmer_id} - Market: {market_profile}")
        batch_result = grading_agent.grade_batch(
            image_paths=uploaded_paths,
            batch_number=batch_number,
            farmer_id=farmer_id,
            market_profile=market_profile
        )
        
        # Log grading results
        for result in batch_result.get('individual_results', []):
            audit_manager.log_grading(
                upload_id=result.get('image_path'),
                farmer_id=farmer_id,
                batch_number=batch_number,
                grade=result.get('grade'),
                confidence=result.get('confidence'),
                detected_issues=result.get('detected_issues', []),
                grading_timestamp=datetime.now()
            )
        
        # Detect fraud patterns
        anomalies = audit_manager.detect_statistical_anomalies(
            farmer_id,
            batch_result.get('individual_results', [])
        )
        
        # Add fraud detection to response
        batch_result['fraud_analysis'] = {
            'anomalies_detected': anomalies,
            'fraud_score': audit_manager.get_farmer_fraud_score(farmer_id),
            'fraud_level': audit_manager._get_fraud_level(
                audit_manager.get_farmer_fraud_score(farmer_id)
            )
        }
        
        return jsonify(batch_result), 200
        
    except Exception as e:
        logger.error(f"Error in grade_batch: {e}")
        return jsonify({
            'status': 'ERROR',
            'message': str(e)
        }), 500

@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get available market profiles"""
    markets = {}
    for code, profile in config.MARKET_PROFILES.items():
        markets[code] = {
            'name': profile['name'],
            'journey_days': profile['journey_days'],
            'target_stages': profile['target_ripeness_stages'],
            'preferred_stage': profile['preferred_stage']
        }
    return jsonify(markets), 200

@app.route('/api/farmer-history/<farmer_id>', methods=['GET'])
def farmer_history(farmer_id):
    """Get grading history for a farmer"""
    days = request.args.get('days', 30, type=int)
    report = audit_manager.generate_audit_report(farmer_id, days=days)
    return jsonify(report), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.now().isoformat(),
        'agent': 'Banana Grading AI Agent v1.0'
    }), 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large"""
    return jsonify({
        'status': 'ERROR',
        'message': f'File too large. Maximum size: {config.API_SETTINGS["max_file_size"] / 1024 / 1024:.0f}MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    """Handle 404"""
    return jsonify({
        'status': 'ERROR',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500"""
    return jsonify({
        'status': 'ERROR',
        'message': 'Internal server error'
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Banana Crop Grading AI Agent...")
    logger.info(f"Upload folder: {config.UPLOAD_FOLDER}")
    logger.info(f"Audit log: {config.LOGGING['audit_log_file']}")
    logger.info("Available markets:")
    for code, profile in config.MARKET_PROFILES.items():
        logger.info(f"  - {code}: {profile['name']}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG,
        use_reloader=True
    )
