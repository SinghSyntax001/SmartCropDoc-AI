#!/usr/bin/env python3
"""
CropGuard AI - Main Application Runner
Starts the Flask development server
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Flask app
try:
    from app.main import app
    print("✓ Flask app imported successfully")
except ImportError as e:
    print(f"✗ Error importing Flask app: {e}")
    print("  Make sure Flask is installed: pip install Flask Flask-CORS")
    sys.exit(1)

if __name__ == '__main__':
    # Configuration
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'

    print("")
    print("=" * 50)
    print("CropGuard AI - Disease Detection System")
    print("=" * 50)
    print("")
    print(f"Starting Flask server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print("")
    print("Access the application at:")
    print(f"  http://localhost:{port}")
    print("")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    print("")

    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        sys.exit(1)
