#!/usr/bin/env python3
"""
Test script to verify username is stored and retrieved correctly in photos
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_creator_photos_with_username():
    """Test that creator photos endpoint returns username"""
    print("Testing /api/creator/photos endpoint...")

    # You'll need to replace this with a valid JWT token for a creator
    # Get token by logging in first
    token = input("Enter your creator JWT token (or press Enter to skip): ").strip()

    if not token:
        print("Skipping test - no token provided")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Get creator's photos
    response = requests.get(f"{BASE_URL}/api/creator/photos", headers=headers)

    if response.status_code == 200:
        photos = response.json()
        print(f"\n✓ Successfully retrieved {len(photos)} photos")

        if photos:
            print("\nFirst photo details:")
            photo = photos[0]
            print(f"  - Title: {photo.get('title')}")
            print(f"  - Username: {photo.get('username')}")
            print(f"  - Creator ID: {photo.get('creator_id')}")

            if photo.get('username'):
                print("\n✓ Username is present in the response!")
            else:
                print("\n✗ Username is missing from the response!")
        else:
            print("\nNo photos found for this creator")
    else:
        print(f"\n✗ Error: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_creator_photos_with_username()
