#!/bin/bash

cd ~/lgcse-project/frontend

echo "Updating packages for compatibility..."

# Update key packages
npm install react@^18 react-dom@^18
npm install -D @tailwindcss/postcss@latest tailwindcss@latest
npm install -D postcss@latest autoprefixer@latest
npm install -D react-scripts@latest

# Create fresh package-lock
rm -rf node_modules package-lock.json
npm install

echo "✅ Packages updated"
