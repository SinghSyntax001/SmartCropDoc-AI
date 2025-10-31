"""
CropGuard AI - Flask Application
Main entry point for the crop disease detection web application.
"""

import os
from pathlib import Path
from flask import Flask, render_template_string, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the app root directory
APP_ROOT = Path(__file__).parent.parent

# Create Flask app
app = Flask(
    __name__,
    template_folder=str(APP_ROOT / 'frontend'),
    static_folder=str(APP_ROOT / 'frontend/styles'),
    static_url_path='/static'
)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

# Enable CORS for API endpoints
CORS(app)


# ============ STATIC FILE SERVING ROUTES ============

@app.route('/static/style.css')
def serve_main_css():
    """Serve main.css"""
    return send_from_directory(str(APP_ROOT / 'frontend/styles'), 'main.css')


@app.route('/static/about.css')
def serve_about_css():
    """Serve about.css"""
    return send_from_directory(str(APP_ROOT / 'frontend/styles'), 'about.css')


@app.route('/static/guide.css')
def serve_guide_css():
    """Serve guide.css"""
    return send_from_directory(str(APP_ROOT / 'frontend/styles'), 'guide.css')


@app.route('/static/script.js')
def serve_script_js():
    """Serve script.js"""
    return send_from_directory(str(APP_ROOT / 'frontend/scripts'), 'script.js')


@app.route('/static/sw.js')
def serve_sw_js():
    """Serve service worker"""
    return send_from_directory(str(APP_ROOT / 'frontend/scripts'), 'sw.js')


@app.route('/static/images/<filename>')
def serve_image(filename):
    """Serve images from frontend/images directory"""
    try:
        return send_from_directory(str(APP_ROOT / 'frontend/images'), filename)
    except Exception:
        # Return 404 JSON response for missing images
        return jsonify({'error': 'Image not found'}), 404


# ============ TEMPLATE RENDERING ROUTES ============

def render_html_file(filename):
    """Helper function to render HTML files with Jinja2 templating"""
    try:
        with open(APP_ROOT / 'frontend' / filename, 'r') as f:
            content = f.read()
        return render_template_string(content)
    except Exception as e:
        return jsonify({'error': f'Template rendering failed: {str(e)}'}), 500


@app.route('/')
def home():
    """Render home page (index.html)"""
    return render_html_file('index.html')


@app.route('/about')
def about():
    """Render about page (about.html)"""
    return render_html_file('about.html')


@app.route('/guide')
def guide():
    """Render guide page (guide.html)"""
    return render_html_file('guide.html')


@app.route('/upload')
def upload():
    """Render upload page (upload.html)"""
    return render_html_file('upload.html')


@app.route('/login')
def login():
    """Render login page (login.html)"""
    try:
        with open(APP_ROOT / 'frontend' / 'login.html', 'r') as f:
            content = f.read()
        return render_template_string(content)
    except FileNotFoundError:
        # If login.html doesn't exist yet, return placeholder
        return jsonify({'message': 'Login page not yet implemented'}), 200


@app.route('/profile')
def profile():
    """Render profile page (profile.html)"""
    try:
        with open(APP_ROOT / 'frontend' / 'profile.html', 'r') as f:
            content = f.read()
        return render_template_string(content)
    except FileNotFoundError:
        # If profile.html doesn't exist yet, return placeholder
        return jsonify({'message': 'Profile page not yet implemented'}), 200


# ============ API ROUTE REGISTRATION ============

# Import API endpoints (routes are registered within endpoints.py)
from app.api import endpoints as api_endpoints


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'status': 500
    }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size limit exceeded (413 Payload Too Large)"""
    return jsonify({
        'success': False,
        'error': 'File size must be under 10MB',
        'status': 413
    }), 413


# ============ MAIN ENTRY POINT ============

if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    app.run(host=host, port=port, debug=debug)
