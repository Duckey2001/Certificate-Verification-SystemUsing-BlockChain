import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const JoinNetwork = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [isVisible, setIsVisible] = useState(false);
  const [formData, setFormData] = useState({
    institutionName: '',
    institutionType: 'educational',
    institutionEmail: '',
    institutionPhone: '',
    institutionWebsite: '',
    contactPerson: '',
    contactEmail: '',
    contactPhone: '',
    requestedRole: 'verifier',
    peerModel: 'hosted',
    expectedVolume: 'low',
    accreditationNumber: '',
    country: '',
    city: '',
    address: '',
    documents: [],
    termsAccepted: false,
    communicationsAccepted: false
  });

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    setFormData(prev => ({
      ...prev,
      documents: [...prev.documents, ...files]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.termsAccepted) {
      alert('Please accept the terms and conditions');
      return;
    }

    // Submit join request
    alert(`
      🎉 Join Request Submitted!
      
      Institution: ${formData.institutionName}
      Requested Role: ${formData.requestedRole}
      Peer Model: ${formData.peerModel === 'hosted' ? 'Hosted Peer' : 'BYO Peer'}
      
      Our team will review your application and contact you at ${formData.contactEmail}.
      
      Thank you for choosing CertiVert!
    `);

    // Redirect to dashboard or confirmation page
    navigate('/join-confirmation');
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const files = Array.from(e.dataTransfer.files);
    setFormData(prev => ({
      ...prev,
      documents: [...prev.documents, ...files]
    }));
  };

  const removeDocument = (index) => {
    setFormData(prev => ({
      ...prev,
      documents: prev.documents.filter((_, i) => i !== index)
    }));
  };

  const nextStep = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setStep(step + 1);
  };

  const prevStep = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setStep(step - 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white overflow-x-hidden relative">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-20 -left-4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-40 -right-4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/3 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
        <div className="absolute inset-0 bg-pattern opacity-5"></div>
      </div>

      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(30)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-white rounded-full animate-float"
            style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 7}s`,
              opacity: 0.1 + Math.random() * 0.3
            }}
          />
        ))}
      </div>

      {/* Header with Logo */}
      <div className="relative pt-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <span className="text-3xl">🔐</span>
                </div>
                <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl blur opacity-30"></div>
              </div>
              <div>
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  CertiVert
                </span>
                <span className="ml-2 px-2 py-0.5 text-xs bg-gray-800 text-gray-300 rounded-full">Network</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-sm text-gray-400">Network Status: Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className={`text-center mb-12 transform transition-all duration-1000 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
        }`}>
          <h1 className="text-5xl md:text-6xl font-bold mb-4">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Join the CertiVert
            </span>
            <br />Blockchain Network
          </h1>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Become part of the trusted blockchain certificate verification network. 
            Connect with institutions worldwide and ensure certificate authenticity.
          </p>
        </div>

        {/* Progress Bar */}
        <div className={`mb-12 transform transition-all duration-1000 delay-300 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
        }`}>
          <div className="relative">
            <div className="absolute top-5 left-0 w-full h-1 bg-gray-700 rounded-full">
              <div 
                className="h-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full transition-all duration-500"
                style={{ width: `${(step / 4) * 100}%` }}
              ></div>
            </div>
            <div className="relative flex justify-between">
              {[1, 2, 3, 4].map((num) => (
                <div key={num} className="flex flex-col items-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold transition-all duration-300 ${
                    step >= num 
                      ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/30' 
                      : 'bg-gray-700 text-gray-400'
                  }`}>
                    {step > num ? '✓' : num}
                  </div>
                  <span className={`mt-2 text-xs font-medium ${
                    step >= num ? 'text-white' : 'text-gray-500'
                  }`}>
                    {num === 1 && 'Institution'}
                    {num === 2 && 'Network'}
                    {num === 3 && 'Documents'}
                    {num === 4 && 'Review'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Form Column */}
          <div className={`lg:col-span-2 transform transition-all duration-1000 delay-500 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
          }`}>
            <div className="bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-6">
                <h2 className="text-2xl font-bold text-white">
                  {step === 1 && 'Institution Information'}
                  {step === 2 && 'Network Configuration'}
                  {step === 3 && 'Contact & Documents'}
                  {step === 4 && 'Review & Submit'}
                </h2>
                <p className="text-blue-100 mt-1">
                  {step === 1 && 'Tell us about your organization'}
                  {step === 2 && 'Configure your network participation'}
                  {step === 3 && 'Provide contact details and required documents'}
                  {step === 4 && 'Review your application before submission'}
                </p>
              </div>

              <form onSubmit={handleSubmit} className="p-8">
                {/* Step 1: Institution Information */}
                {step === 1 && (
                  <div className="space-y-6 animate-fadeIn">
                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Institution Name *
                        </label>
                        <input
                          type="text"
                          name="institutionName"
                          value={formData.institutionName}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="University of Technology"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Institution Type *
                        </label>
                        <select
                          name="institutionType"
                          value={formData.institutionType}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          required
                        >
                          <option value="educational">Educational Institution</option>
                          <option value="government">Government Agency</option>
                          <option value="corporate">Corporate</option>
                          <option value="nonprofit">Non-Profit</option>
                          <option value="other">Other</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Official Email *
                        </label>
                        <input
                          type="email"
                          name="institutionEmail"
                          value={formData.institutionEmail}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="admin@institution.edu"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Phone Number
                        </label>
                        <input
                          type="tel"
                          name="institutionPhone"
                          value={formData.institutionPhone}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="+1 (555) 123-4567"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Website
                        </label>
                        <input
                          type="url"
                          name="institutionWebsite"
                          value={formData.institutionWebsite}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="https://institution.edu"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Accreditation Number
                        </label>
                        <input
                          type="text"
                          name="accreditationNumber"
                          value={formData.accreditationNumber}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="ACC-123456"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Address
                      </label>
                      <textarea
                        name="address"
                        value={formData.address}
                        onChange={handleInputChange}
                        rows="3"
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        placeholder="Full institution address"
                      />
                    </div>

                    <div className="grid md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Country *
                        </label>
                        <input
                          type="text"
                          name="country"
                          value={formData.country}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="Country"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          City
                        </label>
                        <input
                          type="text"
                          name="city"
                          value={formData.city}
                          onChange={handleInputChange}
                          className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                          placeholder="City"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 2: Network Configuration */}
                {step === 2 && (
                  <div className="space-y-8 animate-fadeIn">
                    {/* Role Selection */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Select Your Role *</h3>
                      <div className="grid md:grid-cols-2 gap-4">
                        <div
                          onClick={() => setFormData({...formData, requestedRole: 'verifier'})}
                          className={`p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
                            formData.requestedRole === 'verifier'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-white/10 bg-white/5 hover:border-blue-500/50'
                          }`}
                        >
                          <div className="text-4xl mb-3">🔍</div>
                          <h4 className="font-semibold text-white mb-2">Verifier</h4>
                          <p className="text-sm text-gray-400 mb-4">Read-only access to verify certificates</p>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Query certificate records
                            </li>
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Verify certificate authenticity
                            </li>
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Read blockchain ledger
                            </li>
                            <li className="flex items-center text-gray-500">
                              <span className="mr-2">✗</span> Cannot issue certificates
                            </li>
                          </ul>
                        </div>

                        <div
                          onClick={() => setFormData({...formData, requestedRole: 'issuer'})}
                          className={`p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
                            formData.requestedRole === 'issuer'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-white/10 bg-white/5 hover:border-purple-500/50'
                          }`}
                        >
                          <div className="text-4xl mb-3">🏛️</div>
                          <h4 className="font-semibold text-white mb-2">Issuer</h4>
                          <p className="text-sm text-gray-400 mb-4">Full access to issue and verify</p>
                          <ul className="space-y-2 text-sm">
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Issue new certificates
                            </li>
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Verify certificates
                            </li>
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Write to blockchain
                            </li>
                            <li className="flex items-center text-green-400">
                              <span className="mr-2">✓</span> Manage certificate lifecycle
                            </li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Peer Model Selection */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Select Peer Model *</h3>
                      <div className="space-y-4">
                        <div
                          onClick={() => setFormData({...formData, peerModel: 'hosted'})}
                          className={`p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
                            formData.peerModel === 'hosted'
                              ? 'border-blue-500 bg-blue-500/10'
                              : 'border-white/10 bg-white/5 hover:border-blue-500/50'
                          }`}
                        >
                          <div className="flex items-start gap-4">
                            <div className="text-4xl">🏠</div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="font-semibold text-white">Hosted Peer (Recommended)</h4>
                                <span className="px-3 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">$99/month</span>
                              </div>
                              <p className="text-sm text-gray-400 mb-4">We manage the blockchain infrastructure for you</p>
                              <div className="grid md:grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-300 block mb-2">Advantages:</span>
                                  <ul className="space-y-1 text-gray-400">
                                    <li>✓ No infrastructure management</li>
                                    <li>✓ Faster onboarding (24-48h)</li>
                                    <li>✓ Automatic updates</li>
                                    <li>✓ Lower operational cost</li>
                                  </ul>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div
                          onClick={() => setFormData({...formData, peerModel: 'byo'})}
                          className={`p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300 ${
                            formData.peerModel === 'byo'
                              ? 'border-purple-500 bg-purple-500/10'
                              : 'border-white/10 bg-white/5 hover:border-purple-500/50'
                          }`}
                        >
                          <div className="flex items-start gap-4">
                            <div className="text-4xl">🖥️</div>
                            <div className="flex-1">
                              <h4 className="font-semibold text-white mb-2">Bring Your Own Peer</h4>
                              <p className="text-sm text-gray-400 mb-4">You run your own blockchain infrastructure</p>
                              <div className="grid md:grid-cols-2 gap-4 text-sm">
                                <div>
                                  <span className="text-gray-300 block mb-2">Advantages:</span>
                                  <ul className="space-y-1 text-gray-400">
                                    <li>✓ More decentralization</li>
                                    <li>✓ Complete control</li>
                                    <li>✓ Stronger trust model</li>
                                    <li>✓ Direct ledger access</li>
                                  </ul>
                                </div>
                                <div>
                                  <span className="text-gray-300 block mb-2">Requirements:</span>
                                  <ul className="space-y-1 text-gray-400">
                                    <li>✓ Docker & Docker Compose</li>
                                    <li>✓ 4GB RAM minimum</li>
                                    <li>✓ 50GB storage</li>
                                    <li>✓ Technical team</li>
                                  </ul>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Volume Estimation */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Expected Certificate Volume</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {['low', 'medium', 'high', 'enterprise'].map((level) => (
                          <button
                            key={level}
                            type="button"
                            onClick={() => setFormData({...formData, expectedVolume: level})}
                            className={`p-4 rounded-xl text-center transition-all duration-300 ${
                              formData.expectedVolume === level
                                ? 'bg-blue-500/20 border-2 border-blue-500'
                                : 'bg-white/5 border-2 border-white/10 hover:border-blue-500/50'
                            }`}
                          >
                            <div className="text-sm font-semibold text-white mb-1">
                              {level.toUpperCase()}
                            </div>
                            <div className="text-xs text-gray-400">
                              {level === 'low' && '< 100/month'}
                              {level === 'medium' && '100-1k/month'}
                              {level === 'high' && '1k-10k/month'}
                              {level === 'enterprise' && '10k+/month'}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Step 3: Contact & Documents */}
                {step === 3 && (
                  <div className="space-y-6 animate-fadeIn">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Primary Contact Person</h3>
                      <div className="grid md:grid-cols-2 gap-6">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Full Name *
                          </label>
                          <input
                            type="text"
                            name="contactPerson"
                            value={formData.contactPerson}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="my name"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Email Address *
                          </label>
                          <input
                            type="email"
                            name="contactEmail"
                            value={formData.contactEmail}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="my.name@institution.edu"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Phone Number *
                          </label>
                          <input
                            type="tel"
                            name="contactPhone"
                            value={formData.contactPhone}
                            onChange={handleInputChange}
                            className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                            placeholder="+1 (555) 123-4567"
                            required
                          />
                        </div>
                      </div>
                    </div>

                    {/* Document Upload */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4">Required Documents</h3>
                      <div className="bg-white/5 rounded-xl p-6 mb-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl">📄</span>
                              <span className="text-sm text-gray-300">Business Registration or Accreditation</span>
                            </div>
                            <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">Required</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl">🆔</span>
                              <span className="text-sm text-gray-300">Government ID of Contact Person</span>
                            </div>
                            <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">Required</span>
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl">📋</span>
                              <span className="text-sm text-gray-300">Letter of Authorization (for Issuer role)</span>
                            </div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              formData.requestedRole === 'issuer'
                                ? 'bg-red-500/20 text-red-400'
                                : 'bg-gray-500/20 text-gray-400'
                            }`}>
                              {formData.requestedRole === 'issuer' ? 'Required' : 'Optional'}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Upload Zone */}
                      <div
                        className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-blue-500/50 transition-colors cursor-pointer group"
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('file-upload').click()}
                      >
                        <input
                          id="file-upload"
                          type="file"
                          multiple
                          onChange={handleFileUpload}
                          className="hidden"
                        />
                        <div className="text-5xl mb-4 text-gray-500 group-hover:text-blue-400 transition-colors">📤</div>
                        <h4 className="text-lg font-semibold text-white mb-2">Drag & Drop Documents Here</h4>
                        <p className="text-sm text-gray-400 mb-2">or click to browse files</p>
                        <p className="text-xs text-gray-500">PDF, PNG, JPG up to 10MB each</p>
                      </div>

                      {/* Uploaded Files List */}
                      {formData.documents.length > 0 && (
                        <div className="mt-4 space-y-2">
                          {formData.documents.map((file, index) => (
                            <div key={index} className="flex items-center justify-between bg-white/5 rounded-lg p-3">
                              <div className="flex items-center space-x-3">
                                <span className="text-2xl">📄</span>
                                <div>
                                  <p className="text-sm text-white">{file.name}</p>
                                  <p className="text-xs text-gray-400">
                                    {(file.size / 1024 / 1024).toFixed(2)} MB
                                  </p>
                                </div>
                              </div>
                              <button
                                type="button"
                                onClick={() => removeDocument(index)}
                                className="text-gray-400 hover:text-red-400 transition-colors"
                              >
                                ✕
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Terms Checkboxes */}
                    <div className="space-y-3">
                      <label className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          name="termsAccepted"
                          checked={formData.termsAccepted}
                          onChange={handleInputChange}
                          className="mt-1 w-4 h-4 bg-white/5 border border-white/10 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-400">
                          I agree to the <a href="#" className="text-blue-400 hover:text-blue-300">Terms of Service</a>,{' '}
                          <a href="#" className="text-blue-400 hover:text-blue-300">Privacy Policy</a>, and{' '}
                          <a href="#" className="text-blue-400 hover:text-blue-300">Network Participation Agreement</a>
                        </span>
                      </label>
                      <label className="flex items-start space-x-3">
                        <input
                          type="checkbox"
                          name="communicationsAccepted"
                          checked={formData.communicationsAccepted}
                          onChange={handleInputChange}
                          className="mt-1 w-4 h-4 bg-white/5 border border-white/10 rounded focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-400">
                          I agree to receive communications about my application and network updates
                        </span>
                      </label>
                    </div>
                  </div>
                )}

                {/* Step 4: Review */}
                {step === 4 && (
                  <div className="space-y-6 animate-fadeIn">
                    <div className="bg-white/5 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Institution Details</h3>
                      <dl className="grid md:grid-cols-2 gap-4">
                        <div>
                          <dt className="text-sm text-gray-400">Institution Name</dt>
                          <dd className="text-sm font-medium text-white">{formData.institutionName}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Institution Type</dt>
                          <dd className="text-sm font-medium text-white capitalize">{formData.institutionType}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Email</dt>
                          <dd className="text-sm font-medium text-white">{formData.institutionEmail}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Country</dt>
                          <dd className="text-sm font-medium text-white">{formData.country}</dd>
                        </div>
                      </dl>
                    </div>

                    <div className="bg-white/5 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Network Configuration</h3>
                      <dl className="grid md:grid-cols-3 gap-4">
                        <div>
                          <dt className="text-sm text-gray-400">Requested Role</dt>
                          <dd className="text-sm">
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                              formData.requestedRole === 'issuer'
                                ? 'bg-purple-500/20 text-purple-400'
                                : 'bg-blue-500/20 text-blue-400'
                            }`}>
                              {formData.requestedRole.toUpperCase()}
                            </span>
                          </dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Peer Model</dt>
                          <dd className="text-sm">
                            <span className="inline-block px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-medium">
                              {formData.peerModel === 'hosted' ? 'Hosted' : 'BYO'}
                            </span>
                          </dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Expected Volume</dt>
                          <dd className="text-sm font-medium text-white capitalize">{formData.expectedVolume}</dd>
                        </div>
                      </dl>
                    </div>

                    <div className="bg-white/5 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Contact Information</h3>
                      <dl className="grid md:grid-cols-3 gap-4">
                        <div>
                          <dt className="text-sm text-gray-400">Contact Person</dt>
                          <dd className="text-sm font-medium text-white">{formData.contactPerson}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Contact Email</dt>
                          <dd className="text-sm font-medium text-white">{formData.contactEmail}</dd>
                        </div>
                        <div>
                          <dt className="text-sm text-gray-400">Contact Phone</dt>
                          <dd className="text-sm font-medium text-white">{formData.contactPhone}</dd>
                        </div>
                      </dl>
                    </div>

                    <div className="bg-white/5 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Documents ({formData.documents.length})</h3>
                      {formData.documents.length > 0 ? (
                        <div className="space-y-2">
                          {formData.documents.map((file, index) => (
                            <div key={index} className="flex items-center space-x-3">
                              <span className="text-2xl">📄</span>
                              <span className="text-sm text-gray-300">{file.name}</span>
                              <span className="text-xs text-gray-500">
                                ({(file.size / 1024 / 1024).toFixed(2)} MB)
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-400">No documents uploaded</p>
                      )}
                    </div>

                    {/* Next Steps */}
                    <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-xl p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">What Happens Next?</h3>
                      <div className="grid md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="w-10 h-10 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-blue-400 font-bold">1</span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-1">Application Review</h4>
                          <p className="text-xs text-gray-400">1-2 business days</p>
                        </div>
                        <div className="text-center">
                          <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-purple-400 font-bold">2</span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-1">Verification Call</h4>
                          <p className="text-xs text-gray-400">Schedule with your team</p>
                        </div>
                        <div className="text-center">
                          <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-green-400 font-bold">3</span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-1">Onboarding Package</h4>
                          <p className="text-xs text-gray-400">Receive MSP certificates</p>
                        </div>
                        <div className="text-center">
                          <div className="w-10 h-10 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-orange-400 font-bold">4</span>
                          </div>
                          <h4 className="text-sm font-semibold text-white mb-1">Network Integration</h4>
                          <p className="text-xs text-gray-400">Added to blockchain</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Navigation Buttons */}
                <div className="flex justify-between mt-8 pt-6 border-t border-white/10">
                  {step > 1 && (
                    <button
                      type="button"
                      onClick={prevStep}
                      className="px-6 py-3 bg-white/5 hover:bg-white/10 rounded-xl text-white font-medium transition-all duration-300 flex items-center space-x-2"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                      </svg>
                      <span>Back</span>
                    </button>
                  )}
                  
                  {step < 4 ? (
                    <button
                      type="button"
                      onClick={nextStep}
                      className="ml-auto px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl text-white font-medium transition-all duration-300 flex items-center space-x-2 group"
                    >
                      <span>Continue</span>
                      <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={!formData.termsAccepted}
                      className="ml-auto px-8 py-3 bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 rounded-xl text-white font-medium transition-all duration-300 flex items-center space-x-2 group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span>🚀 Submit Join Request</span>
                      <svg className="w-5 h-5 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </button>
                  )}
                </div>
              </form>
            </div>
          </div>

          {/* Info Sidebar */}
          <div className={`lg:col-span-1 space-y-6 transform transition-all duration-1000 delay-700 ${
            isVisible ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0'
          }`}>
            {/* Benefits Card */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Why Join CertiVert?</h3>
              <ul className="space-y-3">
                {[
                  'Trusted blockchain verification',
                  'Global network of institutions',
                  'Tamper-proof certificate records',
                  'Real-time verification',
                  'Reduced fraud risk',
                  'Industry standard compliance'
                ].map((benefit, index) => (
                  <li key={index} className="flex items-center space-x-3">
                    <span className="text-green-400">✓</span>
                    <span className="text-sm text-gray-300">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Stats Card */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Network Statistics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-white/5 rounded-xl">
                  <div className="text-2xl font-bold text-blue-400">500+</div>
                  <div className="text-xs text-gray-400">Institutions</div>
                </div>
                <div className="text-center p-3 bg-white/5 rounded-xl">
                  <div className="text-2xl font-bold text-purple-400">10K+</div>
                  <div className="text-xs text-gray-400">Certificates</div>
                </div>
                <div className="text-center p-3 bg-white/5 rounded-xl">
                  <div className="text-2xl font-bold text-green-400">99.9%</div>
                  <div className="text-xs text-gray-400">Uptime</div>
                </div>
                <div className="text-center p-3 bg-white/5 rounded-xl">
                  <div className="text-2xl font-bold text-yellow-400">24/7</div>
                  <div className="text-xs text-gray-400">Support</div>
                </div>
              </div>
            </div>

            {/* Support Card */}
            <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 backdrop-blur-xl rounded-2xl border border-white/20 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Need Help?</h3>
              <p className="text-sm text-gray-300 mb-4">Contact our onboarding team:</p>
              <div className="space-y-3 mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">📧</span>
                  <span className="text-sm text-gray-300">onboarding@certivert.com</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">📞</span>
                  <span className="text-sm text-gray-300">+1 (555) 123-4567</span>
                </div>
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">🕒</span>
                  <span className="text-sm text-gray-300">Mon-Fri, 9AM-5PM EST</span>
                </div>
              </div>
              <button className="w-full px-4 py-3 bg-white/10 hover:bg-white/20 rounded-xl text-white font-medium transition-all duration-300">
                Schedule a Demo
              </button>
            </div>

            {/* Trust Badges */}
            <div className="flex items-center justify-center space-x-4">
              <div className="px-3 py-1 bg-white/5 rounded-full text-xs text-gray-400">🔒 SOC2 Type II</div>
              <div className="px-3 py-1 bg-white/5 rounded-full text-xs text-gray-400">🛡️ GDPR</div>
              <div className="px-3 py-1 bg-white/5 rounded-full text-xs text-gray-400">⛓️ Blockchain</div>
            </div>
          </div>
        </div>
      </div>

      {/* Custom Styles */}
      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .animate-blob {
          animation: blob 7s infinite;
        }
        
        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
        
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        
        .bg-pattern {
          background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
        
        select option {
          background-color: #1f2937;
          color: white;
        }
      `}</style>
    </div>
  );
};

export default JoinNetwork;
