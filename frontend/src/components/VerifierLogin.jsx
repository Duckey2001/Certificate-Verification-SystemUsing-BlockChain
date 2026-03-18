import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './VerifierAuth.css';

const VerifierLogin = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/verifier/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('verifier_credential', JSON.stringify(data.verifier_credential));
        navigate('/verifier/dashboard');
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verifier-auth-container">
      <div className="verifier-auth-card">
        <div className="verifier-auth-header">
          <h2>Verifier Login</h2>
          <p>Login to access certificate verification tools</p>
        </div>

        {error && (
          <div className="alert alert-danger">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="verifier-auth-form">
          <div className="form-group">
            <label htmlFor="username">Username or Email</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              className="form-control"
              placeholder="Enter your username or email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="form-control"
              placeholder="Enter your password"
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary verifier-auth-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Logging in...
              </>
            ) : (
              'Login as Verifier'
            )}
          </button>
        </form>

        <div className="verifier-auth-footer">
          <p>
            Don't have an account? 
            <Link to="/verifier/register" className="auth-link"> Register as Verifier</Link>
          </p>
          <p>
            <Link to="/auth/login" className="auth-link">Regular User Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerifierLogin;
