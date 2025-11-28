#!/usr/bin/env python3
"""
Run the Flask web server for the document search interface.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    
    print("=" * 60)
    print("Government Document Search - Web Interface")
    print("=" * 60)
    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)

