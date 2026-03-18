-- Sample Data for CertiVert System with Sesotho Names
-- This file contains sample data for institutions, certificates, and verification logs
-- Run this script after connecting to your database: \c diploma_verification

-- =============================================
-- 1. INSERT INSTITUTIONS (ISSUERS AND VERIFIERS)
-- =============================================

-- Clear existing data (optional - uncomment if you want to start fresh)
-- DELETE FROM "VerificationLog";
-- DELETE FROM "Certificate";
-- DELETE FROM "Institution";

-- Insert Issuer Institutions (Educational Institutions)
INSERT INTO "Institution" (
    id, code, name, "createdAt", "updatedAt", role
) VALUES 
-- Government Institutions
(
    'inst-001', 'MOET', 
    'Ministry of Education and Training - Lesotho', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-002', 'LGCSE', 
    'Lesotho General Certificate of Secondary Education Council', 
    NOW(), NOW(), 'ISSUER'
),

-- Universities and Colleges
(
    'inst-003', 'NUL', 
    'National University of Lesotho', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-004', 'LIMKO', 
    'Limkokwing University of Creative Technology', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-005', 'BOTHO', 
    'Botho University Lesotho Campus', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-006', 'ECOL', 
    'Lesotho College of Education', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-007', 'LTC', 
    'Lerotholi Technical College', 
    NOW(), NOW(), 'ISSUER'
),

-- Private Schools
(
    'inst-008', 'MACHABENG', 
    'Machabeng College', 
    NOW(), NOW(), 'ISSUER'
),
(
    'inst-009', 'STJOSEPHS', 
    'St. Josephs High School', 
    NOW(), NOW(), 'ISSUER'
),

-- =============================================
-- VERIFIER INSTITUTIONS (Companies/Organizations)
-- =============================================

(
    'inst-010', 'GOV-LESOTHO', 
    'Government of Lesotho - Civil Service Commission', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-011', 'NUL-HR', 
    'National University of Lesotho - Human Resources', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-012', 'LIMKO-HR', 
    'Limkokwing University - HR Department', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-013', 'BOTHO-HR', 
    'Botho University - Recruitment Office', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-014', 'STANBIC', 
    'Stanbic Bank Lesotho', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-015', 'FNBL', 
    'First National Bank Lesotho', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-016', 'BEDCO', 
    'Basotho Enterprises Development Corporation', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-017', 'LNDC', 
    'Lesotho National Development Corporation', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-018', 'METS', 
    'Metsing Financial Services', 
    NOW(), NOW(), 'VERIFIER'
),
(
    'inst-019', 'SECHABA', 
    'Sechaba Consular Services', 
    NOW(), NOW(), 'VERIFIER'
);

-- =============================================
-- 2. INSERT CERTIFICATES
-- =============================================

-- Certificates from NUL (National University of Lesotho)
INSERT INTO "Certificate" (
    id, hash, "issuerCode", "examType", "examSession", "candidateNumber", 
    "certificateNumber", "fullName", "dateOfBirth"
) VALUES 
-- NUL Bachelor Degrees
(
    'cert-nul-001', 'hash_nul_bsc_2023_001', 'NUL', 
    'BSC Computer Science', '2023-2024', 'NUL/CS/2023/001',
    'NUL-2023-BSC-001', 'Thabo Mokhele', '1998-05-15'
),
(
    'cert-nul-002', 'hash_nul_bsc_2023_002', 'NUL', 
    'BSC Computer Science', '2023-2024', 'NUL/CS/2023/002',
    'NUL-2023-BSC-002', 'Mampho Tau', '1999-08-22'
),
(
    'cert-nul-003', 'hash_nul_bba_2023_001', 'NUL', 
    'BBA Business Administration', '2023-2024', 'NUL/BA/2023/001',
    'NUL-2023-BBA-001', 'Lerato Ntsoane', '1997-12-10'
),
(
    'cert-nul-004', 'hash_nul_bsc_2023_003', 'NUL', 
    'BSC Mathematics', '2023-2024', 'NUL/MATH/2023/001',
    'NUL-2023-BSC-003', 'Mpho Ramaema', '1998-03-28'
),
(
    'cert-nul-005', 'hash_nul_llb_2023_001', 'NUL', 
    'LLB Law', '2023-2024', 'NUL/LAW/2023/001',
    'NUL-2023-LLB-001', 'Teboho Mokoena', '1996-11-15'
),

-- Certificates from LIMKO (Limkokwing University)
(
    'cert-limko-001', 'hash_limko_bdes_2023_001', 'LIMKO', 
    'BDES Graphic Design', '2023-2024', 'LIMKO/DES/2023/001',
    'LIMKO-2023-BDES-001', 'Mapalesa Molapo', '1999-07-20'
),
(
    'cert-limko-002', 'hash_limko_bba_2023_001', 'LIMKO', 
    'BBA International Business', '2023-2024', 'LIMKO/IB/2023/001',
    'LIMKO-2023-BBA-001', 'Rethabile Seeiso', '1998-09-12'
),
(
    'cert-limko-003', 'hash_limko_bit_2023_001', 'LIMKO', 
    'BIT Information Technology', '2023-2024', 'LIMKO/IT/2023/001',
    'LIMKO-2023-BIT-001', 'Tšepo Raleting', '1997-04-05'
),
(
    'cert-limko-004', 'hash_limko_barch_2023_001', 'LIMKO', 
    'BArch Architecture', '2023-2024', 'LIMKO/ARCH/2023/001',
    'LIMKO-2023-BARCH-001', 'Lineo Makhetha', '1999-01-18'
),

-- Certificates from BOTHO University
(
    'cert-botho-001', 'hash_botho_bcom_2023_001', 'BOTHO', 
    'BCom Accounting', '2023-2024', 'BOTHO/ACC/2023/001',
    'BOTHO-2023-BCOM-001', 'Kopano Tšehlana', '1998-06-30'
),
(
    'cert-botho-002', 'hash_botho_bba_2023_001', 'BOTHO', 
    'BBA Marketing', '2023-2024', 'BOTHO/MKT/2023/001',
    'BOTHO-2023-BBA-001', 'Palesa Motsoahae', '1999-11-25'
),
(
    'cert-botho-003', 'hash_botho_bsc_2023_001', 'BOTHO', 
    'BSC Computer Science', '2023-2024', 'BOTHO/CS/2023/001',
    'BOTHO-2023-BSC-001', 'Ts'epo Lekhanya', '1997-08-14'
),

-- Certificates from ECOL (Lesotho College of Education)
(
    'cert-ecol-001', 'hash_ecol_bed_2023_001', 'ECOL', 
    'BED Primary Education', '2023-2024', 'ECOL/PRIM/2023/001',
    'ECOL-2023-BED-001', 'Mampho Monyane', '1998-02-28'
),
(
    'cert-ecol-002', 'hash_ecol_bed_2023_002', 'ECOL', 
    'BED Secondary Education', '2023-2024', 'ECOL/SEC/2023/001',
    'ECOL-2023-BED-002', 'Thabo Lekhanya', '1999-05-10'
),

-- LGCSE Certificates (High School)
(
    'cert-lgcse-001', 'hash_lgcse_2023_001', 'LGCSE', 
    'LGCSE', '2023', 'LGCSE/2023/0001',
    'LGCSE-2023-0001', 'Nthabiseng Mokhele', '2005-12-15'
),
(
    'cert-lgcse-002', 'hash_lgcse_2023_002', 'LGCSE', 
    'LGCSE', '2023', 'LGCSE/2023/0002',
    'LGCSE-2023-0002', 'Kabelo Ramaema', '2005-08-22'
),
(
    'cert-lgcse-003', 'hash_lgcse_2023_003', 'LGCSE', 
    'LGCSE', '2023', 'LGCSE/2023/0003',
    'LGCSE-2023-0003', 'Maseru Ntsoane', '2005-03-10'
);

-- =============================================
-- 3. INSERT VERIFICATION LOGS
-- =============================================

-- Verification requests and logs
INSERT INTO "VerificationLog" (
    id, hash, "verifierCode", "createdAt", "certificateId", 
    message, verified, "issuerCode"
) VALUES 
-- Recent verifications by Government of Lesotho
(
    'ver-log-001', 'ver_hash_001', 'GOV-LESOTHO', 
    NOW() - INTERVAL '2 hours', 'cert-nul-001',
    'Certificate verified successfully - Thabo Mokhele BSC Computer Science from NUL', 
    TRUE, 'NUL'
),
(
    'ver-log-002', 'ver_hash_002', 'GOV-LESOTHO', 
    NOW() - INTERVAL '5 hours', 'cert-limko-001',
    'Certificate verified successfully - Mapalesa Molapo BDES Graphic Design from LIMKO', 
    TRUE, 'LIMKO'
),

-- Verifications by NUL HR
(
    'ver-log-003', 'ver_hash_003', 'NUL-HR', 
    NOW() - INTERVAL '1 day', 'cert-botho-001',
    'Certificate verified successfully - Kopano Tšehlana BCom Accounting from BOTHO', 
    TRUE, 'BOTHO'
),
(
    'ver-log-004', 'ver_hash_004', 'NUL-HR', 
    NOW() - INTERVAL '2 days', 'cert-ecol-001',
    'Certificate verified successfully - Mampho Monyane BED Primary Education from ECOL', 
    TRUE, 'ECOL'
),

-- Verifications by Banks
(
    'ver-log-005', 'ver_hash_005', 'STANBIC', 
    NOW() - INTERVAL '3 days', 'cert-nul-003',
    'Certificate verified successfully - Mpho Ramaema BSC Mathematics from NUL', 
    TRUE, 'NUL'
),
(
    'ver-log-006', 'ver_hash_006', 'FNBL', 
    NOW() - INTERVAL '4 days', 'cert-botho-001',
    'Certificate verified successfully - Kopano Tšehlana BCom Accounting from BOTHO', 
    TRUE, 'BOTHO'
),

-- Pending verifications
(
    'ver-log-007', 'ver_hash_007', 'LIMKO-HR', 
    NOW() - INTERVAL '6 hours', 'cert-nul-002',
    'Verification pending - Mampho Tau BSC Computer Science from NUL', 
    FALSE, 'NUL'
),
(
    'ver-log-008', 'ver_hash_008', 'BOTHO-HR', 
    NOW() - INTERVAL '12 hours', 'cert-limko-002',
    'Verification pending - Rethabile Seeiso BBA International Business from LIMKO', 
    FALSE, 'LIMKO'
),

-- Failed/Flagged verifications
(
    'ver-log-009', 'ver_hash_009', 'BEDCO', 
    NOW() - INTERVAL '1 day', 'cert-lgcse-002',
    'Certificate flagged for manual review - Kabelo Ramaema LGCSE', 
    FALSE, 'LGCSE'
),

-- More successful verifications
(
    'ver-log-010', 'ver_hash_010', 'LNDC', 
    NOW() - INTERVAL '5 days', 'cert-nul-005',
    'Certificate verified successfully - Teboho Mokoena LLB Law from NUL', 
    TRUE, 'NUL'
),
(
    'ver-log-011', 'ver_hash_011', 'METS', 
    NOW() - INTERVAL '1 week', 'cert-botho-002',
    'Certificate verified successfully - Palesa Motsoahae BBA Marketing from BOTHO', 
    TRUE, 'BOTHO'
),
(
    'ver-log-012', 'ver_hash_012', 'SECHABA', 
    NOW() - INTERVAL '2 weeks', 'cert-limko-003',
    'Certificate verified successfully - Tšepo Raleting BIT Information Technology from LIMKO', 
    TRUE, 'LIMKO'
);

-- =============================================
-- 4. VERIFICATION SUMMARY
-- =============================================

-- Display summary of inserted data
SELECT 'INSTITUTIONS SUMMARY' as summary_type;
SELECT role, COUNT(*) as count FROM "Institution" GROUP BY role;

SELECT 'CERTIFICATES SUMMARY' as summary_type;
SELECT "issuerCode", COUNT(*) as certificates_issued FROM "Certificate" GROUP BY "issuerCode" ORDER BY certificates_issued DESC;

SELECT 'VERIFICATION LOG SUMMARY' as summary_type;
SELECT verified, COUNT(*) as verification_count FROM "VerificationLog" GROUP BY verified;

-- Display sample records for verification
SELECT 'SAMPLE INSTITUTIONS' as summary_type LIMIT 5;
SELECT id, code, name, role FROM "Institution" LIMIT 5;

SELECT 'SAMPLE CERTIFICATES' as summary_type LIMIT 5;
SELECT id, "fullName", "issuerCode", "examType" FROM "Certificate" LIMIT 5;

SELECT 'SAMPLE VERIFICATION LOGS' as summary_type LIMIT 5;
SELECT id, "verifierCode", "certificateId", verified, "createdAt" FROM "VerificationLog" ORDER BY "createdAt" DESC LIMIT 5;

-- =============================================
-- 5. LOGIN CREDENTIALS FOR TESTING
-- =============================================

-- Note: Since your schema uses institutions rather than individual users,
-- you'll need to map these to your authentication system
-- Here are suggested login credentials based on institution codes:

/*
INSTITUTION LOGIN CREDENTIALS:

ISSUER INSTITUTIONS:
- Code: NUL, Password: NUL123!
- Code: LIMKO, Password: LIMKO123!
- Code: BOTHO, Password: BOTHO123!
- Code: ECOL, Password: ECOL123!
- Code: LGCSE, Password: LGCSE123!
- Code: MOET, Password: MOET123!
- Code: LTC, Password: LTC123!
- Code: MACHABENG, Password: MACH123!
- Code: STJOSEPHS, Password: STJO123!

VERIFIER INSTITUTIONS:
- Code: GOV-LESOTHO, Password: GOV123!
- Code: NUL-HR, Password: NULHR123!
- Code: LIMKO-HR, Password: LIMKOHR123!
- Code: BOTHO-HR, Password: BOTHOHR123!
- Code: STANBIC, Password: STAN123!
- Code: FNBL, Password: FNBL123!
- Code: BEDCO, Password: BED123!
- Code: LNDC, Password: LND123!
- Code: METS, Password: METS123!
- Code: SECHABA, Password: SEC123!

SESOTHO NAMES USED:
- Thabo Mokhele (Male)
- Mampho Tau (Female)
- Lerato Ntsoane (Female)
- Mpho Ramaema (Male)
- Teboho Mokoena (Male)
- Mapalesa Molapo (Female)
- Rethabile Seeiso (Female)
- Tšepo Raleting (Male)
- Lineo Makhetha (Female)
- Kopano Tšehlana (Male)
- Palesa Motsoahae (Female)
- Ts'epo Lekhanya (Male)
- Mampho Monyane (Female)
- Kabelo Ramaema (Male)
- Nthabiseng Mokhele (Female)
- Maseru Ntsoane (Male)
*/
