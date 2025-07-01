#!/usr/bin/env python3
"""
Test if Canvas Editor server is running
"""

import requests
import time

def test_server():
    """Test if Canvas Editor is accessible"""
    url = "http://localhost:8554"
    
    print("🔍 Testing Canvas Editor server...")
    
    try:
        # Try to connect
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ Canvas Editor is running at {url}")
            print(f"   Status: {response.status_code}")
            print(f"   Content length: {len(response.content)} bytes")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Canvas Editor server")
        print("   Make sure web_launch.py is running")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Server connection timed out")
        return False
        
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    if success:
        print("\n🎉 Canvas Editor is ready!")
        print("   Open http://localhost:8554 in your browser")
    else:
        print("\n💡 Start the server with: python3 web_launch.py")