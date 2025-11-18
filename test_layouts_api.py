#!/usr/bin/env python3
"""Test script to verify layouts API endpoints are working."""

import requests
import json

def test_layouts_api():
    """Test the layouts API endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Layouts API Endpoints")
    print("=" * 50)
    
    # Test 1: Get presets
    print("\n1. Testing GET /api/v1/layouts/presets")
    try:
        response = requests.get(f"{base_url}/api/v1/layouts/presets")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Found {len(data.get('presets', []))} presets")
            if data.get('presets'):
                first_preset = data['presets'][0]
                print(f"   📋 First preset: {first_preset.get('name')} ({first_preset.get('id')})")
        else:
            print(f"   ❌ Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the backend running?")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get project layout
    print("\n2. Testing GET /api/v1/layouts/project/test-project/layout")
    try:
        response = requests.get(f"{base_url}/api/v1/layouts/project/test-project/layout")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Layout ID: {data.get('layout_id')}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the backend running?")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Update project layout
    print("\n3. Testing PUT /api/v1/layouts/project/test-project/layout")
    test_layout = {
        "layout_id": "layout-002",
        "header_style": "cover",
        "grid_pattern": "masonry-portrait",
        "color_theme": "grey"
    }
    try:
        response = requests.put(
            f"{base_url}/api/v1/layouts/project/test-project/layout",
            json=test_layout
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Message: {data.get('message')}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed - is the backend running?")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\n💡 To run this test:")
    print("   1. Start the backend: python -m uvicorn main:app --reload")
    print("   2. Run this script: python test_layouts_api.py")

if __name__ == "__main__":
    test_layouts_api()