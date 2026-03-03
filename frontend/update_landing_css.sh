#!/bin/bash

cd ~/lgcse-project/frontend

# Append new CSS for landing page
cat >> src/App.css << 'CSS_EOF'

/* Professional Landing Page Styles */
.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  font-size: 0.875rem;
  color: #6b7280;
  margin-left: 1rem;
  padding-left: 1rem;
  border-left: 2px solid #e5e7eb;
}

.hero {
  padding: 6rem 0;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 50%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0.05;
  clip-path: polygon(100% 0, 0 0, 100% 100%);
}

.hero-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.hero-title {
  font-size: 3.5rem;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  color: #1f2937;
}

.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  line-height: 1.6;
  color: #4b5563;
  margin-bottom: 2rem;
}

.hero-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 3rem;
}

.hero-stats {
  display: flex;
  gap: 2rem;
}

.stat {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.stat-label {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.5rem;
}

.certificate-card {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  transform: perspective(1000px) rotateY(-5deg);
  transition: transform 0.3s ease;
}

.certificate-card:hover {
  transform: perspective(1000px) rotateY(0deg);
}

.certificate-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.certificate-icon {
  font-size: 3rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.certificate-title h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
}

.certificate-title p {
  margin: 0;
  color: #6b7280;
  font-size: 0.875rem;
}

.certificate-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.detail:last-child {
  border-bottom: none;
}

.detail .label {
  color: #6b7280;
  font-weight: 500;
}

.detail .value {
  color: #1f2937;
  font-weight: 600;
}

.status {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status.verified {
  background-color: #d1fae5;
  color: #065f46;
}

.blockchain-hash {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.hash {
  display: block;
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: #374151;
  word-break: break-all;
  margin-top: 0.5rem;
}

.trusted-by {
  padding: 3rem 0;
  background-color: white;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
}

.trusted-label {
  text-align: center;
  color: #6b7280;
  margin-bottom: 2rem;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.institutions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 2rem;
}

.institution {
  padding: 0.75rem 1.5rem;
  background-color: #f9fafb;
  border-radius: 8px;
  color: #4b5563;
  font-weight: 500;
  transition: all 0.2s;
}

.institution:hover {
  background-color: #f3f4f6;
  transform: translateY(-2px);
}

.features {
  padding: 6rem 0;
  background-color: #f8fafc;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-header h2 {
  font-size: 2.5rem;
  color: #1f2937;
  margin-bottom: 1rem;
}

.section-header p {
  color: #6b7280;
  font-size: 1.125rem;
  max-width: 600px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.feature-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-color: #667eea;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
  display: inline-block;
}

.feature-card h3 {
  font-size: 1.5rem;
  color: #1f2937;
  margin-bottom: 1rem;
}

.feature-card p {
  color: #4b5563;
  line-height: 1.6;
}

.how-it-works {
  padding: 6rem 0;
  background-color: white;
}

.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 3rem;
  position: relative;
}

.steps::before {
  content: '';
  position: absolute;
  top: 40px;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  z-index: 1;
}

.step {
  position: relative;
  z-index: 2;
  background: white;
}

.step-number {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1.5rem;
  border: 8px solid white;
  box-shadow: 0 0 0 4px #e2e8f0;
}

.step-content h3 {
  font-size: 1.5rem;
  color: #1f2937;
  margin-bottom: 1rem;
}

.step-content p {
  color: #4b5563;
  line-height: 1.6;
}

.use-cases {
  padding: 6rem 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.use-cases .section-header h2,
.use-cases .section-header p {
  color: white;
}

.case-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.case-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.case-card:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-4px);
}

.case-icon {
  font-size: 2.5rem;
  margin-bottom: 1.5rem;
}

.case-card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: white;
}

.case-card p {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
}

.cta-section {
  padding: 8rem 0;
  background-color: #f8fafc;
  text-align: center;
}

.cta-content h2 {
  font-size: 3rem;
  color: #1f2937;
  margin-bottom: 1.5rem;
}

.cta-content p {
  font-size: 1.25rem;
  color: #4b5563;
  max-width: 600px;
  margin: 0 auto 3rem;
}

.cta-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 3rem;
}

.cta-features {
  display: flex;
  justify-content: center;
  gap: 2rem;
  flex-wrap: wrap;
}

.cta-features .feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6b7280;
  font-weight: 500;
}

.footer {
  background-color: #111827;
  color: white;
  padding: 4rem 0 2rem;
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 3rem;
  margin-bottom: 3rem;
}

.footer-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.footer-logo .logo-icon {
  font-size: 1.5rem;
}

.footer-logo .logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.footer-description {
  color: #9ca3af;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-link {
  color: #9ca3af;
  text-decoration: none;
  transition: color 0.2s;
}

.social-link:hover {
  color: white;
}

.footer-section h4 {
  color: white;
  margin-bottom: 1.5rem;
  font-size: 1.125rem;
}

.footer-section a {
  display: block;
  color: #9ca3af;
  margin-bottom: 0.75rem;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-section a:hover {
  color: white;
}

.footer-section p {
  color: #9ca3af;
  margin-bottom: 0.75rem;
  line-height: 1.6;
}

.footer-bottom {
  padding-top: 2rem;
  border-top: 1px solid #374151;
  text-align: center;
  color: #9ca3af;
  font-size: 0.875rem;
}

.blockchain-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 9999px;
  color: #667eea;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .hero-content {
    grid-template-columns: 1fr;
    text-align: center;
  }
  
  .hero-visual {
    order: -1;
  }
  
  .certificate-card {
    transform: none;
    max-width: 500px;
    margin: 0 auto;
  }
  
  .steps::before {
    display: none;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-buttons,
  .cta-buttons {
    flex-direction: column;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .nav-links {
    display: none;
  }
  
  .institutions {
    flex-direction: column;
    align-items: center;
  }
}
CSS_EOF

echo "✅ Professional landing page created!"
