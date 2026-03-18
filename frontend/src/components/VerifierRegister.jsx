import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import './VerifierAuth.css';

const VerifierRegister = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    license_number: '',
    specialization: '',
    qualification_level: '',
    institution_affiliation: '',
    years_experience: 0,
    professional_certificates: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleNumberChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: parseInt(e.target.value) || 0
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      setLoading(false);
      return;
    }

    try {
      const { confirmPassword, ...registrationData } = formData;
      
      const response = await fetch('/api/verifier/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registrationData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Registration successful! Redirecting to login...');
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        localStorage.setItem('verifier_credential', JSON.stringify(data.verifier_credential));
        
        setTimeout(() => {
          navigate('/verifier/dashboard');
        }, 2000);
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verifier-auth-container">
      <div className="verifier-auth-card register-card">
        <div className="verifier-auth-header">
          <h2>Register as Verifier</h2>
          <p>Create your verifier account to start verifying certificates</p>
        </div>

        {error && (
          <div className="alert alert-danger">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="verifier-auth-form">
          <div className="form-section">
            <h3>Account Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="username">Username *</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  required
                  className="form-control"
                  placeholder="Choose a username"
                />
              </div>

              <div className="form-group">
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="form-control"
                  placeholder="your.email@example.com"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="password">Password *</label>
                <input
                  type="password"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="form-control"
                  placeholder="Min 8 characters"
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password *</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="form-control"
                  placeholder="Re-enter password"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Professional Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="license_number">Professional License Number</label>
                <input
                  type="text"
                  id="license_number"
                  name="license_number"
                  value={formData.license_number}
                  onChange={handleChange}
                  className="form-control"
                  placeholder="e.g., PSY-2023-001"
                />
              </div>

              <div className="form-group">
                <label htmlFor="specialization">Specialization</label>
                <input
                  type="text"
                  id="specialization"
                  name="specialization"
                  value={formData.specialization}
                  onChange={handleChange}
                  className="form-control"
                  placeholder="e.g., Computer Science, Engineering"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="qualification_level">Qualification Level</label>
                <select
                  id="qualification_level"
                  name="qualification_level"
                  value={formData.qualification_level}
                  onChange={handleChange}
                  className="form-control"
                >
                  <option value="">Select Qualification</option>
                  <option value="PhD">PhD</option>
                  <option value="Masters">Master's Degree</option>
                  <option value="Bachelor">Bachelor's Degree</option>
                  <option value="Diploma">Diploma</option>
                  <option value="Certificate">Professional Certificate</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="years_experience">Years of Experience</label>
                <input
                  type="number"
                  id="years_experience"
                  name="years_experience"
                  value={formData.years_experience}
                  onChange={handleNumberChange}
                  min="0"
                  max="50"
                  className="form-control"
                  placeholder="0"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="institution_affiliation">Institution Affiliation</label>
              <input
                type="text"
                id="institution_affiliation"
                name="institution_affiliation"
                value={formData.institution_affiliation}
                onChange={handleChange}
                className="form-control"
                placeholder="e.g., University of Technology"
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary verifier-auth-btn"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Registering...
              </>
            ) : (
              'Register as Verifier'
            )}
          </button>
        </form>

        <div className="verifier-auth-footer">
          <p>
            Already have an account? 
            <Link to="/verifier/login" className="auth-link"> Login as Verifier</Link>
          </p>
          <p>
            <Link to="/auth/login" className="auth-link">Regular User Login</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default VerifierRegister;
