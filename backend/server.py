from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
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
        if db.users.count_documents({}) > 0:
            print("✅ Database already contains user data")
            return
        
        print("🌱 Seeding sample data...")
        
        # Sample users for each persona
        sample_users = [
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
                    "address": "123 Owner Street, Mumbai, Maharashtra"
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
                    "office_address": "456 Business Plaza, Pune, Maharashtra",
                    "areas_served": ["Mumbai", "Pune", "Thane", "Navi Mumbai"]
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
                    "current_address": "789 Tenant Colony, Delhi",
                    "permanent_address": "321 Home Town, Rajasthan"
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
                    "current_address": "101 Tech Park, Bangalore",
                    "permanent_address": "567 Village Road, Kerala"
                },
                "created_at": datetime.now().isoformat()
            }
        ]
        
        # Insert sample users
        db.users.insert_many(sample_users)
        
        # Get user IDs for property creation
        owner_user = db.users.find_one({"user_type": "owner"})
        dealer_user = db.users.find_one({"user_type": "dealer"})
        
        # Sample properties
        sample_properties = [
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": owner_user["user_id"],
                "title": "Luxury 3BHK Apartment in Mumbai",
                "description": "Beautiful luxury apartment with modern amenities, great city views, and prime location near business district.",
                "property_type": "apartment",
                "size": "3 BHK",
                "rent": 45000.0,
                "location": "Bandra West, Mumbai, Maharashtra",
                "latitude": 19.0596,
                "longitude": 72.8295,
                "amenities": ["Parking", "Gym", "Swimming Pool", "Security", "Elevator"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": owner_user["user_id"],
                "title": "Cozy 2BHK House in Pune",
                "description": "Well-maintained house with garden, perfect for small families. Close to schools and hospitals.",
                "property_type": "house",
                "size": "2 BHK",
                "rent": 28000.0,
                "location": "Koregaon Park, Pune, Maharashtra", 
                "latitude": 18.5362,
                "longitude": 73.8958,
                "amenities": ["Garden", "Parking", "Wi-Fi Ready"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": dealer_user["user_id"],
                "title": "Commercial Office Space",
                "description": "Modern office space perfect for startups and small businesses. Fully furnished with high-speed internet.",
                "property_type": "commercial",
                "size": "1500 sq ft",
                "rent": 75000.0,
                "location": "Cyber City, Gurgaon, Haryana",
                "latitude": 28.4595,
                "longitude": 77.0266,
                "amenities": ["Furnished", "High Speed Internet", "Conference Room", "Parking", "Security"],
                "images": [],
                "status": "active",
                "created_at": datetime.now().isoformat()
            },
            {
                "property_id": str(uuid.uuid4()),
                "owner_id": dealer_user["user_id"],
                "title": "Studio Apartment for Working Professionals",
                "description": "Compact and efficient studio apartment ideal for working professionals. All modern amenities included.",
                "property_type": "apartment",
                "size": "1 BHK",
                "rent": 22000.0,
                "location": "Whitefield, Bangalore, Karnataka",
                "latitude": 12.9698,
                "longitude": 77.7500,
                "amenities": ["Fully Furnished", "Wi-Fi", "Laundry", "Kitchen"],
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

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    phone: str
    password: str
    user_type: str  # owner, dealer, tenant
    full_name: str

class UserProfile(BaseModel):
    full_name: str
    phone: str
    address: Optional[str] = None
    areas_served: Optional[List[str]] = None  # For dealers
    office_address: Optional[str] = None  # For dealers
    current_address: Optional[str] = None  # For tenants
    permanent_address: Optional[str] = None  # For tenants

class Property(BaseModel):
    title: str
    description: str
    property_type: str  # apartment, house, commercial
    size: str
    rent: float
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    amenities: List[str] = []
    images: List[str] = []

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    size: Optional[str] = None
    rent: Optional[float] = None
    location: Optional[str] = None
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

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def generate_token(user_id: str) -> str:
    return f"token_{user_id}_{int(time.time())}"

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

# API Endpoints

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/auth/register")
async def register_user(user_data: UserRegistration):
    # Check if user exists
    existing_user = db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
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

@app.post("/api/auth/login")
async def login_user(email: str, password: str):
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
    
    # Mock geocoding
    coordinates = mock_geocode(property_data.location)
    
    property_id = str(uuid.uuid4())
    property_doc = {
        "property_id": property_id,
        "owner_id": current_user["user_id"],
        "title": property_data.title,
        "description": property_data.description,
        "property_type": property_data.property_type,
        "size": property_data.size,
        "rent": property_data.rent,
        "location": property_data.location,
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
    """Get all users in the system (for admin/demo purposes)"""
    try:
        users = list(db.users.find({}, {
            "_id": 0,
            "password": 0  # Exclude password from response
        }).sort("created_at", -1))
        
        # Add summary statistics
        user_stats = {
            "total_users": len(users),
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