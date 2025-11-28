#!/usr/bin/env python3
"""Quick script to test Elasticsearch password - tries common passwords"""

import sys
import os
sys.path.insert(0, 'src')

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from search import ElasticsearchSetup

def test_password(password=None):
    """Test if password works."""
    try:
        es = ElasticsearchSetup(
            host="localhost",
            port=9200,
            username="elastic",
            password=password
        )
        es_client = es.get_client()
        info = es_client.info()
        print(f"✅ SUCCESS! Elasticsearch is running")
        print(f"   Version: {info.get('version', {}).get('number', 'unknown')}")
        if password:
            print(f"   Password: {password} (works!)")
        else:
            print(f"   No password required!")
        return True
    except Exception as e:
        if password:
            print(f"❌ Password '{password}' doesn't work")
        else:
            print(f"❌ No password connection failed: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    print("Testing Elasticsearch connection...\n")
    
    # Test 1: No password
    print("1. Testing without password...")
    if test_password(None):
        print("\n✅ Your Elasticsearch doesn't require a password!")
        sys.exit(0)
    
    # Test 2: Common default passwords
    common_passwords = ["elastic", "changeme", ""]
    
    print("\n2. Testing common passwords...")
    for pwd in common_passwords:
        if test_password(pwd):
            print(f"\n✅ Found working password: '{pwd}'")
            sys.exit(0)
    
    print("\n❌ None of the common passwords worked.")
    print("\n💡 Your password might be:")
    print("   - Set during Elasticsearch installation")
    print("   - In your Elasticsearch configuration files")
    print("   - Check: C:\\elasticsearch\\elasticsearch-8.17.4\\config\\elasticsearch.yml")
    print("\n💡 Try running: python quick_embedding.py YOUR_PASSWORD")

