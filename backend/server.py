from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
import os
import json
import time
import random
from pymongo import MongoClient

# Environment variables
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def generate_token(user_id: str) -> str:
    return f"token_{user_id}_{int(time.time())}"

# Database setup
client = MongoClient(MONGO_URL)
db = client.realestate_db

# Initialize database collections with indexes
def initialize_database():
    """Initialize database collections and create indexes for better performance"""
    try:
        # Create indexes for users collection
        db.users.create_index("email", unique=True)
        db.users.create_index("user_id", unique=True)
        db.users.create_index("user_type")
        db.users.create_index("created_at")
        
        # Create indexes for properties collection
        db.properties.create_index("property_id", unique=True)
        db.properties.create_index("owner_id")
        db.properties.create_index("status")
        db.properties.create_index("location")
        db.properties.create_index("rent")
        db.properties.create_index("property_type")
        
        # Create indexes for interests collection
        db.property_interests.create_index("interest_id", unique=True)
        db.property_interests.create_index("property_id")
        db.property_interests.create_index("tenant_id")
        db.property_interests.create_index("owner_id")
        db.property_interests.create_index("status")
        
        print("✅ Database indexes created successfully")
        
        # Seed sample data if collections are empty
        seed_sample_data()
        
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}")

def seed_sample_data():
    """Seed the database with sample users and properties"""
    try:
        # Check if we already have data
        existing_users = db.users.count_documents({})
        if existing_users > 0:
            print(f"✅ Database already contains {existing_users} users")
            return
        
        print("🌱 Seeding sample data...")
        
        # Clear existing data first
        db.users.delete_many({})
        db.properties.delete_many({})
        db.property_interests.delete_many({})
        
        # Sample users for each persona (including admin)
        sample_users = [
            {
                "user_id": str(uuid.uuid4()),
                "email": "admin@realestate.com",
                "phone": "+91-9999999999",
                "password": hash_password("admin123"),
                "user_type": "admin",
                "full_name": "Platform Administrator",
                "profile_completed": True,
                "kyc_completed": True,
                "profile": {
                    "full_name": "Platform Administrator",
                    "phone": "+91-9999999999",
                    "address": "Admin Office, Cyber City, Gurugram"
                },
                "created_at": datetime.now().isoformat()
            },
            {
                "user_id": str(uuid.uuid4()),
                "email": "john.owner@realestate.com",
                "phone": "+91-9876543201",
                "password": hash_password("password123"),
                "user_type": "owner",
                "full_name": "John Property Owner",
                "profile_completed": True,
                "kyc_completed": True,
                "profile": {
                    "full_name": "John Property Owner",
                    "phone": "+91-9876543201",
                    "address": "123 Owner Street, Gurugram, Haryana"
                },
                "created_at": datetime.now().isoformat()
            },
            {
                "user_id": str(uuid.uuid4()),
                "email": "sarah.dealer@realestate.com", 
                "phone": "+91-9876543202",
                "password": hash_password("password123"),
                "user_type": "dealer",
                "full_name": "Sarah Real Estate Dealer",
                "profile_completed": True,
                "kyc_completed": True,
                "profile": {
                    "full_name": "Sarah Real Estate Dealer",
                    "phone": "+91-9876543202",
                    "office_address": "456 Business Plaza, DLF Phase 1, Gurugram",
                    "areas_served": ["Gurugram", "Delhi", "Noida", "Faridabad"]
                },
                "created_at": datetime.now().isoformat()
            },
            {
                "user_id": str(uuid.uuid4()),
                "email": "alex.tenant@realestate.com",
                "phone": "+91-9876543203", 
                "password": hash_password("password123"),
                "user_type": "tenant",
                "full_name": "Alex Tenant User",
                "profile_completed": True,
                "kyc_completed": True,
                "profile": {
                    "full_name": "Alex Tenant User",
                    "phone": "+91-9876543203",
                    "current_address": "789 Tenant Colony, Sector 45, Gurugram",
                    "permanent_address": "321 Home Town, Delhi",
                    "employment_type": "salaried",
                    "monthly_income": "75000-100000"
                },
                "kyc_results": {
                    "aadhaar_verification": {"status": "verified", "name": "Alex Tenant User"},
                    "pan_verification": {"status": "verified", "name": "Alex Tenant User"},
                    "face_match": {"status": "match", "match_score": 95.5},
                    "employer_verification": {"company_found": True, "company_name": "Infosys Limited"}
                },
                "created_at": datetime.now().isoformat()
            },
            {
                "user_id": str(uuid.uuid4()),
                "email": "priya.tenant@realestate.com",
                "phone": "+91-9876543204",
                "password": hash_password("password123"),
                "user_type": "tenant", 
                "full_name": "Priya Tenant",
                "profile_completed": True,
                "kyc_completed": False,
                "profile": {
                    "full_name": "Priya Tenant",
                    "phone": "+91-9876543204",
                    "current_address": "101 Tech Park, Sector 62, Gurugram",
                    "permanent_address": "567 Village Road, Delhi",
                    "employment_type": "self_employed",
                    "monthly_income": "30000-75000"
                },
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Insert sample users
        db.users.insert_many(sample_users)
        
        # Get user IDs for property creation
        owner_user = db.users.find_one({"user_type": "owner"})
        dealer_user = db.users.find_one({"user_type": "dealer"})
        
        # Sample properties with real names from Gurugram and Delhi
        sample_properties = [
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": owner_user["user_id"],
                "title": "Adani Oysters Grande - 3BHK Premium Apartment",
                "description": "Luxury 3BHK apartment in prestigious Adani Oysters Grande with world-class amenities, spacious rooms, and prime location in Sector 102, Gurugram.",
                "property_type": "apartment",
                "bhk": "3",
                "area_size": "1850",
                "area_unit": "sqft",
                "rent": 45000.0,
                "location": "Adani Oysters Grande, Sector 102, Gurugram, Haryana",
                "google_location": {
                    "place_id": "mock_place_id_1",
                    "formatted_address": "Adani Oysters Grande, Sector 102, Gurugram, Haryana 122006",
                    "geometry": {"lat": 28.4354, "lng": 77.0428}
                },
                "latitude": 28.4354,
                "longitude": 77.0428,
                "amenities": ["Swimming Pool", "Gym", "Parking", "Security", "Club House", "Garden"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": owner_user["user_id"],
                "title": "ATS Triumph - 2BHK Modern Apartment",
                "description": "Beautiful 2BHK apartment in ATS Triumph with contemporary design, excellent ventilation, and great connectivity to Delhi NCR.",
                "property_type": "apartment",
                "bhk": "2",
                "area_size": "1250",
                "area_unit": "sqft",
                "rent": 32000.0,
                "location": "ATS Triumph, Sector 104, Gurugram, Haryana", 
                "google_location": {
                    "place_id": "mock_place_id_2",
                    "formatted_address": "ATS Triumph, Sector 104, Gurugram, Haryana 122006",
                    "geometry": {"lat": 28.4296, "lng": 77.0474}
                },
                "latitude": 28.4296,
                "longitude": 77.0474,
                "amenities": ["Gym", "Parking", "Wi-Fi Ready", "Security", "Power Backup"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": dealer_user["user_id"],
                "title": "Emaar Palm Hills - 4BHK Luxury Villa",
                "description": "Spacious 4BHK villa in premium Emaar Palm Hills with private garden, modern amenities, and serene environment perfect for families.",
                "property_type": "house",
                "bhk": "4",
                "area_size": "2800",
                "area_unit": "sqft",
                "rent": 75000.0,
                "location": "Emaar Palm Hills, Sector 77, Gurugram, Haryana",
                "google_location": {
                    "place_id": "mock_place_id_3",
                    "formatted_address": "Emaar Palm Hills, Sector 77, Gurugram, Haryana 122102",
                    "geometry": {"lat": 28.3912, "lng": 77.0597}
                },
                "latitude": 28.3912,
                "longitude": 77.0597,
                "amenities": ["Private Garden", "Swimming Pool", "Club House", "Parking", "Security", "Gym"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": dealer_user["user_id"],
                "title": "Emaar Digi Homes - 1BHK Smart Apartment",
                "description": "Modern 1BHK smart apartment in Emaar Digi Homes with IoT features, optimal for working professionals seeking connectivity and convenience.",
                "property_type": "apartment",
                "bhk": "1",
                "area_size": "650",
                "area_unit": "sqft",
                "rent": 22000.0,
                "location": "Emaar Digi Homes, Sector 62, Gurugram, Haryana",
                "google_location": {
                    "place_id": "mock_place_id_4",
                    "formatted_address": "Emaar Digi Homes, Sector 62, Gurugram, Haryana 122102",
                    "geometry": {"lat": 28.3844, "lng": 77.0467}
                },
                "latitude": 28.3844,
                "longitude": 77.0467,
                "amenities": ["Smart Home Features", "Wi-Fi", "Gym", "Parking", "Security"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": owner_user["user_id"],
                "title": "DLF Park Place - 3BHK Premium Apartment",
                "description": "Elegant 3BHK apartment in DLF Park Place with panoramic city views, premium finishes, and access to exclusive amenities.",
                "property_type": "apartment",
                "bhk": "3",
                "area_size": "1950",
                "area_unit": "sqft",
                "rent": 55000.0,
                "location": "DLF Park Place, Sector 54, Gurugram, Haryana",
                "google_location": {
                    "place_id": "mock_place_id_5",
                    "formatted_address": "DLF Park Place, Sector 54, Gurugram, Haryana 122002",
                    "geometry": {"lat": 28.4421, "lng": 77.0694}
                },
                "latitude": 28.4421,
                "longitude": 77.0694,
                "amenities": ["Swimming Pool", "Gym", "Club House", "Parking", "Security", "Shopping Mall"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Insert sample properties
        db.properties.insert_many(sample_properties)
        
        print(f"✅ Seeded {len(sample_users)} users and {len(sample_properties)} properties")
        
    except Exception as e:
        print(f"⚠️ Error seeding sample data: {e}")

app = FastAPI(title="RealEstate Platform API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and create sample data on startup"""
    initialize_database()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if not token.startswith("token_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    parts = token.split("_")
    if len(parts) < 3:
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    user_id = parts[1]
    user = db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    phone: str
    password: str
    user_type: str  # owner, dealer, tenant
    full_name: str
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove any non-numeric characters for validation
        numeric_phone = ''.join(filter(str.isdigit, v))
        if len(numeric_phone) < 10 or len(numeric_phone) > 12:
            raise ValueError('Phone number must be between 10-12 digits')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v) > 40:
            raise ValueError('Full name must be maximum 40 characters')
        return v.strip()

class UserProfile(BaseModel):
    full_name: str
    phone: str
    address: Optional[str] = None
    areas_served: Optional[List[str]] = None  # For dealers
    office_address: Optional[str] = None  # For dealers
    current_address: Optional[str] = None  # For tenants
    permanent_address: Optional[str] = None  # For tenants
    employment_type: Optional[str] = None  # For tenants: salaried, self_employed
    monthly_income: Optional[str] = None  # For tenants: income range
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove any non-numeric characters for validation
        numeric_phone = ''.join(filter(str.isdigit, v))
        if len(numeric_phone) < 10 or len(numeric_phone) > 12:
            raise ValueError('Phone number must be between 10-12 digits')
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if len(v) > 40:
            raise ValueError('Full name must be maximum 40 characters')
        return v.strip()

class Property(BaseModel):
    title: str
    description: str
    property_type: str  # apartment, house, commercial
    bhk: Optional[str] = None  # 1, 2, 3, 4, 5, 6 BHK
    area_size: Optional[str] = None  # Numeric value
    area_unit: Optional[str] = None  # sqft, sqyard
    rent: float
    location: str
    google_location: Optional[Dict[str, Any]] = None  # Mock Google location data
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    amenities: List[str] = []
    images: List[str] = []

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    bhk: Optional[str] = None
    area_size: Optional[str] = None
    area_unit: Optional[str] = None
    rent: Optional[float] = None
    location: Optional[str] = None
    google_location: Optional[Dict[str, Any]] = None
    amenities: Optional[List[str]] = None
    images: Optional[str] = None

class KYCDocuments(BaseModel):
    aadhaar_number: str
    pan_number: str
    selfie_image: str  # base64 encoded
    employer_name: Optional[str] = None

class PropertyInterest(BaseModel):
    property_id: str
    message: Optional[str] = None

class DealApplication(BaseModel):
    property_id: str
    tenant_id: str
    message: str
    monthly_rent: float

# Mock services
def mock_geocode(address: str) -> Dict[str, float]:
    """Mock Google Maps geocoding"""
    # Return mock coordinates for popular Indian cities
    mock_locations = {
        "mumbai": {"lat": 19.0760, "lng": 72.8777},
        "delhi": {"lat": 28.7041, "lng": 77.1025},
        "bangalore": {"lat": 12.9716, "lng": 77.5946},
        "hyderabad": {"lat": 17.3850, "lng": 78.4867},
        "pune": {"lat": 18.5204, "lng": 73.8567},
        "chennai": {"lat": 13.0827, "lng": 80.2707}
    }
    
    city = address.lower()
    for key in mock_locations:
        if key in city:
            return mock_locations[key]
    
    # Random coordinates for other locations
    return {
        "lat": 28.7041 + random.uniform(-5, 5),
        "lng": 77.1025 + random.uniform(-5, 5)
    }

def mock_karza_verify_aadhaar(aadhaar_number: str) -> Dict[str, Any]:
    """Mock Karza Aadhaar verification"""
    time.sleep(1)  # Simulate API delay
    return {
        "status": "verified",
        "name": "Mock User Name",
        "gender": "M",
        "address": "Mock Address, City, State",
        "verification_id": str(uuid.uuid4())
    }

def mock_karza_verify_pan(pan_number: str) -> Dict[str, Any]:
    """Mock Karza PAN verification"""
    time.sleep(1)
    return {
        "status": "verified",
        "name": "Mock User Name",
        "category": "Individual",
        "verification_id": str(uuid.uuid4())
    }

def mock_karza_face_match(selfie_base64: str, aadhaar_photo: str) -> Dict[str, Any]:
    """Mock Karza face matching"""
    time.sleep(2)
    return {
        "match_score": random.uniform(85, 98),
        "status": "match" if random.random() > 0.1 else "no_match",
        "verification_id": str(uuid.uuid4())
    }

def mock_digilocker_fetch_docs(aadhaar_number: str) -> Dict[str, Any]:
    """Mock DigiLocker document fetch"""
    time.sleep(1)
    return {
        "documents": [
            {"type": "aadhaar", "id": "AADHAAR123", "status": "available"},
            {"type": "driving_license", "id": "DL456", "status": "available"},
            {"type": "voter_id", "id": "VOTER789", "status": "available"}
        ]
    }

def mock_mca_employer_verify(employer_name: str) -> Dict[str, Any]:
    """Mock MCA employer verification"""
    time.sleep(1)
    # Mock some common company names
    valid_companies = [
        "Tata Consultancy Services", "Infosys Limited", "Wipro Limited",
        "Tech Mahindra", "HCL Technologies", "Cognizant Technology Solutions",
        "Accenture", "IBM India", "Microsoft India", "Google India"
    ]
    
    is_valid = any(comp.lower() in employer_name.lower() for comp in valid_companies)
    
    return {
        "company_found": is_valid,
        "company_name": employer_name if is_valid else None,
        "cin": f"U{random.randint(10000, 99999)}MH2010PTC{random.randint(100000, 999999)}" if is_valid else None,
        "status": "active" if is_valid else "not_found"
    }

# API Endpoints

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/admin/reset-database")
async def reset_database():
    """Reset and re-seed the database with sample data"""
    try:
        print("🔄 Resetting database...")
        
        # Clear all collections
        db.users.delete_many({})
        db.properties.delete_many({})
        db.property_interests.delete_many({})
        
        # Re-seed sample data
        seed_sample_data()
        
        return {
            "message": "Database reset and re-seeded successfully",
            "users_count": db.users.count_documents({}),
            "properties_count": db.properties.count_documents({}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset database: {str(e)}")

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    # Check if user with email already exists
    existing_email = db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check if user with phone already exists
    existing_phone = db.users.find_one({"phone": user_data.phone})
    if existing_phone:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "phone": user_data.phone,
        "password": hash_password(user_data.password),
        "user_type": user_data.user_type,
        "full_name": user_data.full_name,
        "profile_completed": False,
        "kyc_completed": False,
        "created_at": datetime.now().isoformat()
    }
    
    try:
        db.users.insert_one(user_doc)
        token = generate_token(user_id)
        
        return {
            "message": "User registered successfully",
            "token": token,
            "user": {
                "user_id": user_id,
                "email": user_data.email,
                "user_type": user_data.user_type,
                "full_name": user_data.full_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

@app.post("/api/auth/login")
async def login_user(email: str = Form(...), password: str = Form(...)):
    user = db.users.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = generate_token(user["user_id"])
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "user_type": user["user_type"],
            "full_name": user["full_name"],
            "profile_completed": user.get("profile_completed", False),
            "kyc_completed": user.get("kyc_completed", False)
        }
    }

@app.get("/api/user/profile")
async def get_user_profile(current_user = Depends(verify_token)):
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "user_type": current_user["user_type"],
        "full_name": current_user["full_name"],
        "profile": current_user.get("profile", {}),
        "profile_completed": current_user.get("profile_completed", False),
        "kyc_completed": current_user.get("kyc_completed", False)
    }

@app.put("/api/user/profile")
async def update_user_profile(profile_data: UserProfile, current_user = Depends(verify_token)):
    profile_dict = profile_data.dict(exclude_unset=True)
    
    db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$set": {
                "profile": profile_dict,
                "profile_completed": True,
                "updated_at": datetime.now().isoformat()
            }
        }
    )
    
    return {"message": "Profile updated successfully"}

@app.post("/api/properties")
async def create_property(property_data: Property, current_user = Depends(verify_token)):
    if current_user["user_type"] not in ["owner", "dealer"]:
        raise HTTPException(status_code=403, detail="Only owners and dealers can create properties")
    
    # Mock geocoding with enhanced location data
    coordinates = mock_geocode(property_data.location)
    
    property_id = str(uuid.uuid4())
    property_doc = {
        "property_id": property_id,
        "owner_id": current_user["user_id"],
        "title": property_data.title,
        "description": property_data.description,
        "property_type": property_data.property_type,
        "bhk": property_data.bhk,
        "area_size": property_data.area_size,
        "area_unit": property_data.area_unit,
        "rent": property_data.rent,
        "location": property_data.location,
        "google_location": property_data.google_location or {
            "place_id": f"mock_place_{property_id[:8]}",
            "formatted_address": property_data.location,
            "geometry": {"lat": coordinates["lat"], "lng": coordinates["lng"]}
        },
        "latitude": coordinates["lat"],
        "longitude": coordinates["lng"],
        "amenities": property_data.amenities,
        "images": property_data.images,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    db.properties.insert_one(property_doc)
    
    # Remove the MongoDB _id field before returning
    property_doc.pop('_id', None)
    
    return {
        "message": "Property created successfully",
        "property_id": property_id,
        "property": property_doc
    }

@app.get("/api/properties")
async def get_properties(
    user_type: Optional[str] = None,
    location: Optional[str] = None,
    min_rent: Optional[float] = None,
    max_rent: Optional[float] = None,
    property_type: Optional[str] = None,
    current_user = Depends(verify_token)
):
    filters = {"status": "active"}
    
    # If owner or dealer, show their properties
    if current_user["user_type"] in ["owner", "dealer"] and not user_type:
        filters["owner_id"] = current_user["user_id"]
    
    # Apply search filters
    if location:
        filters["location"] = {"$regex": location, "$options": "i"}
    if min_rent is not None:
        filters["rent"] = {"$gte": min_rent}
    if max_rent is not None:
        filters.setdefault("rent", {})["$lte"] = max_rent
    if property_type and property_type != 'all':
        filters["property_type"] = property_type
    
    properties = list(db.properties.find(filters, {"_id": 0}))
    return {"properties": properties}

@app.get("/api/properties/{property_id}")
async def get_property(property_id: str, current_user = Depends(verify_token)):
    property_doc = db.properties.find_one({"property_id": property_id}, {"_id": 0})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return property_doc

@app.put("/api/properties/{property_id}")
async def update_property(property_id: str, update_data: PropertyUpdate, current_user = Depends(verify_token)):
    property_doc = db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    if property_doc["owner_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    update_dict = update_data.dict(exclude_unset=True)
    if update_dict:
        update_dict["updated_at"] = datetime.now().isoformat()
        db.properties.update_one({"property_id": property_id}, {"$set": update_dict})
    
    return {"message": "Property updated successfully"}

@app.post("/api/kyc/verify")
async def verify_kyc(kyc_data: KYCDocuments, current_user = Depends(verify_token)):
    if current_user["user_type"] != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can complete KYC")
    
    # Mock KYC verification process
    verification_results = {
        "aadhaar_verification": mock_karza_verify_aadhaar(kyc_data.aadhaar_number),
        "pan_verification": mock_karza_verify_pan(kyc_data.pan_number),
        "face_match": mock_karza_face_match(kyc_data.selfie_image, "mock_aadhaar_photo"),
        "digilocker_docs": mock_digilocker_fetch_docs(kyc_data.aadhaar_number)
    }
    
    # Mock employer verification if provided
    if kyc_data.employer_name:
        verification_results["employer_verification"] = mock_mca_employer_verify(kyc_data.employer_name)
    
    # Update user KYC status
    kyc_status = all([
        verification_results["aadhaar_verification"]["status"] == "verified",
        verification_results["pan_verification"]["status"] == "verified",
        verification_results["face_match"]["status"] == "match"
    ])
    
    db.users.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$set": {
                "kyc_completed": kyc_status,
                "kyc_results": verification_results,
                "kyc_updated_at": datetime.now().isoformat()
            }
        }
    )
    
    return {
        "message": "KYC verification completed",
        "kyc_status": kyc_status,
        "verification_results": verification_results
    }

@app.post("/api/properties/{property_id}/interest")
async def express_interest(property_id: str, interest_data: PropertyInterest, current_user = Depends(verify_token)):
    if current_user["user_type"] != "tenant":
        raise HTTPException(status_code=403, detail="Only tenants can express interest")
    
    if not current_user.get("kyc_completed"):
        raise HTTPException(status_code=400, detail="Complete KYC verification first")
    
    property_doc = db.properties.find_one({"property_id": property_id})
    if not property_doc:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Create interest record
    interest_id = str(uuid.uuid4())
    interest_doc = {
        "interest_id": interest_id,
        "property_id": property_id,
        "tenant_id": current_user["user_id"],
        "owner_id": property_doc["owner_id"],
        "message": interest_data.message,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    db.property_interests.insert_one(interest_doc)
    
    return {
        "message": "Interest expressed successfully",
        "interest_id": interest_id
    }

@app.get("/api/interests")
async def get_interests(current_user = Depends(verify_token)):
    if current_user["user_type"] == "tenant":
        interests = list(db.property_interests.find({"tenant_id": current_user["user_id"]}, {"_id": 0}))
    elif current_user["user_type"] in ["owner", "dealer"]:
        interests = list(db.property_interests.find({"owner_id": current_user["user_id"]}, {"_id": 0}))
    else:
        interests = []
    
    return {"interests": interests}

@app.put("/api/interests/{interest_id}/respond")
async def respond_to_interest(interest_id: str, response: str, current_user = Depends(verify_token)):
    if current_user["user_type"] not in ["owner", "dealer"]:
        raise HTTPException(status_code=403, detail="Only owners and dealers can respond to interests")
    
    interest_doc = db.property_interests.find_one({"interest_id": interest_id})
    if not interest_doc:
        raise HTTPException(status_code=404, detail="Interest not found")
    
    if interest_doc["owner_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this interest")
    
    db.property_interests.update_one(
        {"interest_id": interest_id},
        {
            "$set": {
                "status": response,  # approved, rejected
                "responded_at": datetime.now().isoformat(),
                "responded_by": current_user["user_id"]
            }
        }
    )
    
    return {"message": f"Interest {response} successfully"}

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user = Depends(verify_token)):
    user_type = current_user["user_type"]
    stats = {}
    
    if user_type == "owner":
        stats = {
            "total_properties": db.properties.count_documents({"owner_id": current_user["user_id"]}),
            "active_properties": db.properties.count_documents({"owner_id": current_user["user_id"], "status": "active"}),
            "total_interests": db.property_interests.count_documents({"owner_id": current_user["user_id"]}),
            "pending_interests": db.property_interests.count_documents({"owner_id": current_user["user_id"], "status": "pending"})
        }
    elif user_type == "dealer":
        stats = {
            "managed_properties": db.properties.count_documents({"owner_id": current_user["user_id"]}),
            "active_listings": db.properties.count_documents({"owner_id": current_user["user_id"], "status": "active"}),
            "total_interests": db.property_interests.count_documents({"owner_id": current_user["user_id"]}),
            "deals_closed": 0  # Mock data
        }
    elif user_type == "tenant":
        stats = {
            "properties_viewed": 0,  # Mock data
            "interests_expressed": db.property_interests.count_documents({"tenant_id": current_user["user_id"]}),
            "applications_pending": db.property_interests.count_documents({"tenant_id": current_user["user_id"], "status": "pending"}),
            "kyc_status": current_user.get("kyc_completed", False)
        }
    
    return {"stats": stats}

@app.get("/api/admin/users")
async def get_all_users(current_user = Depends(verify_token)):
    """Get all users in the system (admin only)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        users = list(db.users.find({}, {
            "_id": 0,
            "password": 0  # Exclude password from response
        }).sort("created_at", -1))
        
        # Add summary statistics
        user_stats = {
            "total_users": len(users),
            "admins": len([u for u in users if u["user_type"] == "admin"]),
            "owners": len([u for u in users if u["user_type"] == "owner"]),
            "dealers": len([u for u in users if u["user_type"] == "dealer"]), 
            "tenants": len([u for u in users if u["user_type"] == "tenant"]),
            "profile_completed": len([u for u in users if u.get("profile_completed", False)]),
            "kyc_completed": len([u for u in users if u.get("kyc_completed", False)])
        }
        
        return {
            "users": users,
            "statistics": user_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(verify_token)):
    """Delete a user (admin only)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent admin from deleting themselves
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    
    try:
        user = db.users.find_one({"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user and related data
        db.users.delete_one({"user_id": user_id})
        db.properties.delete_many({"owner_id": user_id})
        db.property_interests.delete_many({"$or": [{"tenant_id": user_id}, {"owner_id": user_id}]})
        
        return {"message": f"User {user['full_name']} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/properties")
async def get_all_properties_admin(current_user = Depends(verify_token)):
    """Get all properties (admin only)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        properties = list(db.properties.find({}, {"_id": 0}).sort("created_at", -1))
        
        # Add owner information to each property
        for property_doc in properties:
            owner = db.users.find_one({"user_id": property_doc["owner_id"]}, {"_id": 0, "password": 0})
            if owner:
                property_doc["owner_info"] = {
                    "name": owner["full_name"],
                    "email": owner["email"],
                    "user_type": owner["user_type"]
                }
        
        return {"properties": properties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/properties/{property_id}")
async def delete_property_admin(property_id: str, current_user = Depends(verify_token)):
    """Delete a property (admin only)"""
    if current_user["user_type"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        property_doc = db.properties.find_one({"property_id": property_id})
        if not property_doc:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Delete property and related interests
        db.properties.delete_one({"property_id": property_id})
        db.property_interests.delete_many({"property_id": property_id})
        
        return {"message": f"Property '{property_doc['title']}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/google/places/autocomplete")
async def google_places_autocomplete(query: str, current_user = Depends(verify_token)):
    """Mock Google Places Autocomplete for location selection"""
    if not query or len(query.strip()) < 2:
        return {"predictions": []}
    
    # Mock popular locations in Gurugram and Delhi
    mock_locations = [
        {
            "place_id": "mock_place_1",
            "description": "Sector 102, Gurugram, Haryana, India",
            "structured_formatting": {
                "main_text": "Sector 102",
                "secondary_text": "Gurugram, Haryana, India"
            }
        },
        {
            "place_id": "mock_place_2", 
            "description": "DLF Phase 1, Gurugram, Haryana, India",
            "structured_formatting": {
                "main_text": "DLF Phase 1",
                "secondary_text": "Gurugram, Haryana, India"
            }
        },
        {
            "place_id": "mock_place_3",
            "description": "Cyber City, Gurugram, Haryana, India",
            "structured_formatting": {
                "main_text": "Cyber City", 
                "secondary_text": "Gurugram, Haryana, India"
            }
        },
        {
            "place_id": "mock_place_4",
            "description": "Connaught Place, New Delhi, Delhi, India",
            "structured_formatting": {
                "main_text": "Connaught Place",
                "secondary_text": "New Delhi, Delhi, India"
            }
        },
        {
            "place_id": "mock_place_5",
            "description": "Rajouri Garden, New Delhi, Delhi, India", 
            "structured_formatting": {
                "main_text": "Rajouri Garden",
                "secondary_text": "New Delhi, Delhi, India"
            }
        }
    ]
    
    # Filter based on query
    query_lower = query.lower()
    filtered_locations = [
        loc for loc in mock_locations 
        if query_lower in loc["description"].lower() or query_lower in loc["structured_formatting"]["main_text"].lower()
    ]
    
    return {"predictions": filtered_locations[:5]}

@app.get("/api/google/places/details")
async def google_place_details(place_id: str, current_user = Depends(verify_token)):
    """Mock Google Place Details API"""
    mock_place_details = {
        "mock_place_1": {
            "place_id": "mock_place_1",
            "formatted_address": "Sector 102, Gurugram, Haryana 122006, India",
            "geometry": {
                "location": {"lat": 28.4354, "lng": 77.0428}
            },
            "name": "Sector 102"
        },
        "mock_place_2": {
            "place_id": "mock_place_2",
            "formatted_address": "DLF Phase 1, Gurugram, Haryana 122002, India", 
            "geometry": {
                "location": {"lat": 28.4744, "lng": 77.0909}
            },
            "name": "DLF Phase 1"
        },
        "mock_place_3": {
            "place_id": "mock_place_3",
            "formatted_address": "Cyber City, Gurugram, Haryana 122002, India",
            "geometry": {
                "location": {"lat": 28.4948, "lng": 77.0869}
            },
            "name": "Cyber City"
        },
        "mock_place_4": {
            "place_id": "mock_place_4",
            "formatted_address": "Connaught Place, New Delhi, Delhi 110001, India",
            "geometry": {
                "location": {"lat": 28.6289, "lng": 77.2065}
            },
            "name": "Connaught Place"
        },
        "mock_place_5": {
            "place_id": "mock_place_5",
            "formatted_address": "Rajouri Garden, New Delhi, Delhi 110027, India",
            "geometry": {
                "location": {"lat": 28.6463, "lng": 77.1189}
            },
            "name": "Rajouri Garden"
        }
    }
    
    if place_id not in mock_place_details:
        raise HTTPException(status_code=404, detail="Place not found")
    
    return {"result": mock_place_details[place_id]}

@app.get("/api/admin/system-stats")
async def get_system_stats(current_user = Depends(verify_token)):
    """Get comprehensive system statistics"""
    try:
        stats = {
            "users": {
                "total": db.users.count_documents({}),
                "owners": db.users.count_documents({"user_type": "owner"}),
                "dealers": db.users.count_documents({"user_type": "dealer"}),
                "tenants": db.users.count_documents({"user_type": "tenant"}),
                "profile_completed": db.users.count_documents({"profile_completed": True}),
                "kyc_completed": db.users.count_documents({"kyc_completed": True})
            },
            "properties": {
                "total": db.properties.count_documents({}),
                "active": db.properties.count_documents({"status": "active"}),
                "apartments": db.properties.count_documents({"property_type": "apartment"}), 
                "houses": db.properties.count_documents({"property_type": "house"}),
                "commercial": db.properties.count_documents({"property_type": "commercial"})
            },
            "interests": {
                "total": db.property_interests.count_documents({}),
                "pending": db.property_interests.count_documents({"status": "pending"}),
                "approved": db.property_interests.count_documents({"status": "approved"}),
                "rejected": db.property_interests.count_documents({"status": "rejected"})
            }
        }
        
        return {"system_stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/recent-activity")
async def get_recent_activity(current_user = Depends(verify_token)):
    """Get recent platform activity"""
    try:
        # Recent users (last 10)
        recent_users = list(db.users.find({}, {
            "_id": 0, "password": 0, "profile": 0
        }).sort("created_at", -1).limit(10))
        
        # Recent properties (last 10)
        recent_properties = list(db.properties.find({}, {
            "_id": 0
        }).sort("created_at", -1).limit(10))
        
        # Recent interests (last 10)
        recent_interests = list(db.property_interests.find({}, {
            "_id": 0
        }).sort("created_at", -1).limit(10))
        
        return {
            "recent_users": recent_users,
            "recent_properties": recent_properties,
            "recent_interests": recent_interests
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)