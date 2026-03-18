// utils/testConnection.js
export const testBackendConnection = async () => {
  try {
    const response = await fetch('http://localhost:8000/health', {
      method: 'GET',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      console.log('✅ Backend connection successful');
      return true;
    } else {
      console.log('❌ Backend returned error:', response.status);
      return false;
    }
  } catch (error) {
    console.error('❌ Cannot connect to backend:', error.message);
    console.log('💡 Make sure your backend server is running on http://localhost:8000');
    return false;
  }
};

export const testCORSConnection = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/health', {
      method: 'GET',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (response.ok) {
      console.log('✅ CORS connection successful');
      return true;
    } else {
      console.log('❌ CORS test failed:', response.status);
      return false;
    }
  } catch (error) {
    console.error('❌ CORS error:', error.message);
    console.log('💡 Check CORS configuration in backend');
    return false;
  }
};

export const testAuthEndpoints = async () => {
  try {
    // Test register endpoint
    const registerResponse = await fetch('http://localhost:8000/api/auth/register', {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'test_user',
        email: 'test@example.com',
        password: 'test123',
        role: 'student'
      })
    });
    
    if (registerResponse.ok) {
      console.log('✅ Register endpoint accessible');
    } else {
      console.log('❌ Register endpoint error:', registerResponse.status);
    }

    // Test login endpoint
    const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: 'test_user',
        password: 'test123'
      })
    });
    
    if (loginResponse.ok) {
      console.log('✅ Login endpoint accessible');
      return true;
    } else {
      console.log('❌ Login endpoint error:', loginResponse.status);
      return false;
    }
  } catch (error) {
    console.error('❌ Auth endpoints error:', error.message);
    return false;
  }
};
