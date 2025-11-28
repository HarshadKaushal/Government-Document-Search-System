#!/usr/bin/env python3
"""Simple script to verify Elasticsearch is running and accessible."""

import sys

try:
    import requests
except ImportError:
    print("⚠ requests library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

def check_elasticsearch(host='localhost', port=9200, username=None, password=None):
    """Check if Elasticsearch is running."""
    url = f'http://{host}:{port}'
    print(f"Checking Elasticsearch at {url}...")
    
    try:
        auth = None
        if username and password:
            auth = (username, password)
        
        response = requests.get(url, auth=auth, timeout=10)
        
        if response.status_code == 200:
            info = response.json()
            print("\n✓✓✓ Elasticsearch is running! ✓✓✓")
            print(f"\n  Version: {info.get('version', {}).get('number', 'Unknown')}")
            print(f"  Cluster: {info.get('cluster_name', 'Unknown')}")
            print(f"  Status: {info.get('tagline', 'Unknown')}")
            return True
        elif response.status_code == 401:
            print("\n✗ Authentication required")
            print("  Elasticsearch requires username/password.")
            print("  Try running with credentials:")
            print("    python verify_elasticsearch.py --username elastic --password YOUR_PASSWORD")
            return False
        else:
            print(f"\n✗ Elasticsearch responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to Elasticsearch")
        print("\n  Make sure Elasticsearch is started:")
        print("    cd C:\\elasticsearch\\elasticsearch-8.17.4\\bin")
        print("    .\\elasticsearch.bat")
        return False
    except requests.exceptions.Timeout:
        print("\n✗ Connection timeout")
        print("  Elasticsearch may still be starting up. Wait a bit and try again.")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Verify Elasticsearch is running')
    parser.add_argument('--host', default='localhost', help='Elasticsearch host')
    parser.add_argument('--port', type=int, default=9200, help='Elasticsearch port')
    parser.add_argument('--username', help='Elasticsearch username')
    parser.add_argument('--password', help='Elasticsearch password')
    
    args = parser.parse_args()
    
    is_running = check_elasticsearch(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password
    )
    
    if is_running:
        print("\n" + "="*60)
        print("Ready to index documents!")
        print("="*60)
        print("\nRun:")
        if args.username and args.password:
            print(f"  python src/process_and_index.py --es-username {args.username} --es-password {args.password}")
        else:
            print("  python src/process_and_index.py")
        sys.exit(0)
    else:
        sys.exit(1)

