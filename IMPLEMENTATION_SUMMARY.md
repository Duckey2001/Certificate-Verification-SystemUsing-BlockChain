# CertiVert LGCSE Implementation Summary

## Overview
This implementation transforms CertiVert into an admin-controlled LGCSE certificate verification system with Google OAuth authentication and strict certificate validation.

## Key Features Implemented

### 1. Admin as Central Authority
- **Admin Email**: `letsapobokang.certivert@gmail.com` (only admin with password login)
- **Admin Dashboard**: Full control over network access and user approvals
- **User Management**: Admin can approve/reject institution users
- **Audit Trail**: Complete audit log of all admin actions

### 2. Email-Based Institution Detection
- **Pattern Recognition**: `letsapobokang.limko@gmail.com` → Limkokwing University
- **Supported Institutions**:
  - LIMKO → Limkokwing University
  - NUL → National University of Lesotho
  - BOTHO → Botho University
  - LGCSE → LGCSE Examination Council
  - ECOL → Ecol University
- **Role Assignment**: New users get `pending_issuer` role until admin approval

### 3. Google OAuth Enforcement
- **Admin Only**: Can still use username/password login
- **Institution Users**: Must use Google OAuth with institution email
- **Access Control**: Only recognized institution emails allowed
- **Error Handling**: Clear error messages for unauthorized access attempts

### 4. LGCSE Certificate OCR Validation
- **Keyword Detection**: Validates LGCSE-specific terminology
- **Pattern Matching**: Certificate numbers, student numbers, grading levels
- **Data Extraction**: Student name, institution, grades, issue dates
- **Hash Generation**: SHA-256 hash from extracted certificate data

### 5. Certificate Rejection System
- **Non-LGCSE Detection**: Rejects certificates without LGCSE characteristics
- **Minimum Requirements**: At least 5 LGCSE keywords required
- **Specific Validation**: Certificate numbers, grading levels, institution types
- **Clear Error Messages**: Detailed rejection reasons

## API Endpoints

### Authentication
- `POST /api/auth/login` - Admin login only
- `POST /api/auth/google/verify-token` - Google OAuth for institutions

### Admin Management
- `GET /api/admin/pending-users` - View pending approvals
- `POST /api/admin/approve-user` - Approve/reject users
- `GET /api/admin/institution-stats` - Institution statistics
- `GET /api/admin/audit-log` - Admin activity log
- `POST /api/admin/revoke-user-access` - Revoke user access

### Certificate Processing
- `POST /api/certificates/upload` - Upload LGCSE certificates
- **Validation**: OCR processing with LGCSE verification
- **Blockchain**: Hash storage on blockchain
- **Audit**: Complete tracking of certificate uploads

## User Roles & Permissions

### Admin
- Email: `letsapobokang.certivert@gmail.com`
- Password: `mpho10//`
- Permissions: Full system control, user approvals, certificate management

### Pending Issuer
- New institution users awaiting approval
- Limited access until admin approval
- Can view dashboard but cannot upload certificates

### Issuer (Approved)
- Approved institution representatives
- Can upload and manage LGCSE certificates
- Institution-specific permissions

## Certificate Validation Rules

### Required LGCSE Elements
- Minimum 5 LGCSE keywords
- Valid certificate number format (2 letters + 7+ digits)
- Valid student number format
- LGCSE grading levels (LEVEL 1-4, GRADE A-G)
- Institution name containing "HIGH SCHOOL" or similar

### Rejection Criteria
- Non-LGCSE certificates
- Missing required patterns
- Invalid certificate/student numbers
- No LGCSE grading system

## Security Features

### Authentication
- Google OAuth for institutions
- Admin password protection
- JWT token-based sessions
- Role-based access control

### Data Protection
- Certificate hash generation
- Blockchain storage
- Audit trail for all actions
- Secure file handling

## Error Handling

### Authentication Errors
- "Access denied. Only admin emails and registered institution emails are allowed."
- "Google OAuth not configured. Please contact administrator."
- "Unable to determine institution from email. Please use your institution email."

### Certificate Errors
- "Document does not appear to be an LGCSE certificate."
- "No valid LGCSE certificate number found."
- "No LGCSE grading levels found."

## Configuration

### Environment Variables
```
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
```

### Database Schema
- Users table with role-based permissions
- Certificates table with blockchain references
- Audit events table for complete tracking

## Testing Workflow

1. **Admin Login**: Use credentials at `/login`
2. **Institution Login**: Use Google OAuth with institution email
3. **User Approval**: Admin approves pending users
4. **Certificate Upload**: Approved users upload LGCSE certificates
5. **Validation**: OCR processing validates LGCSE authenticity
6. **Blockchain**: Certificate hashes stored on blockchain

## Frontend Integration

### Login Flow
- Admin: Traditional login form
- Institutions: Google OAuth button only
- Error messages for unauthorized access

### Dashboard Features
- Admin: User management, statistics, audit log
- Institutions: Certificate upload, management
- Role-based UI components

## Deployment Notes

### Dependencies
- Python: FastAPI, SQLAlchemy, OCR libraries
- Frontend: React, Google OAuth integration
- Database: PostgreSQL with audit tables
- OCR: Tesseract, PDF processing

### Security Considerations
- Google OAuth configuration required
- Admin credentials protection
- Certificate file validation
- Blockchain integration setup

## Future Enhancements

### Potential Improvements
- Additional institution patterns
- Enhanced OCR accuracy
- Mobile certificate verification
- Advanced analytics dashboard

### Scalability
- Multi-admin support
- Institutional hierarchies
- Batch certificate processing
- API rate limiting

This implementation provides a robust, secure, and admin-controlled LGCSE certificate verification system with proper authentication, validation, and audit capabilities.
