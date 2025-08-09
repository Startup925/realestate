import React, { useState, useEffect } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Alert, AlertDescription } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { MapPin, Home, Users, FileCheck, Star, Plus, Search, Phone, Mail, Calendar, CheckCircle, XCircle, Clock, Building, User, Heart } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [loading, setLoading] = useState(false);
  const [properties, setProperties] = useState([]);
  const [interests, setInterests] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [allUsers, setAllUsers] = useState([]);
  const [systemStats, setSystemStats] = useState({});
  const [recentActivity, setRecentActivity] = useState({});

  // Auth forms state
  const [authData, setAuthData] = useState({
    email: '',
    phone: '',
    password: '',
    user_type: 'tenant',
    full_name: ''
  });

  // Profile form state
  const [profileData, setProfileData] = useState({
    full_name: '',
    phone: '',
    address: '',
    areas_served: [],
    office_address: '',
    current_address: '',
    permanent_address: ''
  });

  // Property form state
  const [propertyData, setPropertyData] = useState({
    title: '',
    description: '',
    property_type: 'apartment',
    size: '',
    rent: '',
    location: '',
    amenities: [],
    images: []
  });

  // KYC form state
  const [kycData, setKycData] = useState({
    aadhaar_number: '',
    pan_number: '',
    selfie_image: '',
    employer_name: ''
  });

  // Search filters
  const [searchFilters, setSearchFilters] = useState({
    location: '',
    min_rent: '',
    max_rent: '',
    property_type: 'all'
  });

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      fetchUserProfile();
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      fetchDashboardStats();
      if (activeTab === 'properties') {
        fetchProperties();
      } else if (activeTab === 'interests') {
        fetchInterests();
      } else if (activeTab === 'users') {
        fetchAllUsers();
        fetchSystemStats();
        fetchRecentActivity();
      }
    }
  }, [currentUser, activeTab]);

  const apiCall = async (url, options = {}) => {
    const token = localStorage.getItem('auth_token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers
    };

    const response = await fetch(`${BACKEND_URL}${url}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error);
    }

    return response.json();
  };

  const fetchUserProfile = async () => {
    try {
      const data = await apiCall('/api/user/profile');
      setCurrentUser(data);
      setProfileData({
        full_name: data.full_name || '',
        phone: data.profile?.phone || '',
        address: data.profile?.address || '',
        areas_served: data.profile?.areas_served || [],
        office_address: data.profile?.office_address || '',
        current_address: data.profile?.current_address || '',
        permanent_address: data.profile?.permanent_address || ''
      });
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      localStorage.removeItem('auth_token');
    }
  };

  const fetchDashboardStats = async () => {
    try {
      const data = await apiCall('/api/dashboard/stats');
      setDashboardStats(data.stats);
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  };

  const fetchProperties = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(searchFilters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const data = await apiCall(`/api/properties?${params.toString()}`);
      setProperties(data.properties);
    } catch (error) {
      console.error('Failed to fetch properties:', error);
    }
  };

  const fetchInterests = async () => {
    try {
      const data = await apiCall('/api/interests');
      setInterests(data.interests);
    } catch (error) {
      console.error('Failed to fetch interests:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      let endpoint, payload;
      
      if (authMode === 'login') {
        endpoint = '/api/auth/login';
        payload = new URLSearchParams({
          email: authData.email,
          password: authData.password
        });
      } else {
        endpoint = '/api/auth/register';
        payload = JSON.stringify(authData);
      }

      const headers = authMode === 'login' 
        ? { 'Content-Type': 'application/x-www-form-urlencoded' }
        : { 'Content-Type': 'application/json' };

      const data = await apiCall(endpoint, {
        method: 'POST',
        headers,
        body: payload
      });

      localStorage.setItem('auth_token', data.token);
      setCurrentUser(data.user);
      setAuthData({ email: '', phone: '', password: '', user_type: 'tenant', full_name: '' });
    } catch (error) {
      alert('Authentication failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await apiCall('/api/user/profile', {
        method: 'PUT',
        body: JSON.stringify(profileData)
      });
      
      await fetchUserProfile();
      alert('Profile updated successfully!');
    } catch (error) {
      alert('Failed to update profile: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProperty = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...propertyData,
        rent: parseFloat(propertyData.rent),
        amenities: propertyData.amenities.filter(a => a.trim())
      };

      await apiCall('/api/properties', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setPropertyData({
        title: '',
        description: '',
        property_type: 'apartment',
        size: '',
        rent: '',
        location: '',
        amenities: [],
        images: []
      });
      
      fetchProperties();
      alert('Property created successfully!');
    } catch (error) {
      alert('Failed to create property: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKYCVerification = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = await apiCall('/api/kyc/verify', {
        method: 'POST',
        body: JSON.stringify({
          ...kycData,
          selfie_image: 'mock_base64_image_data'
        })
      });

      await fetchUserProfile();
      alert('KYC verification completed! Status: ' + (data.kyc_status ? 'Verified' : 'Pending'));
    } catch (error) {
      alert('KYC verification failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExpressInterest = async (propertyId, message = '') => {
    setLoading(true);

    try {
      await apiCall(`/api/properties/${propertyId}/interest`, {
        method: 'POST',
        body: JSON.stringify({ property_id: propertyId, message })
      });

      alert('Interest expressed successfully!');
      fetchInterests();
    } catch (error) {
      alert('Failed to express interest: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRespondToInterest = async (interestId, response) => {
    setLoading(true);

    try {
      await apiCall(`/api/interests/${interestId}/respond`, {
        method: 'PUT',
        body: JSON.stringify({ response })
      });

      alert(`Interest ${response} successfully!`);
      fetchInterests();
    } catch (error) {
      alert('Failed to respond to interest: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setCurrentUser(null);
    setActiveTab('dashboard');
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-md mx-auto">
            <div className="text-center mb-8">
              <div className="flex justify-center mb-4">
                <div className="bg-blue-600 p-3 rounded-full">
                  <Home className="h-8 w-8 text-white" />
                </div>
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">RealEstate Platform</h1>
              <p className="text-gray-600">Connecting Owners, Dealers & Tenants</p>
            </div>

            <Card>
              <CardHeader>
                <div className="flex justify-center space-x-2 mb-4">
                  <Button 
                    variant={authMode === 'login' ? 'default' : 'outline'}
                    onClick={() => setAuthMode('login')}
                  >
                    Login
                  </Button>
                  <Button 
                    variant={authMode === 'register' ? 'default' : 'outline'}
                    onClick={() => setAuthMode('register')}
                  >
                    Register
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAuth} className="space-y-4">
                  {authMode === 'register' && (
                    <>
                      <div>
                        <Label htmlFor="full_name">Full Name</Label>
                        <Input
                          id="full_name"
                          value={authData.full_name}
                          onChange={(e) => setAuthData({...authData, full_name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="user_type">I am a</Label>
                        <Select 
                          value={authData.user_type} 
                          onValueChange={(value) => setAuthData({...authData, user_type: value})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select user type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="tenant">Tenant</SelectItem>
                            <SelectItem value="owner">Property Owner</SelectItem>
                            <SelectItem value="dealer">Dealer/Agent</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                          id="phone"
                          value={authData.phone}
                          onChange={(e) => setAuthData({...authData, phone: e.target.value})}
                          required
                        />
                      </div>
                    </>
                  )}
                  
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={authData.email}
                      onChange={(e) => setAuthData({...authData, email: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={authData.password}
                      onChange={(e) => setAuthData({...authData, password: e.target.value})}
                      required
                    />
                  </div>

                  <Button type="submit" className="w-full" disabled={loading}>
                    {loading ? 'Processing...' : (authMode === 'login' ? 'Login' : 'Register')}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  const DashboardContent = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Welcome, {currentUser.full_name}</h2>
          <p className="text-gray-600 capitalize">{currentUser.user_type} Dashboard</p>
        </div>
        <div className="flex items-center space-x-2">
          {!currentUser.profile_completed && (
            <Badge variant="outline" className="text-orange-600">Profile Incomplete</Badge>
          )}
          {currentUser.user_type === 'tenant' && !currentUser.kyc_completed && (
            <Badge variant="outline" className="text-red-600">KYC Pending</Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {currentUser.user_type === 'owner' && (
          <>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Building className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.total_properties || 0}</p>
                    <p className="text-sm text-gray-600">Total Properties</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.active_properties || 0}</p>
                    <p className="text-sm text-gray-600">Active Listings</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Users className="h-8 w-8 text-purple-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.total_interests || 0}</p>
                    <p className="text-sm text-gray-600">Total Interests</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Clock className="h-8 w-8 text-orange-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.pending_interests || 0}</p>
                    <p className="text-sm text-gray-600">Pending Interests</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {currentUser.user_type === 'dealer' && (
          <>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Building className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.managed_properties || 0}</p>
                    <p className="text-sm text-gray-600">Managed Properties</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.active_listings || 0}</p>
                    <p className="text-sm text-gray-600">Active Listings</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Users className="h-8 w-8 text-purple-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.total_interests || 0}</p>
                    <p className="text-sm text-gray-600">Client Interests</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Star className="h-8 w-8 text-yellow-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.deals_closed || 0}</p>
                    <p className="text-sm text-gray-600">Deals Closed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {currentUser.user_type === 'tenant' && (
          <>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Search className="h-8 w-8 text-blue-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.properties_viewed || 0}</p>
                    <p className="text-sm text-gray-600">Properties Viewed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Heart className="h-8 w-8 text-red-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.interests_expressed || 0}</p>
                    <p className="text-sm text-gray-600">Interests Expressed</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <Clock className="h-8 w-8 text-orange-600" />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.applications_pending || 0}</p>
                    <p className="text-sm text-gray-600">Applications Pending</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center space-x-2">
                  <FileCheck className={`h-8 w-8 ${dashboardStats.kyc_status ? 'text-green-600' : 'text-red-600'}`} />
                  <div>
                    <p className="text-2xl font-bold">{dashboardStats.kyc_status ? 'Verified' : 'Pending'}</p>
                    <p className="text-sm text-gray-600">KYC Status</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Home className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">RealEstate Platform</h1>
                <p className="text-sm text-gray-600 capitalize">{currentUser.user_type} Portal</p>
              </div>
            </div>
            <Button onClick={logout} variant="outline">Logout</Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="properties">Properties</TabsTrigger>
            {currentUser.user_type === 'tenant' && (
              <TabsTrigger value="kyc">KYC Verification</TabsTrigger>
            )}
            <TabsTrigger value="interests">
              {currentUser.user_type === 'tenant' ? 'My Interests' : 'Interest Requests'}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="mt-6">
            <DashboardContent />
          </TabsContent>

          <TabsContent value="profile" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Complete your profile to get started
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUpdateProfile} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="full_name">Full Name</Label>
                      <Input
                        id="full_name"
                        value={profileData.full_name}
                        onChange={(e) => setProfileData({...profileData, full_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone">Phone</Label>
                      <Input
                        id="phone"
                        value={profileData.phone}
                        onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  {currentUser.user_type === 'dealer' && (
                    <>
                      <div>
                        <Label htmlFor="office_address">Office Address</Label>
                        <Input
                          id="office_address"
                          value={profileData.office_address}
                          onChange={(e) => setProfileData({...profileData, office_address: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="areas_served">Areas Served (comma separated)</Label>
                        <Input
                          id="areas_served"
                          value={profileData.areas_served.join(', ')}
                          onChange={(e) => setProfileData({
                            ...profileData, 
                            areas_served: e.target.value.split(',').map(a => a.trim()).filter(a => a)
                          })}
                        />
                      </div>
                    </>
                  )}

                  {currentUser.user_type === 'tenant' && (
                    <>
                      <div>
                        <Label htmlFor="current_address">Current Address</Label>
                        <Input
                          id="current_address"
                          value={profileData.current_address}
                          onChange={(e) => setProfileData({...profileData, current_address: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label htmlFor="permanent_address">Permanent Address</Label>
                        <Input
                          id="permanent_address"
                          value={profileData.permanent_address}
                          onChange={(e) => setProfileData({...profileData, permanent_address: e.target.value})}
                        />
                      </div>
                    </>
                  )}

                  {currentUser.user_type === 'owner' && (
                    <div>
                      <Label htmlFor="address">Address</Label>
                      <Input
                        id="address"
                        value={profileData.address}
                        onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                      />
                    </div>
                  )}

                  <Button type="submit" disabled={loading}>
                    {loading ? 'Updating...' : 'Update Profile'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="properties" className="mt-6">
            <div className="space-y-6">
              {/* Search/Filter Bar */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex flex-wrap gap-4 items-end">
                    <div className="flex-1 min-w-[200px]">
                      <Label htmlFor="search_location">Location</Label>
                      <Input
                        id="search_location"
                        placeholder="Search by location..."
                        value={searchFilters.location}
                        onChange={(e) => setSearchFilters({...searchFilters, location: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="min_rent">Min Rent</Label>
                      <Input
                        id="min_rent"
                        type="number"
                        placeholder="Min"
                        value={searchFilters.min_rent}
                        onChange={(e) => setSearchFilters({...searchFilters, min_rent: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="max_rent">Max Rent</Label>
                      <Input
                        id="max_rent"
                        type="number"
                        placeholder="Max"
                        value={searchFilters.max_rent}
                        onChange={(e) => setSearchFilters({...searchFilters, max_rent: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label htmlFor="property_type">Type</Label>
                      <Select 
                        value={searchFilters.property_type} 
                        onValueChange={(value) => setSearchFilters({...searchFilters, property_type: value})}
                      >
                        <SelectTrigger className="w-[130px]">
                          <SelectValue placeholder="All Types" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Types</SelectItem>
                          <SelectItem value="apartment">Apartment</SelectItem>
                          <SelectItem value="house">House</SelectItem>
                          <SelectItem value="commercial">Commercial</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <Button onClick={fetchProperties}>
                      <Search className="h-4 w-4 mr-2" />
                      Search
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Add Property Button for Owners/Dealers */}
              {currentUser.user_type !== 'tenant' && (
                <Dialog>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Add New Property
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Add New Property</DialogTitle>
                      <DialogDescription>
                        Create a new property listing
                      </DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleCreateProperty} className="space-y-4">
                      <div>
                        <Label htmlFor="title">Property Title</Label>
                        <Input
                          id="title"
                          value={propertyData.title}
                          onChange={(e) => setPropertyData({...propertyData, title: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="description">Description</Label>
                        <Textarea
                          id="description"
                          value={propertyData.description}
                          onChange={(e) => setPropertyData({...propertyData, description: e.target.value})}
                          required
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="property_type">Property Type</Label>
                          <Select 
                            value={propertyData.property_type} 
                            onValueChange={(value) => setPropertyData({...propertyData, property_type: value})}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select property type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="apartment">Apartment</SelectItem>
                              <SelectItem value="house">House</SelectItem>
                              <SelectItem value="commercial">Commercial</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label htmlFor="size">Size</Label>
                          <Input
                            id="size"
                            placeholder="e.g., 2 BHK, 1000 sq ft"
                            value={propertyData.size}
                            onChange={(e) => setPropertyData({...propertyData, size: e.target.value})}
                            required
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="rent">Monthly Rent (₹)</Label>
                          <Input
                            id="rent"
                            type="number"
                            value={propertyData.rent}
                            onChange={(e) => setPropertyData({...propertyData, rent: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="location">Location</Label>
                          <Input
                            id="location"
                            value={propertyData.location}
                            onChange={(e) => setPropertyData({...propertyData, location: e.target.value})}
                            required
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="amenities">Amenities (comma separated)</Label>
                        <Input
                          id="amenities"
                          placeholder="e.g., Parking, Gym, Swimming Pool"
                          value={propertyData.amenities.join(', ')}
                          onChange={(e) => setPropertyData({
                            ...propertyData, 
                            amenities: e.target.value.split(',').map(a => a.trim()).filter(a => a)
                          })}
                        />
                      </div>
                      <Button type="submit" disabled={loading}>
                        {loading ? 'Creating...' : 'Create Property'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              )}

              {/* Properties Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {properties.map((property) => (
                  <Card key={property.property_id} className="hover:shadow-lg transition-shadow">
                    <CardContent className="p-0">
                      <div className="h-48 bg-gradient-to-r from-blue-500 to-purple-600 rounded-t-lg flex items-center justify-center">
                        <Home className="h-16 w-16 text-white opacity-50" />
                      </div>
                      <div className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold text-lg truncate">{property.title}</h3>
                          <Badge variant="secondary" className="capitalize">
                            {property.property_type}
                          </Badge>
                        </div>
                        <p className="text-gray-600 text-sm mb-2 line-clamp-2">{property.description}</p>
                        <div className="space-y-1 text-sm text-gray-500">
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            {property.location}
                          </div>
                          <div className="flex justify-between">
                            <span>{property.size}</span>
                            <span className="font-semibold text-green-600">₹{property.rent}/month</span>
                          </div>
                        </div>
                        {property.amenities && property.amenities.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {property.amenities.slice(0, 3).map((amenity, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {amenity}
                              </Badge>
                            ))}
                            {property.amenities.length > 3 && (
                              <Badge variant="outline" className="text-xs">
                                +{property.amenities.length - 3} more
                              </Badge>
                            )}
                          </div>
                        )}
                        <div className="mt-4 flex space-x-2">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => setSelectedProperty(property)}
                          >
                            View Details
                          </Button>
                          {currentUser.user_type === 'tenant' && (
                            <Button 
                              size="sm" 
                              onClick={() => handleExpressInterest(property.property_id)}
                              disabled={loading}
                            >
                              Express Interest
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {properties.length === 0 && (
                <Card>
                  <CardContent className="p-8 text-center">
                    <Home className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Properties Found</h3>
                    <p className="text-gray-600">
                      {currentUser.user_type === 'tenant' 
                        ? 'Try adjusting your search filters or check back later for new listings.'
                        : 'Start by adding your first property listing.'
                      }
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {currentUser.user_type === 'tenant' && (
            <TabsContent value="kyc" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>KYC Verification</CardTitle>
                  <CardDescription>
                    Complete your KYC verification to express interest in properties
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {currentUser.kyc_completed ? (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Your KYC verification is complete! You can now express interest in properties.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <form onSubmit={handleKYCVerification} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="aadhaar_number">Aadhaar Number</Label>
                          <Input
                            id="aadhaar_number"
                            placeholder="XXXX XXXX XXXX"
                            value={kycData.aadhaar_number}
                            onChange={(e) => setKycData({...kycData, aadhaar_number: e.target.value})}
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="pan_number">PAN Number</Label>
                          <Input
                            id="pan_number"
                            placeholder="ABCDE1234F"
                            value={kycData.pan_number}
                            onChange={(e) => setKycData({...kycData, pan_number: e.target.value})}
                            required
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="employer_name">Employer Name (Optional)</Label>
                        <Input
                          id="employer_name"
                          placeholder="e.g., Tata Consultancy Services"
                          value={kycData.employer_name}
                          onChange={(e) => setKycData({...kycData, employer_name: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label>Selfie Upload</Label>
                        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                          <User className="h-12 w-12 mx-auto text-gray-400 mb-2" />
                          <p className="text-gray-600">Click to upload your selfie</p>
                          <p className="text-xs text-gray-500 mt-1">
                            This will be used for face matching with your ID documents
                          </p>
                        </div>
                      </div>
                      <Alert>
                        <FileCheck className="h-4 w-4" />
                        <AlertDescription>
                          This is a mock KYC process. In production, this would integrate with Karza APIs for Aadhaar/PAN verification, face matching, DigiLocker for document verification, and MCA for employer verification.
                        </AlertDescription>
                      </Alert>
                      <Button type="submit" disabled={loading}>
                        {loading ? 'Verifying...' : 'Submit for Verification'}
                      </Button>
                    </form>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          )}

          <TabsContent value="interests" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>
                  {currentUser.user_type === 'tenant' ? 'My Property Interests' : 'Interest Requests'}
                </CardTitle>
                <CardDescription>
                  {currentUser.user_type === 'tenant' 
                    ? 'Track your property applications and their status'
                    : 'Manage interest requests from potential tenants'
                  }
                </CardDescription>
              </CardHeader>
              <CardContent>
                {interests.length === 0 ? (
                  <div className="text-center py-8">
                    <Users className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Interests Yet</h3>
                    <p className="text-gray-600">
                      {currentUser.user_type === 'tenant' 
                        ? 'Start browsing properties and express your interest!'
                        : 'Interest requests from tenants will appear here.'
                      }
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {interests.map((interest) => (
                      <div key={interest.interest_id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-semibold">Property Interest</h4>
                            <p className="text-sm text-gray-600">
                              Interest ID: {interest.interest_id}
                            </p>
                          </div>
                          <Badge 
                            variant={
                              interest.status === 'approved' ? 'default' :
                              interest.status === 'rejected' ? 'destructive' : 'secondary'
                            }
                          >
                            {interest.status}
                          </Badge>
                        </div>
                        {interest.message && (
                          <p className="text-gray-700 mb-2">{interest.message}</p>
                        )}
                        <div className="text-sm text-gray-500">
                          <p>Created: {new Date(interest.created_at).toLocaleDateString()}</p>
                        </div>
                        {currentUser.user_type !== 'tenant' && interest.status === 'pending' && (
                          <div className="mt-3 flex space-x-2">
                            <Button 
                              size="sm" 
                              onClick={() => handleRespondToInterest(interest.interest_id, 'approved')}
                              disabled={loading}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Approve
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleRespondToInterest(interest.interest_id, 'rejected')}
                              disabled={loading}
                            >
                              <XCircle className="h-4 w-4 mr-1" />
                              Reject
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Property Details Modal */}
      {selectedProperty && (
        <Dialog open={!!selectedProperty} onOpenChange={() => setSelectedProperty(null)}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{selectedProperty.title}</DialogTitle>
              <DialogDescription>
                {selectedProperty.location} • ₹{selectedProperty.rent}/month
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="h-64 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Home className="h-24 w-24 text-white opacity-50" />
              </div>
              <div>
                <h4 className="font-semibold mb-2">Description</h4>
                <p className="text-gray-700">{selectedProperty.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold mb-1">Property Type</h4>
                  <p className="text-gray-700 capitalize">{selectedProperty.property_type}</p>
                </div>
                <div>
                  <h4 className="font-semibold mb-1">Size</h4>
                  <p className="text-gray-700">{selectedProperty.size}</p>
                </div>
              </div>
              {selectedProperty.amenities && selectedProperty.amenities.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Amenities</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedProperty.amenities.map((amenity, index) => (
                      <Badge key={index} variant="outline">
                        {amenity}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Location Details</h4>
                <p className="text-gray-700 mb-2">{selectedProperty.location}</p>
                <div className="bg-gray-200 h-32 rounded flex items-center justify-center">
                  <MapPin className="h-8 w-8 text-gray-400" />
                  <span className="ml-2 text-gray-500">Map View (Mock)</span>
                </div>
              </div>
              {currentUser.user_type === 'tenant' && (
                <Button 
                  className="w-full" 
                  onClick={() => {
                    handleExpressInterest(selectedProperty.property_id);
                    setSelectedProperty(null);
                  }}
                  disabled={loading}
                >
                  Express Interest in This Property
                </Button>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

export default App;