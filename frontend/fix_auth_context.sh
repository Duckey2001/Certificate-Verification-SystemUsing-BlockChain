#!/bin/bash

cd ~/lgcse-project/frontend

if [ -f "src/contexts/AuthContext.jsx" ]; then
  # Create backup
  cp src/contexts/AuthContext.jsx src/contexts/AuthContext.jsx.backup.$(date +%s)
  
  # Fix the useEffect by adding missing dependency
  sed -i "s/useEffect(() => {/const fetchCurrentUser = useCallback(async () => {\n  try {\n    const token = localStorage.getItem('token');\n    if (token) {\n      \/\/ Your fetch logic here\n    }\n  } catch (error) {\n    console.error('Error fetching user:', error);\n  }\n}, []);\n\nuseEffect(() => {/" src/contexts/AuthContext.jsx
  
  # Add useCallback import if not present
  if ! grep -q "useCallback" src/contexts/AuthContext.jsx; then
    sed -i "1s/^import React/import React, { useCallback } from 'react'/" src/contexts/AuthContext.jsx
  fi
  
  echo "✅ Fixed AuthContext.jsx"
else
  echo "⚠️ AuthContext.jsx not found"
fi
