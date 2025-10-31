"""
CropGuard AI - API Endpoints
Handles disease prediction, recommendations, and combined analysis.
"""

import io
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import traceback

from app.services.prediction import load_mobilenet_model, predict_disease
from app.services.recommendation import generate_recommendation
from app.services.enhancer import load_real_esrgan_model, check_image_quality, enhance_image

# Create blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# ============ MODEL CACHING ============
# Cache models to avoid reloading on every request
_model_cache = {
    'prediction_model': None,
    'enhancer_model': None
}


def get_prediction_model():
    """Get or load the prediction model (cached)"""
    if _model_cache['prediction_model'] is None:
        _model_cache['prediction_model'] = load_mobilenet_model()
    return _model_cache['prediction_model']


def get_enhancer_model():
    """Get or load the enhancer model (cached)"""
    if _model_cache['enhancer_model'] is None:
        _model_cache['enhancer_model'] = load_real_esrgan_model()
    return _model_cache['enhancer_model']


# ============ VALIDATION UTILITIES ============

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_file(file):
    """
    Validate image file
    Returns: (is_valid: bool, error_message: str or None)
    """
    if not file or file.filename == '':
        return False, "No image file provided"

    if not allowed_file(file.filename):
        return False, "File must be JPG or PNG format"

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > MAX_FILE_SIZE:
        return False, "File size must be under 10MB"

    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, "File must be a valid JPG or PNG image"

    return True, None


# ============ API ROUTES ============

@api_bp.route('/predict', methods=['POST'])
def predict():
    """
    Disease Prediction Endpoint

    Request: multipart/form-data with image file
    Response: disease_name, confidence, severity_level, gradcam_image, image_quality
    """
    try:
        # Validate request has file
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Validate file
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Read image bytes
        image_bytes = file.read()

        # Load prediction model
        model = get_prediction_model()
        if model is None:
            return jsonify({
                'success': False,
                'error': 'Model loading failed. Please try again.'
            }), 500

        # Get initial prediction
        result = predict_disease(model, image_bytes)

        # Check image quality (blur detection)
        image_quality = 'good'
        if check_image_quality(image_bytes):
            image_quality = 'blurry'
            # Try to enhance
            enhancer = get_enhancer_model()
            if enhancer is not None:
                try:
                    enhanced_bytes = enhance_image(image_bytes, enhancer)
                    if enhanced_bytes != image_bytes:  # Successfully enhanced
                        # Re-predict on enhanced image
                        result = predict_disease(model, enhanced_bytes)
                        image_quality = 'enhanced'
                except Exception as e:
                    print(f"Enhancement failed: {e}")
                    # Continue with original prediction

        return jsonify({
            'success': True,
            'disease_name': result['disease_name'],
            'confidence': result['confidence'],
            'severity_level': result['severity_level'],
            'gradcam_image': result['gradcam_image'],
            'image_quality': image_quality,
            'message': f"Disease detected. Severity level {result['severity_level']}/5."
        }), 200

    except Exception as e:
        print(f"Prediction error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Prediction failed. Please try again.'
        }), 500


@api_bp.route('/recommend', methods=['POST'])
def recommend():
    """
    Treatment Recommendation Endpoint

    Request: JSON with disease_name, severity_level, language_code (optional)
    Response: recommendation text in specified language
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # Validate required fields
        disease_name = data.get('disease_name')
        severity_level = data.get('severity_level')
        language_code = data.get('language_code', 'en')

        if not disease_name or severity_level is None:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: disease_name, severity_level'
            }), 400

        # Validate severity level
        try:
            severity_level = int(severity_level)
            if severity_level < 1 or severity_level > 5:
                return jsonify({
                    'success': False,
                    'error': 'Severity level must be between 1 and 5'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Severity level must be an integer'
            }), 400

        # Generate recommendation
        recommendation = generate_recommendation(disease_name, severity_level, language_code)

        return jsonify({
            'success': True,
            'disease_name': disease_name,
            'severity_level': severity_level,
            'language_code': language_code,
            'recommendation': recommendation,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200

    except Exception as e:
        print(f"Recommendation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Recommendation generation failed'
        }), 500


@api_bp.route('/predict-and-recommend', methods=['POST'])
def predict_and_recommend():
    """
    Combined Prediction + Recommendation Endpoint

    Runs prediction on the image, then generates a recommendation based on results.

    Request: multipart/form-data with image file and optional language_code
    Response: Combined prediction + recommendation results
    """
    try:
        # Validate request has file
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Validate file
        is_valid, error_msg = validate_image_file(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Get language code from form
        language_code = request.form.get('language_code', 'en')

        # Read image bytes
        image_bytes = file.read()

        # Load prediction model
        model = get_prediction_model()
        if model is None:
            return jsonify({
                'success': False,
                'error': 'Model loading failed. Please try again.'
            }), 500

        # Get initial prediction
        prediction_result = predict_disease(model, image_bytes)

        # Check image quality (blur detection)
        image_quality = 'good'
        if check_image_quality(image_bytes):
            image_quality = 'blurry'
            # Try to enhance
            enhancer = get_enhancer_model()
            if enhancer is not None:
                try:
                    enhanced_bytes = enhance_image(image_bytes, enhancer)
                    if enhanced_bytes != image_bytes:  # Successfully enhanced
                        # Re-predict on enhanced image
                        prediction_result = predict_disease(model, enhanced_bytes)
                        image_quality = 'enhanced'
                except Exception as e:
                    print(f"Enhancement failed: {e}")
                    # Continue with original prediction

        # Generate recommendation based on prediction
        recommendation_text = generate_recommendation(
            prediction_result['disease_name'],
            prediction_result['severity_level'],
            language_code
        )

        return jsonify({
            'success': True,
            'prediction': {
                'disease_name': prediction_result['disease_name'],
                'confidence': prediction_result['confidence'],
                'severity_level': prediction_result['severity_level'],
                'gradcam_image': prediction_result['gradcam_image'],
                'image_quality': image_quality,
                'message': f"Disease detected. Severity level {prediction_result['severity_level']}/5."
            },
            'recommendation': {
                'disease_name': prediction_result['disease_name'],
                'severity_level': prediction_result['severity_level'],
                'language_code': language_code,
                'recommendation': recommendation_text,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        }), 200

    except Exception as e:
        print(f"Combined prediction-recommendation error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Prediction failed. Please try again.'
        }), 500


# ============ BLUEPRINT REGISTRATION ============
# This blueprint will be imported and registered in main.py
# The routes will be prefixed with /api automatically
