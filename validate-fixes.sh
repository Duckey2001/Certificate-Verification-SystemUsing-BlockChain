#!/bin/bash

echo "🔍 Validating all fixes for LGCSE Project..."
echo ""

# 1. Check database configuration
echo "1️⃣ Database Configuration:"
echo "   ✓ backend/.env configured" $(grep -q "diploma_verification" /home/duckey/lgcse-project/backend/.env && echo "✅" || echo "❌")
echo "   ✓ root .env configured" $(grep -q "diploma_verification" /home/duckey/lgcse-project/.env && echo "✅" || echo "❌")
echo "   ✓ VS Code settings configured" $(grep -q "diploma_admin" /home/duckey/lgcse-project/.vscode/settings.json && echo "✅" || echo "❌")

# 2. Check frontend API methods
echo ""
echo "2️⃣ Frontend API Methods:"
echo "   ✓ getPendingUsers" $(grep -q "getPendingUsers" /home/duckey/lgcse-project/frontend/src/api/adminApi.js && echo "✅" || echo "❌")
echo "   ✓ approveUser" $(grep -q "approveUser" /home/duckey/lgcse-project/frontend/src/api/adminApi.js && echo "✅" || echo "❌")
echo "   ✓ revokeCertificate" $(grep -q "revokeCertificate" /home/duckey/lgcse-project/frontend/src/api/adminApi.js && echo "✅" || echo "❌")

# 3. Check backend endpoints
echo ""
echo "3️⃣ Backend Endpoints:"
echo "   ✓ /admin/pending-users" $(grep -q '@router.get.*admin/pending-users' /home/duckey/lgcse-project/backend/api/dashboard.py && echo "✅" || echo "❌")
echo "   ✓ /admin/users/approve" $(grep -q '@router.post.*admin/users/approve' /home/duckey/lgcse-project/backend/api/dashboard.py && echo "✅" || echo "❌")
echo "   ✓ /admin/certificates/{id}/revoke" $(grep -q '@router.post.*admin/certificates' /home/duckey/lgcse-project/backend/api/dashboard.py && echo "✅" || echo "❌")
echo "   ✓ /admin/logs" $(grep -q '@router.get.*admin/logs' /home/duckey/lgcse-project/backend/api/dashboard.py && echo "✅" || echo "❌")

# 4. Check routers are included
echo ""
echo "4️⃣ Router Inclusion in main.py:"
echo "   ✓ dashboard_router" $(grep -q "app.include_router(dashboard_router)" /home/duckey/lgcse-project/backend/main.py && echo "✅" || echo "❌")
echo "   ✓ admin_approval_router" $(grep -q "app.include_router(admin_approval_router)" /home/duckey/lgcse-project/backend/main.py && echo "✅" || echo "❌")

# 5. Check authentication context
echo ""
echo "5️⃣ Authentication Context:"
echo "   ✓ login method exists" $(grep -q "const login = async" /home/duckey/lgcse-project/frontend/src/contexts/AuthContext.jsx && echo "✅" || echo "❌")
echo "   ✓ register method exists" $(grep -q "const register = async" /home/duckey/lgcse-project/frontend/src/contexts/AuthContext.jsx && echo "✅" || echo "❌")
echo "   ✓ logout method exists" $(grep -q "const logout = " /home/duckey/lgcse-project/frontend/src/contexts/AuthContext.jsx && echo "✅" || echo "❌")

echo ""
echo "✨ Validation Complete!"
