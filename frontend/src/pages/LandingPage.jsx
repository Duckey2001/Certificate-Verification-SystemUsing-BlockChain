import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  const [scrollY, setScrollY] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activePaymentTab, setActivePaymentTab] = useState('once');
  const [verificationQty, setVerificationQty] = useState(1);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      icon: '🔗',
      title: 'Blockchain Security',
      metric: '100% Tamper-Proof',
      gradient: 'from-blue-600 to-indigo-600',
      description: 'Certificate hashes anchored to decentralized blockchain networks for immutable proof of authenticity',
      details: ['SHA-256 cryptographic hashing', 'Multi-chain support', 'Permanent audit trail', 'Instant verification'],
      color: 'blue'
    },
    {
      icon: '🤖',
      title: 'AI-Powered OCR',
      metric: '99.9% Accuracy',
      gradient: 'from-purple-600 to-pink-600',
      description: 'Advanced machine learning models extract and validate certificate data with exceptional accuracy',
      details: ['Text extraction from PDFs', 'Handwriting recognition', 'Automatic validation', 'Multi-language support'],
      color: 'purple'
    },
    {
      icon: '⚡',
      title: 'Real-time Verification',
      metric: '< 2 Seconds',
      gradient: 'from-green-500 to-emerald-600',
      description: 'Instant cross-referencing against blockchain records with comprehensive verification reports',
      details: ['Instant blockchain lookup', 'Automated matching', 'Detailed verification logs', 'Shareable links'],
      color: 'green'
    },
    {
      icon: '🌐',
      title: 'Enterprise Integration',
      metric: '99.99% Uptime',
      gradient: 'from-orange-500 to-red-600',
      description: 'Seamlessly integrate with existing systems through robust APIs and webhooks',
      details: ['RESTful API architecture', 'Webhook notifications', 'Bulk verification', 'Custom integration'],
      color: 'orange'
    }
  ];

  const stats = [
    { icon: '📜', change: '+127%', value: '50K+', label: 'Certificates Verified' },
    { icon: '🏛️', change: '+43%', value: '500+', label: 'Active Institutions' },
    { icon: '✓', change: '+2.1%', value: '99.9%', label: 'Accuracy Rate' },
    { icon: '⚡', change: '-35%', value: '<2s', label: 'Response Time' }
  ];

  const useCases = [
    {
      icon: '🎓',
      title: 'Educational Institutions',
      gradient: 'from-blue-600 to-indigo-600',
      description: 'Issue and verify certificates for thousands of students with blockchain security',
      benefits: ['Bulk certificate generation', 'Student portal access', 'Academic integrity']
    },
    {
      icon: '💼',
      title: 'Employers & HR',
      gradient: 'from-purple-600 to-pink-600',
      description: 'Verify candidate credentials instantly during recruitment and onboarding',
      benefits: ['Instant background checks', 'Fraud prevention', 'Compliance tracking']
    },
    {
      icon: '🏛️',
      title: 'Government Agencies',
      gradient: 'from-green-500 to-emerald-600',
      description: 'Validate educational qualifications for licensing and regulatory compliance',
      benefits: ['Regulatory compliance', 'Audit trails', 'Inter-agency sharing']
    }
  ];

  const testimonials = [
    {
      quote: "CertiVert has revolutionized how we verify certificates. The blockchain integration gives us complete confidence in the results.",
      author: "Dr. Sarah Johnson",
      role: "Director of Academics, University of Technology",
      avatar: "👩‍🏫"
    },
    {
      quote: "The AI-powered extraction saves us hours of manual work. It's incredibly accurate and user-friendly.",
      author: "Michael Chen",
      role: "HR Director, Global Corp",
      avatar: "👨‍💼"
    },
    {
      quote: "As a regulatory body, we needed a solution we could trust. CertiVert delivers with enterprise-grade security.",
      author: "Elizabeth Moyo",
      role: "Chief Examiner, Education Council",
      avatar: "👩‍⚖️"
    }
  ];

  const totalAmount = verificationQty * 50;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0b1020] via-[#131b2c] to-[#0b1020] text-white relative overflow-x-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-pattern opacity-10"></div>
        <div className="absolute top-20 left-10 w-80 h-80 bg-amber-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-40 right-10 w-80 h-80 bg-emerald-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-20 left-1/2 w-80 h-80 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      {/* Navigation */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
        scrollY > 50 ? 'bg-gray-900/80 backdrop-blur-xl border-b border-amber-500/20 shadow-2xl' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 md:h-20">
            {/* Logo */}
            <div className="flex items-center space-x-2 group">
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-r from-amber-500 to-yellow-600 rounded-xl flex items-center justify-center text-2xl transform group-hover:rotate-12 transition duration-300 shadow-lg">
                  🔐
                </div>
                <div className="absolute -inset-1 bg-gradient-to-r from-amber-500 to-yellow-600 rounded-xl blur opacity-40 group-hover:opacity-70 transition"></div>
              </div>
              <span className="text-2xl font-extrabold tracking-tight">
                <span className="bg-gradient-to-r from-amber-300 to-yellow-400 bg-clip-text text-transparent">CertiVert</span>
                <span className="ml-1.5 text-xs align-super bg-gray-800 text-amber-300 px-2 py-0.5 rounded-full border border-amber-500/40">BETA</span>
              </span>
            </div>

            {/* Trust Badge - Desktop */}
            <div className="hidden md:flex items-center gap-3 bg-gray-800/50 px-4 py-2 rounded-full border border-amber-500/30">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute h-full w-full rounded-full bg-amber-400"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
              </span>
              <span className="text-sm text-amber-200 font-medium">Trusted by 500+ Institutions</span>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3">
              <Link to="/login" className="hidden md:block text-gray-300 hover:text-white transition-colors">
                Sign In
              </Link>
              <Link 
                to="/register" 
                className="px-5 py-2 bg-gradient-to-r from-amber-600 to-yellow-600 rounded-xl text-white font-semibold shadow-lg hover:shadow-amber-600/30 transition transform hover:scale-105"
              >
                Get started
              </Link>
              
              {/* Mobile menu button */}
              <button 
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden relative w-10 h-10 focus:outline-none"
                aria-label="Toggle menu"
              >
                <span className={`absolute h-0.5 w-6 bg-white transform transition-all duration-300 ${mobileMenuOpen ? 'rotate-45 top-5' : 'top-3'}`}></span>
                <span className={`absolute h-0.5 w-6 bg-white transform transition-all duration-300 ${mobileMenuOpen ? 'opacity-0' : 'top-5'}`}></span>
                <span className={`absolute h-0.5 w-6 bg-white transform transition-all duration-300 ${mobileMenuOpen ? '-rotate-45 top-5' : 'top-7'}`}></span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        <div className={`md:hidden transition-all duration-500 overflow-hidden ${
          mobileMenuOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}>
          <div className="px-4 py-6 bg-gray-800/90 backdrop-blur-lg border-t border-gray-700 space-y-4">
            <Link to="/features" className="block text-gray-300 hover:text-white py-2">Features</Link>
            <Link to="/solutions" className="block text-gray-300 hover:text-white py-2">Solutions</Link>
            <Link to="/pricing" className="block text-gray-300 hover:text-white py-2">Pricing</Link>
            <Link to="/contact" className="block text-gray-300 hover:text-white py-2">Contact</Link>
            <div className="pt-4 flex flex-col space-y-3">
              <Link to="/login" className="px-6 py-3 text-gray-300 hover:text-white text-center">Sign In</Link>
              <Link to="/register" className="px-6 py-3 bg-gradient-to-r from-amber-600 to-yellow-600 rounded-xl text-white font-medium text-center">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-28 md:pt-36 pb-12 px-4 z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Column */}
            <div className="space-y-6">
              {/* Mobile Trust Badge */}
              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-800/70 backdrop-blur-sm rounded-full border border-amber-500/30 md:hidden">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute h-full w-full rounded-full bg-amber-400"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                </span>
                <span className="text-sm text-amber-200">Trusted by 500+ Institutions</span>
              </div>

              <h1 className="text-4xl md:text-6xl font-black leading-tight">
                <span className="block text-white">Secure LGCSE</span>
                <span className="bg-gradient-to-r from-amber-300 via-yellow-400 to-orange-400 bg-clip-text text-transparent">
                  Certificate Verification
                </span>
              </h1>

              <p className="text-lg text-gray-400 max-w-xl">
                CertiVert combines blockchain technology with AI-powered data extraction 
                to provide tamper-proof verification for educational certificates.
              </p>

              <div className="flex flex-wrap gap-4 pt-2">
                <Link 
                  to="/register" 
                  className="px-8 py-4 bg-gradient-to-r from-amber-600 to-yellow-600 rounded-xl text-white font-bold shadow-xl hover:shadow-amber-500/30 transition flex items-center gap-2"
                >
                  <span>Start Free Trial</span>
                  <span>✨</span>
                </Link>
                <Link 
                  to="/demo" 
                  className="px-8 py-4 bg-gray-800 hover:bg-gray-700 rounded-xl font-semibold border border-gray-700 transition"
                >
                  Watch Demo
                </Link>
              </div>

              {/* Institution Icons */}
              <div className="flex items-center space-x-6 pt-4 text-gray-300">
                <div className="flex -space-x-3">
                  <span className="w-8 h-8 rounded-full bg-amber-700/60 border-2 border-gray-800 flex items-center justify-center text-sm">🏛️</span>
                  <span className="w-8 h-8 rounded-full bg-amber-600/60 border-2 border-gray-800 flex items-center justify-center text-sm">🎓</span>
                  <span className="w-8 h-8 rounded-full bg-amber-500/60 border-2 border-gray-800 flex items-center justify-center text-sm">💼</span>
                  <span className="w-8 h-8 rounded-full bg-amber-400/60 border-2 border-gray-800 flex items-center justify-center text-sm">🏫</span>
                </div>
                <span className="text-sm">
                  <span className="font-bold text-white">50K+</span> certificates verified
                </span>
              </div>
            </div>

            {/* Right Column - Live Preview Card */}
            <div className="relative">
              <div className="bg-gray-800/50 backdrop-blur-xl rounded-3xl border border-amber-500/30 p-5 shadow-2xl">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-300 flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span> 
                    Live Verification
                  </span>
                  <span className="text-xs text-gray-500">ID: VRF-2024-001</span>
                </div>

                <div className="bg-gray-900/70 rounded-2xl p-4 border border-gray-700">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-amber-500 to-orange-500 rounded-xl flex items-center justify-center text-xl">📜</div>
                    <div>
                      <h4 className="font-semibold">LGCSE Certificate</h4>
                      <p className="text-xs text-gray-400">Computer Science · 2024</p>
                    </div>
                    <span className="ml-auto px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full border border-green-500/30">
                      ✓ Verified
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                    <div>
                      <span className="text-gray-500 text-xs">Student</span>
                      <p className="font-medium">Sarah Johnson</p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">Student ID</span>
                      <p className="font-medium">LGCSE2024001</p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">Grade</span>
                      <p className="text-amber-400 font-bold">A+ (95%)</p>
                    </div>
                    <div>
                      <span className="text-gray-500 text-xs">Issue Date</span>
                      <p className="font-medium">Jan 15, 2024</p>
                    </div>
                  </div>

                  <div className="bg-gray-800 rounded-xl p-3 border border-gray-600">
                    <div className="flex items-center gap-1 text-xs text-gray-400 mb-1">
                      <span>⛓️</span>Blockchain Verification
                    </div>
                    <div className="flex items-center justify-between bg-gray-900 rounded-lg p-2">
                      <code className="text-xs text-amber-400">0x8a3f...e7f8</code>
                      <span className="px-2 py-0.5 bg-green-500/10 text-green-400 text-xs rounded-full">Confirmed</span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Network: Ethereum</span>
                      <span>Block: #19,482,301</span>
                    </div>
                  </div>
                </div>

                {/* Progress Steps */}
                <div className="mt-6 flex justify-between">
                  {[
                    { icon: '✓', label: 'Upload', active: true },
                    { icon: '✓', label: 'Extract', active: true },
                    { icon: '⛓️', label: 'Verify', active: true },
                    { icon: '✅', label: 'Complete', active: false }
                  ].map((step, i) => (
                    <div key={i} className="flex flex-col items-center">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                        step.active 
                          ? i === 2 
                            ? 'bg-amber-500/20 text-amber-400' 
                            : 'bg-green-500/20 text-green-400'
                          : 'bg-gray-700 text-gray-400'
                      }`}>
                        {step.icon}
                      </span>
                      <span className={`text-xs mt-1 ${step.active ? 'text-gray-300' : 'text-gray-500'}`}>
                        {step.label}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-8 px-4 relative z-10">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-5">
          {stats.map((stat, index) => (
            <div key={index} className="bg-gray-800/30 backdrop-blur-md rounded-2xl p-5 border border-gray-700 hover:border-amber-500/30 transition-all duration-300 transform hover:-translate-y-1">
              <div className="flex items-center justify-between w-full">
                <span className="text-3xl">{stat.icon}</span>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                  stat.change.startsWith('+') ? 'bg-green-500/10 text-green-400' : 'bg-blue-500/10 text-blue-400'
                }`}>
                  {stat.change}
                </span>
              </div>
              <div className="text-3xl font-bold mt-2">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Header */}
      <div className="max-w-7xl mx-auto px-4 pt-12 text-center">
        <span className="inline-block px-4 py-1.5 bg-gray-800/70 rounded-full border border-amber-500/30 text-sm text-amber-300 mb-4">
          Platform Features
        </span>
        <h2 className="text-4xl md:text-5xl font-bold">
          <span className="bg-gradient-to-r from-amber-300 to-yellow-300 bg-clip-text text-transparent">
            Comprehensive Verification
          </span>
          <br />Solutions
        </h2>
        <p className="text-gray-400 mt-4 max-w-2xl mx-auto">
          Everything you need to issue, manage, and verify certificates securely
        </p>
      </div>

      {/* Features Grid */}
      <section className="py-12 px-4 max-w-7xl mx-auto grid md:grid-cols-2 gap-6">
        {features.map((feature, index) => (
          <div key={index} className="group bg-gray-800/30 backdrop-blur-sm rounded-3xl p-7 border border-gray-700 hover:border-amber-500/40 transition-all duration-300 transform hover:-translate-y-2">
            <div className="flex items-center justify-between">
              <span className={`w-14 h-14 bg-gradient-to-r ${feature.gradient} rounded-xl flex items-center justify-center text-3xl transform group-hover:rotate-6 transition duration-300`}>
                {feature.icon}
              </span>
              <span className="px-3 py-1 bg-gray-700/70 rounded-full text-sm font-medium text-amber-300">
                {feature.metric}
              </span>
            </div>
            <h3 className="text-2xl font-bold mt-4">{feature.title}</h3>
            <p className="text-gray-400 text-sm mt-1">{feature.description}</p>
            <ul className="mt-4 space-y-2 text-sm text-gray-300">
              {feature.details.map((detail, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 bg-gradient-to-r ${feature.gradient} rounded-full`}></span>
                  {detail}
                </li>
              ))}
            </ul>
            <Link to="/features" className="mt-5 inline-flex items-center gap-1 text-amber-400 text-sm group/link">
              Learn more 
              <span className="group-hover/link:translate-x-1 transition-transform">→</span>
            </Link>
          </div>
        ))}
      </section>

      {/* Use Cases Header */}
      <div className="max-w-7xl mx-auto px-4 pt-12 text-center">
        <span className="inline-block px-4 py-1.5 bg-gray-800/70 rounded-full border border-purple-500/30 text-sm text-purple-300 mb-4">
          Use Cases
        </span>
        <h2 className="text-4xl md:text-5xl font-bold">
          <span className="bg-gradient-to-r from-purple-300 to-pink-300 bg-clip-text text-transparent">
            Tailored Solutions
          </span>
          <br />for Every Stakeholder
        </h2>
      </div>

      {/* Use Cases Grid */}
      <section className="py-12 px-4 max-w-7xl mx-auto grid md:grid-cols-3 gap-6">
        {useCases.map((useCase, index) => (
          <div key={index} className="group bg-gray-800/30 rounded-3xl border border-gray-700 overflow-hidden hover:border-amber-500/30 transition-all duration-300 transform hover:-translate-y-2">
            <div className={`h-32 bg-gradient-to-r ${useCase.gradient} p-5 relative overflow-hidden`}>
              <div className="absolute inset-0 bg-black/20"></div>
              <span className="text-5xl relative z-10">{useCase.icon}</span>
              <h3 className="text-xl font-bold mt-1 relative z-10">{useCase.title}</h3>
            </div>
            <div className="p-5">
              <p className="text-gray-400 text-sm">{useCase.description}</p>
              <ul className="mt-4 space-y-1 text-sm text-gray-300">
                {useCase.benefits.map((benefit, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-green-400">✓</span>
                    {benefit}
                  </li>
                ))}
              </ul>
              <Link to="/solutions" className="inline-block mt-4 text-amber-400 hover:text-amber-300 transition-colors">
                Learn more →
              </Link>
            </div>
          </div>
        ))}
      </section>

      {/* Integration Section */}
      <section className="py-16 px-4 max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <span className="px-4 py-1.5 bg-gray-800/70 rounded-full border border-green-500/30 text-green-300 text-sm">
              Seamless Integration
            </span>
            <h2 className="text-4xl font-bold mt-4">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-300 to-blue-300">
                Works with Your
              </span>
              <br />Existing Systems
            </h2>
            <p className="text-gray-400 mt-4">
              Simple API integration that connects with your student information systems, 
              HR platforms, and verification portals.
            </p>

            {/* Code Block */}
            <div className="bg-gray-900 rounded-2xl border border-gray-700 mt-6 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                <span className="text-xs text-gray-400">JavaScript</span>
                <button className="text-xs text-gray-400 hover:text-white transition-colors">Copy</button>
              </div>
              <pre className="p-4 text-xs text-gray-300 overflow-x-auto">
                <code>
{`// Verify a certificate
const result = await certivert.verify({
  certificateId: "LGCSE2024001",
  blockchain: "ethereum",
  includeDetails: true
});

console.log(result);
// {
//   verified: true,
//   timestamp: "2024-01-15T10:30:00Z",
//   student: "Sarah Johnson",
//   hash: "0x8a3f..."
// }`}
                </code>
              </pre>
            </div>
            <Link to="/docs" className="inline-block mt-4 text-blue-400 hover:text-blue-300 transition-colors">
              Read Documentation →
            </Link>
          </div>

          {/* Integration Icons */}
          <div className="grid grid-cols-2 gap-4 p-6 bg-gray-800/30 rounded-3xl border border-gray-700">
            {[
              { icon: '🏫', label: 'SIS' },
              { icon: '💼', label: 'HRIS' },
              { icon: '📱', label: 'Mobile' },
              { icon: '🌐', label: 'Portal' }
            ].map((item, i) => (
              <div key={i} className="bg-gray-900/50 p-4 text-center rounded-xl border border-gray-700 hover:border-amber-500/30 transition">
                <span className="text-3xl">{item.icon}</span>
                <div className="text-sm mt-1 text-gray-300">{item.label}</div>
              </div>
            ))}
            <div className="col-span-2 bg-gradient-to-r from-amber-600 to-yellow-600 p-4 rounded-xl text-center font-bold shadow-lg">
              ⛓️ CertiVert API
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <div className="max-w-7xl mx-auto px-4 text-center">
        <span className="px-4 py-1.5 bg-gray-800/70 rounded-full border border-yellow-500/30 text-yellow-300 text-sm">
          Testimonials
        </span>
        <h2 className="text-4xl font-bold mt-2 bg-gradient-to-r from-yellow-300 to-orange-300 bg-clip-text text-transparent">
          Trusted by Industry Leaders
        </h2>
      </div>

      <section className="py-12 px-4 max-w-7xl mx-auto grid md:grid-cols-3 gap-6">
        {testimonials.map((testimonial, index) => (
          <div key={index} className="bg-gray-800/30 p-6 rounded-3xl border border-gray-700 hover:border-amber-500/30 transition">
            <div className="flex text-yellow-400 mb-3">
              {[...Array(5)].map((_, i) => (
                <svg key={i} className="w-5 h-5 fill-current" viewBox="0 0 20 20">
                  <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
                </svg>
              ))}
            </div>
            <p className="text-gray-300 italic">"{testimonial.quote}"</p>
            <div className="flex items-center gap-3 mt-4">
              <span className="w-10 h-10 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-center text-xl">
                {testimonial.avatar}
              </span>
              <div>
                <div className="font-semibold">{testimonial.author}</div>
                <div className="text-xs text-gray-400">{testimonial.role}</div>
              </div>
            </div>
          </div>
        ))}
      </section>

      {/* M-Pesa Payment Section */}
      <section className="py-16 px-4 max-w-5xl mx-auto">
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm rounded-3xl border border-amber-500/30 p-8 shadow-2xl">
          <div className="text-center mb-8">
            <span className="inline-block px-4 py-1.5 bg-green-500/20 rounded-full border border-green-500/30 text-green-400 text-sm mb-4">
              💰 M-Pesa · Maloti (LSL)
            </span>
            <h2 className="text-3xl md:text-4xl font-bold">
              <span className="bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
                Pay with M-Pesa
              </span>
            </h2>
            <p className="text-gray-400 mt-2">Instant verification · Zero blockchain fees</p>
          </div>

          {/* Payment Tabs */}
          <div className="flex justify-center gap-4 mb-8 border-b border-gray-700 pb-2">
            <button
              onClick={() => setActivePaymentTab('once')}
              className={`px-6 py-3 font-medium text-lg transition-colors ${
                activePaymentTab === 'once' 
                  ? 'text-amber-400 border-b-2 border-amber-400' 
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              💸 Pay-as-you-go
            </button>
            <button
              onClick={() => setActivePaymentTab('subscription')}
              className={`px-6 py-3 font-medium text-lg transition-colors ${
                activePaymentTab === 'subscription' 
                  ? 'text-amber-400 border-b-2 border-amber-400' 
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              📅 Subscription
              <span className="ml-2 text-xs bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full">save 20%</span>
            </button>
          </div>

          {activePaymentTab === 'once' ? (
            <div className="grid md:grid-cols-2 gap-8 items-center">
              {/* Pay-as-you-go Form */}
              <div className="space-y-5">
                <div>
                  <label className="text-sm text-gray-400 block mb-2">M-Pesa phone number</label>
                  <div className="flex">
                    <span className="inline-flex items-center px-3 bg-gray-700 border border-r-0 border-gray-600 rounded-l-xl text-gray-300">
                      +266
                    </span>
                    <input 
                      type="text" 
                      defaultValue="57123456" 
                      className="w-full bg-gray-700 border border-gray-600 rounded-r-xl px-4 py-3 text-white focus:ring-2 focus:ring-amber-500 outline-none"
                      placeholder="57123456"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-sm text-gray-400 block mb-2">Number of verifications</label>
                  <div className="flex items-center gap-4">
                    <input 
                      type="number" 
                      min="1" 
                      max="100" 
                      value={verificationQty}
                      onChange={(e) => setVerificationQty(parseInt(e.target.value) || 1)}
                      className="w-24 bg-gray-700 border border-gray-600 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-amber-500 outline-none"
                    />
                    <span className="text-gray-300">
                      × <span className="text-amber-400 font-bold">LSL 50</span>
                    </span>
                  </div>
                </div>

                <div className="bg-gray-900/60 p-4 rounded-xl border border-gray-700">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Verification fee</span>
                    <span>LSL {verificationQty * 50}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Blockchain gas</span>
                    <span className="text-green-400">LSL 0</span>
                  </div>
                  <div className="flex justify-between font-bold text-base pt-2 border-t border-gray-700 mt-2">
                    <span>Total due</span>
                    <span className="text-amber-400">LSL {verificationQty * 50}</span>
                  </div>
                </div>

                <button className="w-full py-4 bg-gradient-to-r from-green-600 to-emerald-600 rounded-xl font-bold text-lg shadow-xl hover:shadow-green-500/30 transition flex items-center justify-center gap-3 group">
                  <span>💰 Pay with M-Pesa</span>
                  <span className="group-hover:translate-x-1 transition-transform">→</span>
                </button>

                <p className="text-xs text-gray-500 text-center">
                  You'll receive an STK push on your phone. Verification completes instantly.
                </p>
              </div>

              {/* M-Pesa Mock STK */}
              <div className="hidden md:block">
                <div className="bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700 rounded-3xl p-6 rotate-2 shadow-2xl">
                  <div className="absolute -top-4 -right-4 w-20 h-20 bg-green-500/20 rounded-full blur-2xl"></div>
                  <div className="flex items-center gap-2 mb-4">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    <span className="text-sm">M-Pesa STK push</span>
                  </div>
                  <div className="bg-gray-900 rounded-xl p-5 border border-gray-700">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-4xl">📲</span>
                      <div>
                        <div className="font-medium">Confirm payment</div>
                        <div className="text-xs text-gray-400">CertiVert · LGCSE verification</div>
                      </div>
                    </div>
                    <div className="my-4 text-center">
                      <span className="text-3xl font-bold text-amber-400">LSL {verificationQty * 50}</span>
                    </div>
                    <div className="flex gap-2 justify-center">
                      <span className="bg-gray-800 px-3 py-1 rounded-full text-xs">Enter PIN</span>
                      <span className="bg-gray-800 px-3 py-1 rounded-full text-xs">1:59</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div className="bg-gray-800/40 border border-gray-700 rounded-3xl p-6">
                <span className="bg-purple-500/20 text-purple-300 px-3 py-1 rounded-full text-sm">popular</span>
                <h3 className="text-2xl font-bold mt-3">
                  Institution plan <span className="text-emerald-400">· M-Pesa monthly</span>
                </h3>
                <div className="my-6">
                  <span className="text-5xl font-bold">LSL 2,500</span>
                  <span className="text-gray-400">/month</span>
                </div>
                <ul className="space-y-2 text-gray-300 mb-6">
                  <li className="flex items-center gap-2">✓ Up to 250 verifications</li>
                  <li className="flex items-center gap-2">✓ Bulk certificate upload</li>
                  <li className="flex items-center gap-2">✓ API access & webhooks</li>
                  <li className="flex items-center gap-2">✓ Priority M-Pesa support</li>
                </ul>
                <button className="w-full py-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-bold shadow-lg flex items-center justify-center gap-2 hover:shadow-purple-500/30 transition">
                  Subscribe via M-Pesa <span>📲</span>
                </button>
              </div>
              <div className="text-gray-400 p-4">
                <span className="text-5xl block mb-2">🏦</span>
                <p>Pay annually with M-Pesa and get 2 months free. Over 50 institutions already paying via M-Pesa.</p>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 max-w-5xl mx-auto">
        <div className="bg-gradient-to-r from-amber-600 to-yellow-600 rounded-3xl p-10 text-center relative overflow-hidden">
          <div className="absolute inset-0 bg-black/20"></div>
          <div className="relative">
            <h2 className="text-4xl md:text-5xl font-bold text-white">
              Ready to Transform Certificate Verification?
            </h2>
            <p className="text-xl text-amber-100 mt-4 max-w-2xl mx-auto">
              Join leading institutions using CertiVert to secure and streamline their verification process.
            </p>

            <div className="flex flex-wrap justify-center gap-6 mt-6 text-white">
              <span className="flex items-center gap-2">✓ 14-day free trial</span>
              <span className="flex items-center gap-2">✓ No credit card required</span>
              <span className="flex items-center gap-2">✓ Dedicated support</span>
            </div>

            <div className="flex flex-wrap justify-center gap-4 mt-8">
              <Link 
                to="/register" 
                className="px-8 py-4 bg-white text-gray-900 rounded-xl font-bold shadow-xl hover:shadow-2xl transition transform hover:scale-105"
              >
                Get Started Now
              </Link>
              <Link 
                to="/contact" 
                className="px-8 py-4 border-2 border-white text-white rounded-xl font-bold hover:bg-white/10 transition"
              >
                Contact Sales
              </Link>
            </div>

            <div className="flex flex-wrap gap-6 justify-center mt-8 text-sm text-amber-100">
              <span>🔒 SOC2 Type II</span>
              <span>🛡️ GDPR Compliant</span>
              <span>⛓️ Blockchain Validated</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-12 px-4">
        <div className="max-w-7xl mx-auto grid md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">🔐</span>
              <span className="text-xl font-bold bg-gradient-to-r from-amber-300 to-yellow-300 bg-clip-text text-transparent">
                CertiVert
              </span>
            </div>
            <p className="text-sm text-gray-400">
              Blockchain-powered certificate verification for educational institutions and employers.
            </p>
            <div className="flex gap-4 mt-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">𝕏</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">in</a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">GH</a>
            </div>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Product</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><Link to="/demo" className="hover:text-white transition-colors">Demo</Link></li>
              <li><Link to="/docs" className="hover:text-white transition-colors">Documentation</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Company</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/about" className="hover:text-white transition-colors">About</Link></li>
              <li><Link to="/contact" className="hover:text-white transition-colors">Contact</Link></li>
              <li><Link to="/careers" className="hover:text-white transition-colors">Careers</Link></li>
              <li><Link to="/blog" className="hover:text-white transition-colors">Blog</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-3">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/privacy" className="hover:text-white transition-colors">Privacy</Link></li>
              <li><Link to="/terms" className="hover:text-white transition-colors">Terms</Link></li>
              <li><Link to="/security" className="hover:text-white transition-colors">Security</Link></li>
              <li><Link to="/compliance" className="hover:text-white transition-colors">Compliance</Link></li>
            </ul>
          </div>
        </div>

        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center pt-8 text-sm text-gray-500 border-t border-gray-800 mt-8">
          <div>© {new Date().getFullYear()} CertiVert. All rights reserved.</div>
          <div className="flex items-center gap-2 mt-2 md:mt-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute h-full w-full rounded-full bg-green-400"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            System Status: Operational
          </div>
        </div>
      </footer>

      {/* Styles for animations */}
      <style data-jsx="true">{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(40px, -60px) scale(1.1); }
          66% { transform: translate(-30px, 30px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 10s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .bg-pattern {
          background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23928dab' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
      `}</style>
    </div>
  );
};

export default LandingPage;
