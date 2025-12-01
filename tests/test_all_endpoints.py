"""
Comprehensive API Endpoint Test Script
Tests all endpoints to ensure they work correctly
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

test_results = {
    'passed': 0,
    'failed': 0,
    'total': 0,
    'failures': []
}

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")

def test_endpoint(name, method, url, expected_status, headers=None, data=None, auth=False):
    """Test a single endpoint"""
    global test_results
    test_results['total'] += 1

    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code == expected_status:
            print(f"{GREEN}PASS{RESET} {name}: {response.status_code}")
            test_results['passed'] += 1
            return response
        else:
            print(f"{RED}FAIL{RESET} {name}: Expected {expected_status}, got {response.status_code}")
            test_results['failed'] += 1
            test_results['failures'].append({
                'name': name,
                'expected': expected_status,
                'got': response.status_code,
                'response': response.text[:200]
            })
            return None
    except Exception as e:
        print(f"{RED}FAIL{RESET} {name}: Exception - {str(e)}")
        test_results['failed'] += 1
        test_results['failures'].append({
            'name': name,
            'error': str(e)
        })
        return None

def main():
    """Run all endpoint tests"""
    print_header("SegurifAI x PAQ - API Endpoint Test Suite")
    print(f"Testing: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Store access token
    access_token = None

    # Test Authentication
    print_header("1. Authentication Endpoints")

    # Login
    response = test_endpoint(
        "Login with user credentials",
        "POST",
        f"{BASE_URL}/api/auth/token/",
        200,
        data={"email": "user1@example.com", "password": "User123!"}
    )
    if response:
        tokens = response.json()
        access_token = tokens.get('access')
        print(f"  > Access token obtained")

    # Verify token
    if access_token:
        test_endpoint(
            "Verify access token",
            "POST",
            f"{BASE_URL}/api/auth/token/verify/",
            200,
            data={"token": access_token}
        )

    # Test Public Endpoints
    print_header("2. Public Endpoints (No Auth Required)")

    test_endpoint(
        "Get all service categories",
        "GET",
        f"{BASE_URL}/api/services/categories/",
        200
    )

    test_endpoint(
        "Get all service plans",
        "GET",
        f"{BASE_URL}/api/services/plans/",
        200
    )

    test_endpoint(
        "Get featured service plans",
        "GET",
        f"{BASE_URL}/api/services/plans/featured/",
        200
    )

    test_endpoint(
        "Get all providers",
        "GET",
        f"{BASE_URL}/api/providers/",
        200
    )

    test_endpoint(
        "Get available providers",
        "GET",
        f"{BASE_URL}/api/providers/available/",
        200
    )

    # Test User Registration
    print_header("3. User Registration")

    test_endpoint(
        "Register new user",
        "POST",
        f"{BASE_URL}/api/users/register/",
        201,
        data={
            "email": f"testuser{datetime.now().timestamp()}@example.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
            "phone_number": "+525599999999"
        }
    )

    # Test Authenticated Endpoints
    if access_token:
        headers = {"Authorization": f"Bearer {access_token}"}

        print_header("4. User Profile Endpoints (Authenticated)")

        test_endpoint(
            "Get my profile",
            "GET",
            f"{BASE_URL}/api/users/me/",
            200,
            headers=headers
        )

        test_endpoint(
            "Update my profile",
            "PUT",
            f"{BASE_URL}/api/users/me/",
            200,
            headers=headers,
            data={
                "first_name": "Updated",
                "last_name": "Name",
                "phone_number": "+525511111111"
            }
        )

        print_header("5. Service Subscription Endpoints")

        test_endpoint(
            "Get my subscriptions",
            "GET",
            f"{BASE_URL}/api/services/user-services/",
            200,
            headers=headers
        )

        print_header("6. Assistance Request Endpoints")

        test_endpoint(
            "Get my assistance requests",
            "GET",
            f"{BASE_URL}/api/assistance/requests/",
            200,
            headers=headers
        )

        test_endpoint(
            "Get pending assistance requests",
            "GET",
            f"{BASE_URL}/api/assistance/requests/pending/",
            200,
            headers=headers
        )

        test_endpoint(
            "Get active assistance requests",
            "GET",
            f"{BASE_URL}/api/assistance/requests/active/",
            200,
            headers=headers
        )

        print_header("7. PAQ Wallet Endpoints")

        # Wallet endpoints might return error if no wallet ID
        test_endpoint(
            "Get wallet transaction history",
            "GET",
            f"{BASE_URL}/api/wallet/history/",
            200,
            headers=headers
        )

        test_endpoint(
            "Get all wallet transactions",
            "GET",
            f"{BASE_URL}/api/wallet/transactions/",
            200,
            headers=headers
        )

        print_header("8. Provider Review Endpoints")

        test_endpoint(
            "Get provider reviews",
            "GET",
            f"{BASE_URL}/api/providers/reviews/",
            200,
            headers=headers
        )

        print_header("9. Request Updates Endpoints")

        test_endpoint(
            "Get request updates",
            "GET",
            f"{BASE_URL}/api/assistance/updates/",
            200,
            headers=headers
        )

    # Test Admin Endpoints
    print_header("10. Admin Endpoints")

    # Login as admin
    response = test_endpoint(
        "Login with admin credentials",
        "POST",
        f"{BASE_URL}/api/auth/token/",
        200,
        data={"email": "admin@segurifai.com", "password": "Admin123!"}
    )

    if response:
        admin_token = response.json().get('access')
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        test_endpoint(
            "Get all users (admin only)",
            "GET",
            f"{BASE_URL}/api/users/",
            200,
            headers=admin_headers
        )

        test_endpoint(
            "Get specific category details",
            "GET",
            f"{BASE_URL}/api/services/categories/1/",
            200,
            headers=admin_headers
        )

        test_endpoint(
            "Get specific plan details",
            "GET",
            f"{BASE_URL}/api/services/plans/1/",
            200,
            headers=admin_headers
        )

        test_endpoint(
            "Get specific provider details",
            "GET",
            f"{BASE_URL}/api/providers/1/",
            200,
            headers=admin_headers
        )

    # Test API Documentation
    print_header("11. API Documentation Endpoints")

    test_endpoint(
        "OpenAPI Schema",
        "GET",
        f"{BASE_URL}/api/schema/",
        200
    )

    # Print Summary
    print_header("Test Results Summary")

    total = test_results['total']
    passed = test_results['passed']
    failed = test_results['failed']
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"Total Tests:  {total}")
    print(f"{GREEN}Passed:       {passed}{RESET}")
    print(f"{RED}Failed:       {failed}{RESET}")
    print(f"Pass Rate:    {pass_rate:.1f}%")

    if failed > 0:
        print(f"\n{RED}Failed Tests:{RESET}")
        for failure in test_results['failures']:
            print(f"\n  - {failure['name']}")
            if 'expected' in failure:
                print(f"    Expected: {failure['expected']}, Got: {failure['got']}")
                if 'response' in failure:
                    print(f"    Response: {failure['response']}")
            if 'error' in failure:
                print(f"    Error: {failure['error']}")

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"Testing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Return exit code
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        exit(1)
    except Exception as e:
        print(f"\n{RED}Fatal error: {str(e)}{RESET}")
        exit(1)
