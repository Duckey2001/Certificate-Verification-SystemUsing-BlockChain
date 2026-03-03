#!/bin/bash

cd ~/lgcse-project/frontend

# Append creative styles to App.css
cat >> src/App.css << 'CSS_EOF'

/* Creative Landing Page Styles */
.creative-landing {
  position: relative;
  overflow-x: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: #f8fafc;
}

/* Animated Background */
.animated-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
}

.floating-certificate {
  position: absolute;
  font-size: 3rem;
  opacity: 0.1;
  animation: float 20s infinite ease-in-out;
}

.floating-certificate:nth-child(1) { top: 10%; left: 5%; }
.floating-certificate:nth-child(2) { top: 20%; right: 10%; }
.floating-certificate:nth-child(3) { bottom: 30%; left: 15%; }
.floating-certificate:nth-child(4) { bottom: 20%; right: 20%; }

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(5deg); }
}

/* Creative Navigation */
.creative-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  backdrop-filter: blur(10px);
  background: rgba(15, 23, 42, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem 0;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
}

.logo-icon {
  font-size: 1.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.logo-pulse {
  position: absolute;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  opacity: 0.3;
  filter: blur(20px);
  animation: pulse-glow 3s infinite;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 0.5; }
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.logo-subtitle {
  font-size: 0.75rem;
  color: #94a3b8;
  letter-spacing: 0.05em;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  position: relative;
  padding: 0.5rem 0;
}

.nav-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.nav-link:hover {
  color: white;
}

.nav-link:hover::after {
  transform: scaleX(1);
}

.nav-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-glow {
  position: relative;
  overflow: hidden;
}

.btn-glow::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.btn-glow:hover::before {
  left: 100%;
}

.mobile-menu-btn {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
}

/* Hero Section */
.hero-section {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
  padding: 8rem 2rem 4rem;
}

.hero-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 9999px;
  padding: 0.5rem 1rem;
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
}

.badge-icon {
  color: #667eea;
}

.hero-title {
  font-size: 3.5rem;
  line-height: 1.1;
  margin-bottom: 1.5rem;
}

.title-line {
  display: block;
}

.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  position: relative;
}

.typing-text {
  display: inline-block;
  overflow: hidden;
  white-space: nowrap;
  animation: typing 3.5s steps(40, end);
}

.cursor {
  display: inline-block;
  animation: blink 1s infinite;
}

@keyframes typing {
  from { width: 0 }
  to { width: 100% }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.hero-subtitle {
  font-size: 1.25rem;
  line-height: 1.6;
  color: #94a3b8;
  margin-bottom: 3rem;
  max-width: 600px;
}

.hero-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 4rem;
}

.btn-icon {
  margin-right: 0.5rem;
}

.hero-stats {
  display: flex;
  gap: 3rem;
}

.stat-card {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

/* Certificate Demo */
.certificate-demo {
  position: relative;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  transform-style: preserve-3d;
  perspective: 1000px;
}

.certificate-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100%;
  background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
  border-radius: 20px;
  filter: blur(40px);
  z-index: -1;
}

.certificate-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.certificate-title h3 {
  font-size: 1.5rem;
  margin: 0;
  color: white;
}

.verified-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 9999px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.verified-badge .badge-icon {
  color: #10b981;
}

.certificate-details {
  margin-bottom: 2rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  color: #94a3b8;
  font-weight: 500;
}

.detail-row .value {
  color: white;
  font-weight: 600;
}

.grade-a {
  color: #10b981;
  font-weight: 700;
  font-size: 1.25rem;
}

.blockchain-proof {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.blockchain-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  color: #94a3b8;
  font-weight: 500;
}

.chain-icon {
  color: #667eea;
}

.blockchain-hash {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  overflow-x: auto;
}

.blockchain-hash code {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: #60a5fa;
  word-break: break-all;
}

.blockchain-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.875rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.active {
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.verification-animation {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #667eea, transparent);
  animation: scan 3s infinite linear;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.verification-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.verification-steps .step {
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
  transition: all 0.3s;
}

.verification-steps .step.active {
  color: #667eea;
  transform: scale(1.1);
}

.scroll-indicator {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.875rem;
  animation: bounce 2s infinite;
}

.mouse {
  width: 30px;
  height: 50px;
  border: 2px solid #94a3b8;
  border-radius: 15px;
  position: relative;
}

.wheel {
  width: 4px;
  height: 8px;
  background: #94a3b8;
  border-radius: 2px;
  position: absolute;
  top: 10px;
  left: 50%;
  transform: translateX(-50%);
  animation: scroll 2s infinite;
}

@keyframes scroll {
  0% { top: 10px; opacity: 1; }
  100% { top: 30px; opacity: 0; }
}

@keyframes bounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(10px); }
}

/* Features Section */
.features-section {
  padding: 8rem 2rem;
  position: relative;
  z-index: 1;
}

.section-header {
  text-align: center;
  margin-bottom: 4rem;
}

.section-badge {
  display: inline-block;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 0.5rem 1.5rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: white;
}

.section-header p {
  font-size: 1.125rem;
  color: #94a3b8;
  max-width: 600px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 20px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--feature-color);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.feature-card.hovered::before {
  transform: scaleX(1);
}

.feature-card.hovered {
  transform: translateY(-10px);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.feature-icon {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  margin-bottom: 1.5rem;
  color: white;
}

.feature-content h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: white;
}

.feature-content p {
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.feature-stats {
  margin-top: 1rem;
}

.stats-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.feature-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200px;
  height: 200px;
  background: var(--feature-color);
  opacity: 0.1;
  filter: blur(60px);
  z-index: -1;
  transition: all 0.3s ease;
}

.feature-card.hovered .feature-glow {
  opacity: 0.2;
  filter: blur(80px);
}

/* Interactive Demo */
.interactive-demo {
  padding: 8rem 2rem;
  background: rgba(15, 23, 42, 0.5);
  position: relative;
  z-index: 1;
}

.demo-container {
  max-width: 1200px;
  margin: 0 auto;
}

.demo-header {
  text-align: center;
  margin-bottom: 4rem;
}

.demo-header h2 {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: white;
}

.demo-header p {
  font-size: 1.125rem;
  color: #94a3b8;
}

.demo-content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 4rem;
}

.demo-steps {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.demo-step {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.step-number {
  width: 40px;
  height: 40px;
  background: rgba(102, 126, 234, 0.1);
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #667eea;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.step-content h3 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  color: white;
}

.step-content p {
  color: #94a3b8;
  font-size: 0.875rem;
  line-height: 1.6;
}

.demo-area {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 20px;
  padding: 3rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.upload-zone {
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  margin-bottom: 3rem;
  transition: all 0.3s;
}

.upload-zone:hover {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.05);
}

.upload-icon {
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.5;
}

.upload-zone h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: white;
}

.upload-zone p {
  color: #94a3b8;
  margin-bottom: 1.5rem;
}

.supported-formats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1.5rem;
  color: #64748b;
  font-size: 0.875rem;
}

.demo-result {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 16px;
  padding: 2rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.result-header h3 {
  font-size: 1.5rem;
  margin: 0;
  color: white;
}

.result-status {
  padding: 0.5rem 1.5rem;
  border-radius: 9999px;
  font-weight: 600;
  font-size: 0.875rem;
}

.result-status.verified {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.result-content {
  margin-bottom: 2rem;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-item:last-child {
  border-bottom: none;
}

.result-item .label {
  color: #94a3b8;
}

.result-item .value {
  color: white;
  font-weight: 600;
}

.result-item .value.success {
  color: #10b981;
}

/* CTA Section */
.cta-section {
  padding: 8rem 2rem;
  position: relative;
  z-index: 1;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.cta-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.cta-content h2 {
  font-size: 3.5rem;
  margin-bottom: 1.5rem;
  color: white;
}

.cta-content p {
  font-size: 1.25rem;
  color: #94a3b8;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.cta-features {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}

.cta-features .feature {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #cbd5e1;
  font-weight: 500;
}

.feature-icon {
  color: #10b981;
}

.cta-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 4rem;
}

.trust-badges {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.trust-badges .badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  padding: 0.5rem 1.5rem;
  font-size: 0.875rem;
  color: #94a3b8;
}

/* Creative Footer */
.creative-footer {
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 4rem 2rem 2rem;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-main {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 4rem;
  margin-bottom: 3rem;
}

.footer-brand .logo {
  margin-bottom: 1rem;
}

.footer-tagline {
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.social-links {
  display: flex;
  gap: 1rem;
}

.social-link {
  color: #94a3b8;
  text-decoration: none;
  transition: color 0.3s;
}

.social-link:hover {
  color: white;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
}

.link-group h4 {
  color: white;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.link-group a {
  display: block;
  color: #94a3b8;
  text-decoration: none;
  margin-bottom: 0.5rem;
  transition: color 0.3s;
  font-size: 0.875rem;
}

.link-group a:hover {
  color: white;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #64748b;
  font-size: 0.875rem;
}

.blockchain-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .hero-container,
  .demo-content,
  .footer-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
  
  .footer-links {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
}

@media (max-width: 768px) {
  .nav-links {
    display: none;
  }
  
  .mobile-menu-btn {
    display: block;
  }
  
  .hero-actions,
  .cta-actions {
    flex-direction: column;
  }
  
  .hero-stats {
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .footer-bottom {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
}

/* Dashboard Enhancements */
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

.sidebar {
  width: 280px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  color: white;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header .logo {
  margin-bottom: 1rem;
}

.user-badge {
  display: inline-block;
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
}

.nav-section {
  margin-bottom: 2rem;
}

.nav-section-title {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 1rem;
  padding-left: 0.5rem;
}

.sidebar-nav ul {
  list-style: none;
}

.sidebar-nav li {
  margin-bottom: 0.5rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  color: #cbd5e1;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.3s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.nav-link.active {
  background: rgba(102, 126, 234, 0.2);
  color: white;
  border-left: 3px solid #667eea;
}

.nav-icon {
  font-size: 1.25rem;
}

.action-link {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  font: inherit;
  cursor: pointer;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.system-status,
.blockchain-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator.active {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

.main-header {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
}

.breadcrumb .current-page {
  color: #1e293b;
  font-weight: 600;
}

.breadcrumb .separator {
  opacity: 0.5;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.notifications-container {
  position: relative;
}

.notifications-btn {
  position: relative;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.3s;
}

.notifications-btn:hover {
  background: #f1f5f9;
}

.notification-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: #ef4444;
  color: white;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  min-width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notifications-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 350px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  margin-top: 0.5rem;
  z-index: 1000;
}

.notifications-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.notifications-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.clear-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 0.875rem;
  cursor: pointer;
}

.clear-btn:hover {
  color: #1e293b;
}

.notifications-list {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;
  transition: background 0.3s;
}

.notification-item:hover {
  background: #f8fafc;
}

.notification-item.read {
  opacity: 0.6;
}

.notification-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.notification-content {
  flex: 1;
}

.notification-message {
  margin: 0;
  color: #1e293b;
  font-size: 0.875rem;
  line-height: 1.4;
}

.notification-time {
  display: block;
  margin-top: 0.25rem;
  color: #94a3b8;
  font-size: 0.75rem;
}

.no-notifications {
  padding: 2rem 1.5rem;
  text-align: center;
  color: #94a3b8;
}

.user-menu-container {
  position: relative;
}

.user-menu-btn {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.3s;
}

.user-menu-btn:hover {
  background: #f1f5f9;
}

.user-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.25rem;
}

.user-info {
  text-align: left;
}

.user-name {
  display: block;
  font-weight: 600;
  color: #1e293b;
}

.user-email {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
}

.dropdown-arrow {
  color: #64748b;
  font-size: 0.75rem;
}

.user-menu-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  margin-top: 0.5rem;
  z-index: 1000;
}

.user-menu-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  gap: 1rem;
  align-items: center;
}

.menu-avatar {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.menu-user-info h4 {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.menu-user-info p {
  margin: 0.25rem 0;
  color: #64748b;
  font-size: 0.875rem;
}

.user-role-badge {
  display: inline-block;
  background: #e0f2fe;
  color: #0369a1;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-top: 0.5rem;
}

.user-menu-items {
  padding: 0.5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #1e293b;
  font-size: 0.875rem;
  transition: background 0.3s;
  text-align: left;
}

.menu-item:hover {
  background: #f1f5f9;
}

.menu-icon {
  font-size: 1.25rem;
  opacity: 0.7;
}

.menu-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 0.5rem 1rem;
}

.logout-item {
  color: #dc2626;
}

.logout-item .menu-icon {
  color: #dc2626;
}

.page-content {
  flex: 1;
  padding: 2rem;
  background: #f8fafc;
}

.main-footer {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #64748b;
  font-size: 0.875rem;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.footer-separator {
  opacity: 0.5;
}

/* Interactive Elements */
.glow-on-hover {
  position: relative;
  overflow: hidden;
}

.glow-on-hover::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.glow-on-hover:hover::after {
  left: 100%;
}

/* Loading Animations */
.loading-pulse {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

/* Certificate Preview Animation */
.certificate-preview {
  position: relative;
  overflow: hidden;
}

.certificate-preview::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: shine 3s infinite;
}

@keyframes shine {
  0% { left: -100%; }
  100% { left: 100%; }
}

/* Blockchain Connection Animation */
.blockchain-connection {
  position: relative;
}

.blockchain-connection::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #10b981, #3b82f6, #8b5cf6);
  background-size: 200% 100%;
  animation: flow 2s linear infinite;
}

@keyframes flow {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
CSS_EOF

echo "✅ Creative styles added!"
