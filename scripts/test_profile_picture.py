#!/usr/bin/env python3
"""
Test script for profile picture functionality
This script tests:
1. User registration
2. User login
3. Profile picture upload
4. Profile picture retrieval
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Test user credentials
TEST_USER = {
    "email": f"testuser_{Path(__file__).stem}@example.com",
    "username": f"testuser_{Path(__file__).stem}",
    "password": "TestPassword123!"
}


def print_step(message):
    """Print a test step message"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")


def print_result(success, message):
    """Print test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")


def test_register_user():
    """Test user registration"""
    print_step("Step 1: Register a new user")

    try:
        response = requests.post(
            f"{API_BASE}/auth/register-consumer",
            json=TEST_USER
        )

        if response.status_code == 201:
            data = response.json()
            print_result(True, f"User registered successfully: {data['username']}")
            print(f"   User ID: {data['id']}")
            print(f"   Email: {data['email']}")
            print(f"   Profile Picture URL: {data.get('profile_picture_url', 'None')}")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print_result(True, "User already exists (this is OK for testing)")
            return True
        else:
            print_result(False, f"Registration failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print_result(False, f"Registration error: {str(e)}")
        return False


def test_login_user():
    """Test user login and get access token"""
    print_step("Step 2: Login user")

    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_result(True, "User logged in successfully")
            print(f"   Access Token: {token[:20]}...")
            return token
        else:
            print_result(False, f"Login failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print_result(False, f"Login error: {str(e)}")
        return None


def test_upload_profile_picture(token):
    """Test profile picture upload"""
    print_step("Step 3: Upload profile picture")

    # Create a temporary test image file
    try:
        from PIL import Image
        import io

        # Create a simple 400x400 test image
        img = Image.new('RGB', (400, 400), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {
            'file': ('test_profile.jpg', img_bytes, 'image/jpeg')
        }

        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(
            f"{API_BASE}/auth/profile-picture",
            files=files,
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            profile_url = data.get('profile_picture_url')
            print_result(True, "Profile picture uploaded successfully")
            print(f"   Profile Picture URL: {profile_url}")
            return profile_url
        else:
            print_result(False, f"Upload failed: {response.status_code} - {response.text}")
            return None

    except ImportError:
        print_result(False, "PIL (Pillow) not installed. Install with: pip install Pillow")
        return None
    except Exception as e:
        print_result(False, f"Upload error: {str(e)}")
        return None


def test_get_user_profile(token):
    """Test retrieving user profile with profile picture"""
    print_step("Step 4: Retrieve user profile")

    try:
        headers = {
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(
            f"{API_BASE}/auth/me",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            profile_url = data.get('profile_picture_url')
            print_result(True, "User profile retrieved successfully")
            print(f"   Username: {data['username']}")
            print(f"   Email: {data['email']}")
            print(f"   Profile Picture URL: {profile_url}")

            # Verify the profile picture URL is valid
            if profile_url:
                print("\n   Testing if profile picture URL is accessible...")
                try:
                    img_response = requests.head(profile_url)
                    if img_response.status_code == 200:
                        print_result(True, "Profile picture URL is accessible")
                        return True
                    else:
                        print_result(False, f"Profile picture URL not accessible: {img_response.status_code}")
                        return False
                except Exception as e:
                    print_result(False, f"Error checking URL: {str(e)}")
                    return False
            else:
                print_result(False, "No profile picture URL found")
                return False
        else:
            print_result(False, f"Profile retrieval failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print_result(False, f"Profile retrieval error: {str(e)}")
        return False


def test_list_all_profile_pictures():
    """Test listing all profile pictures (public endpoint)"""
    print_step("Step 5: List all profile pictures (all users)")

    try:
        # Test without filter (all users)
        response = requests.get(f"{API_BASE}/auth/profile-pictures")

        if response.status_code == 200:
            data = response.json()
            print_result(True, "Profile pictures list retrieved successfully")
            print(f"   Total users: {data['total']}")
            print(f"   Page: {data['page']}")
            print(f"   Page size: {data['page_size']}")
            print(f"   Has next page: {data['has_next']}")
            print(f"   Users in this page: {len(data['users'])}")

            if data['users']:
                print("\n   Sample users:")
                for user in data['users'][:3]:  # Show first 3 users
                    print(f"     - {user['username']}: {user.get('profile_picture_url', 'No picture')}")

            return True
        else:
            print_result(False, f"List retrieval failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print_result(False, f"List retrieval error: {str(e)}")
        return False


def test_list_only_with_pictures():
    """Test listing only users with profile pictures"""
    print_step("Step 6: List only users with profile pictures")

    try:
        response = requests.get(
            f"{API_BASE}/auth/profile-pictures",
            params={"with_pictures_only": True}
        )

        if response.status_code == 200:
            data = response.json()
            print_result(True, "Filtered profile pictures list retrieved successfully")
            print(f"   Total users with pictures: {data['total']}")
            print(f"   Users in this page: {len(data['users'])}")

            # Verify all users have profile pictures
            all_have_pictures = all(user.get('profile_picture_url') for user in data['users'])

            if all_have_pictures or len(data['users']) == 0:
                print_result(True, "All returned users have profile pictures")
                if data['users']:
                    print("\n   Users with profile pictures:")
                    for user in data['users'][:5]:  # Show first 5 users
                        print(f"     - {user['username']}")
                        print(f"       Picture: {user['profile_picture_url'][:50]}...")
                return True
            else:
                print_result(False, "Some users without profile pictures were returned")
                return False
        else:
            print_result(False, f"Filtered list retrieval failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print_result(False, f"Filtered list retrieval error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  PROFILE PICTURE FUNCTIONALITY TEST")
    print("="*60)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print_result(False, f"Server not responding correctly: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print_result(False, f"Cannot connect to server at {BASE_URL}: {str(e)}")
        print("\nMake sure the server is running with: python -m uvicorn app.main:app --reload")
        sys.exit(1)

    print_result(True, f"Server is running at {BASE_URL}")

    # Run tests
    test_results = []

    # Test 1: Register user
    test_results.append(test_register_user())

    # Test 2: Login user
    token = test_login_user()
    test_results.append(token is not None)

    if not token:
        print_result(False, "Cannot continue without valid token")
        sys.exit(1)

    # Test 3: Upload profile picture
    profile_url = test_upload_profile_picture(token)
    test_results.append(profile_url is not None)

    # Test 4: Get user profile and verify profile picture
    test_results.append(test_get_user_profile(token))

    # Test 5: List all profile pictures (public endpoint)
    test_results.append(test_list_all_profile_pictures())

    # Test 6: List only users with profile pictures
    test_results.append(test_list_only_with_pictures())

    # Print summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    passed = sum(test_results)
    total = len(test_results)
    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print_result(True, "All tests passed! Profile picture functionality is working.")
        sys.exit(0)
    else:
        print_result(False, f"{total - passed} test(s) failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
