import requests
import sys
import json
from datetime import datetime
import uuid

class RealEstatePlatformTester:
    def __init__(self, base_url="https://cc953fed-5032-4e42-9944-9f59ff5f3380.preview.emergentagent.com"):
        self.base_url = base_url
        self.tokens = {}  # Store tokens for different user types
        self.users = {}   # Store user data
        self.properties = {}  # Store created properties
        self.interests = {}   # Store created interests
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, user_type=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth token if user_type specified
        if user_type and user_type in self.tokens:
            headers['Authorization'] = f'Bearer {self.tokens[user_type]}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if '/api/auth/login' in endpoint:
                    # Login endpoint uses query parameters
                    response = requests.post(url, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200
        )
        return success

    def test_user_registration(self, user_type, email_suffix=""):
        """Test user registration for different personas"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "email": f"test_{user_type}_{timestamp}{email_suffix}@example.com",
            "phone": f"9876543{timestamp[-3:]}",
            "password": "TestPass123!",
            "user_type": user_type,
            "full_name": f"Test {user_type.title()} {timestamp}"
        }
        
        success, response = self.run_test(
            f"Register {user_type.title()}",
            "POST",
            "/api/auth/register",
            200,
            data=user_data
        )
        
        if success and 'token' in response:
            self.tokens[user_type] = response['token']
            self.users[user_type] = {
                'data': user_data,
                'response': response['user']
            }
            return True
        return False

    def test_user_login(self, user_type):
        """Test user login"""
        if user_type not in self.users:
            print(f"❌ No user data for {user_type}")
            return False
            
        email = self.users[user_type]['data']['email']
        password = self.users[user_type]['data']['password']
        
        success, response = self.run_test(
            f"Login {user_type.title()}",
            "POST",
            f"/api/auth/login?email={email}&password={password}",
            200
        )
        
        if success and 'token' in response:
            self.tokens[user_type] = response['token']
            return True
        return False

    def test_get_user_profile(self, user_type):
        """Test getting user profile"""
        success, response = self.run_test(
            f"Get {user_type.title()} Profile",
            "GET",
            "/api/user/profile",
            200,
            user_type=user_type
        )
        return success

    def test_update_user_profile(self, user_type):
        """Test updating user profile"""
        profile_data = {
            "full_name": f"Updated {user_type.title()} Name",
            "phone": "9876543210"
        }
        
        # Add user-type specific fields
        if user_type == "dealer":
            profile_data.update({
                "office_address": "123 Business Street, City",
                "areas_served": ["Mumbai", "Pune", "Delhi"]
            })
        elif user_type == "tenant":
            profile_data.update({
                "current_address": "456 Current Street, City",
                "permanent_address": "789 Permanent Street, City"
            })
        elif user_type == "owner":
            profile_data["address"] = "321 Owner Street, City"
        
        success, response = self.run_test(
            f"Update {user_type.title()} Profile",
            "PUT",
            "/api/user/profile",
            200,
            data=profile_data,
            user_type=user_type
        )
        return success

    def test_create_property(self, user_type):
        """Test property creation (owners and dealers only)"""
        if user_type == "tenant":
            print(f"⏭️  Skipping property creation for {user_type}")
            return True
            
        property_data = {
            "title": f"Test Property by {user_type.title()}",
            "description": "A beautiful test property with all modern amenities",
            "property_type": "apartment",
            "size": "2 BHK",
            "rent": 25000.0,
            "location": "Mumbai, Maharashtra",
            "amenities": ["Parking", "Gym", "Swimming Pool"],
            "images": []
        }
        
        success, response = self.run_test(
            f"Create Property ({user_type.title()})",
            "POST",
            "/api/properties",
            200,
            data=property_data,
            user_type=user_type
        )
        
        if success and 'property_id' in response:
            self.properties[user_type] = response['property_id']
            return True
        return False

    def test_get_properties(self, user_type):
        """Test getting properties"""
        success, response = self.run_test(
            f"Get Properties ({user_type.title()})",
            "GET",
            "/api/properties",
            200,
            user_type=user_type
        )
        return success

    def test_get_property_details(self, user_type):
        """Test getting specific property details"""
        if user_type == "tenant":
            # Use property created by owner or dealer
            property_id = self.properties.get("owner") or self.properties.get("dealer")
        else:
            property_id = self.properties.get(user_type)
            
        if not property_id:
            print(f"⏭️  No property available for testing property details")
            return True
            
        success, response = self.run_test(
            f"Get Property Details ({user_type.title()})",
            "GET",
            f"/api/properties/{property_id}",
            200,
            user_type=user_type
        )
        return success

    def test_property_search(self, user_type):
        """Test property search with filters"""
        success, response = self.run_test(
            f"Search Properties ({user_type.title()})",
            "GET",
            "/api/properties?location=Mumbai&min_rent=20000&max_rent=30000&property_type=apartment",
            200,
            user_type=user_type
        )
        return success

    def test_kyc_verification(self, user_type):
        """Test KYC verification (tenants only)"""
        if user_type != "tenant":
            print(f"⏭️  Skipping KYC verification for {user_type}")
            return True
            
        kyc_data = {
            "aadhaar_number": "1234 5678 9012",
            "pan_number": "ABCDE1234F",
            "selfie_image": "mock_base64_image_data",
            "employer_name": "Tata Consultancy Services"
        }
        
        success, response = self.run_test(
            f"KYC Verification ({user_type.title()})",
            "POST",
            "/api/kyc/verify",
            200,
            data=kyc_data,
            user_type=user_type
        )
        return success

    def test_express_interest(self, user_type):
        """Test expressing interest in property (tenants only)"""
        if user_type != "tenant":
            print(f"⏭️  Skipping express interest for {user_type}")
            return True
            
        # Use property created by owner or dealer
        property_id = self.properties.get("owner") or self.properties.get("dealer")
        if not property_id:
            print(f"⏭️  No property available for expressing interest")
            return True
            
        interest_data = {
            "property_id": property_id,
            "message": "I am interested in this property. Please contact me."
        }
        
        success, response = self.run_test(
            f"Express Interest ({user_type.title()})",
            "POST",
            f"/api/properties/{property_id}/interest",
            200,
            data=interest_data,
            user_type=user_type
        )
        
        if success and 'interest_id' in response:
            self.interests[user_type] = response['interest_id']
            return True
        return False

    def test_get_interests(self, user_type):
        """Test getting interests"""
        success, response = self.run_test(
            f"Get Interests ({user_type.title()})",
            "GET",
            "/api/interests",
            200,
            user_type=user_type
        )
        return success

    def test_respond_to_interest(self, user_type):
        """Test responding to interest (owners and dealers only)"""
        if user_type == "tenant":
            print(f"⏭️  Skipping respond to interest for {user_type}")
            return True
            
        interest_id = self.interests.get("tenant")
        if not interest_id:
            print(f"⏭️  No interest available for responding")
            return True
            
        # Test approval
        success, response = self.run_test(
            f"Respond to Interest - Approve ({user_type.title()})",
            "PUT",
            f"/api/interests/{interest_id}/respond",
            200,
            data={"response": "approved"},
            user_type=user_type
        )
        return success

    def test_dashboard_stats(self, user_type):
        """Test getting dashboard statistics"""
        success, response = self.run_test(
            f"Get Dashboard Stats ({user_type.title()})",
            "GET",
            "/api/dashboard/stats",
            200,
            user_type=user_type
        )
        return success

    def run_comprehensive_test(self):
        """Run comprehensive test suite for all personas"""
        print("🚀 Starting Comprehensive Real Estate Platform API Testing")
        print("=" * 60)
        
        # Test health check first
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return False
            
        user_types = ["owner", "dealer", "tenant"]
        
        # Test user registration and authentication
        print("\n📝 Testing User Registration & Authentication")
        for user_type in user_types:
            if not self.test_user_registration(user_type):
                print(f"❌ Registration failed for {user_type}, stopping tests")
                return False
                
            if not self.test_user_login(user_type):
                print(f"❌ Login failed for {user_type}, stopping tests")
                return False
        
        # Test profile management
        print("\n👤 Testing Profile Management")
        for user_type in user_types:
            self.test_get_user_profile(user_type)
            self.test_update_user_profile(user_type)
        
        # Test property management
        print("\n🏠 Testing Property Management")
        for user_type in user_types:
            self.test_create_property(user_type)
            self.test_get_properties(user_type)
            self.test_get_property_details(user_type)
            self.test_property_search(user_type)
        
        # Test KYC verification
        print("\n🔐 Testing KYC Verification")
        self.test_kyc_verification("tenant")
        
        # Test interest system
        print("\n💝 Testing Interest System")
        self.test_express_interest("tenant")
        for user_type in user_types:
            self.test_get_interests(user_type)
        self.test_respond_to_interest("owner")
        
        # Test dashboard statistics
        print("\n📊 Testing Dashboard Statistics")
        for user_type in user_types:
            self.test_dashboard_stats(user_type)
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Final Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend is working correctly.")
            return True
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} tests failed. Backend needs attention.")
            return False

def main():
    tester = RealEstatePlatformTester()
    success = tester.run_comprehensive_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())