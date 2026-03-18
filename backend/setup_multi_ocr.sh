#!/bin/bash

# Multi-OCR API Setup Script for LGCSE Certificate Verification System

echo "=== Multi-OCR API Setup Script ==="
echo "Setting up OCR services for enhanced certificate processing..."

# Check if required packages are installed
echo "Checking dependencies..."

# Install Google Cloud Vision client
if ! pip show google-cloud-vision > /dev/null 2>&1; then
    echo "Installing Google Cloud Vision API client..."
    pip install google-cloud-vision
else
    echo "✓ Google Cloud Vision API client already installed"
fi

# Install required packages for multi-OCR
if ! pip show requests > /dev/null 2>&1; then
    echo "Installing requests library..."
    pip install requests
else
    echo "✓ Requests library already installed"
fi

# Check Tesseract installation
if ! command -v tesseract &> /dev/null; then
    echo "⚠️  Tesseract OCR not found. Installing..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    elif command -v yum &> /dev/null; then
        sudo yum install -y tesseract tesseract-langpack-eng
    elif command -v brew &> /dev/null; then
        brew install tesseract
    else
        echo "❌ Could not install Tesseract automatically. Please install it manually."
        exit 1
    fi
else
    echo "✓ Tesseract OCR already installed"
fi

# Install pytesseract Python wrapper
if ! pip show pytesseract > /dev/null 2>&1; then
    echo "Installing pytesseract Python wrapper..."
    pip install pytesseract
else
    echo "✓ pytesseract already installed"
fi

# Install Pillow for image processing
if ! pip show Pillow > /dev/null 2>&1; then
    echo "Installing Pillow for image processing..."
    pip install Pillow
else
    echo "✓ Pillow already installed"
fi

echo ""
echo "=== OCR Services Configuration ==="

echo "1. Google Cloud Vision API:"
echo "   - Free tier: 1000 units/month"
echo "   - Setup: https://console.cloud.google.com/apis/credentials"
echo "   - Enable: Cloud Vision API"
echo "   - Create API key and add to .env as GOOGLE_CLOUD_VISION_API_KEY"

echo ""
echo "2. Kolosal AI OCR:"
echo "   - 100% free, no API key required"
echo "   - Auto-detects languages"
echo "   - Good for blurry documents"

echo ""
echo "3. OCR.space API:"
echo "   - Already configured with key: 8195ce015388957"
echo "   - Free tier: 5MB file limit"

echo ""
echo "4. Tesseract OCR:"
echo "   - Open-source, offline processing"
echo "   - Multiple language support"

echo ""
echo "=== Environment Configuration ==="
echo "Update your .env file with:"
echo "GOOGLE_CLOUD_VISION_API_KEY=your_google_cloud_vision_api_key_here"
echo "OCR_PREFERRED_API=auto"
echo "OCR_FALLBACK_ENABLED=true"
echo "OCR_CONFIDENCE_THRESHOLD=70"

echo ""
echo "=== Testing Multi-OCR Integration ==="
echo "Run the backend and test with:"
echo "curl -X POST 'http://localhost:8000/api/ocr/ocr-status'"
echo ""
echo "Test certificate processing:"
echo "curl -X POST -F 'file=@certificate.jpg' -F 'prefer_api=auto' 'http://localhost:8000/api/ocr/extract-certificate-data'"

echo ""
echo "=== Setup Complete ==="
echo "Your LGCSE Certificate Verification System now supports multiple OCR engines:"
echo "- Automatic API selection based on confidence scores"
echo "- Fallback mechanisms for reliability"
echo "- Real-time API comparison"
echo "- Enhanced accuracy for certificate processing"

echo ""
echo "Next steps:"
echo "1. Get Google Cloud Vision API key for best accuracy"
echo "2. Test with sample LGCSE certificates"
echo "3. Monitor performance in the dashboard"
echo "4. Adjust confidence thresholds as needed"
