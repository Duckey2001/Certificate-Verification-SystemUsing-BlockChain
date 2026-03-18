/*
Certificate Verification Chaincode for LGCSE Certificate Verification System
Designed for Hyperledger Fabric v2.4+

This chaincode provides:
- Certificate issuance and verification
- Institution node management
- Verification history tracking
- Private data collections for sensitive information
- Role-based access control
- Comprehensive audit logging
*/

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing certificates
type SmartContract struct {
	contractapi.Contract
}

// Certificate represents a certificate record
type Certificate struct {
	CertificateHash    string    `json:"certificateHash"`
	StudentID          string    `json:"studentId"`
	StudentName        string    `json:"studentName"`
	StudentSurname     string    `json:"studentSurname"`
	ExaminationYear    int       `json:"examinationYear"`
	Subjects           []Subject `json:"subjects"`
	Credits            int       `json:"credits"`
	IssueDate          string    `json:"issueDate"`
	Issuer             string    `json:"issuer"`
	InstitutionCode    string    `json:"institutionCode"`
	Status             string    `json:"status"`             // active, revoked, suspended
	CreatedAt          time.Time `json:"createdAt"`
	UpdatedAt          time.Time `json:"updatedAt"`
	VerificationCount  int       `json:"verificationCount"`
	LastVerified       time.Time `json:"lastVerified,omitempty"`
	RevocationReason   string    `json:"revocationReason,omitempty"`
	RevokedAt          time.Time `json:"revokedAt,omitempty"`
	PrivateData        string    `json:"privateData,omitempty"` // Encrypted sensitive data
}

// Subject represents a subject in the certificate
type Subject struct {
	Name   string `json:"name"`
	Grade  string `json:"grade"`
	Symbol string `json:"symbol"`
	Marks  int    `json:"marks,omitempty"`
}

// VerificationRequest represents a verification request
type VerificationRequest struct {
	RequestID         string    `json:"requestId"`
	CertificateHash   string    `json:"certificateHash"`
	VerifierID        string    `json:"verifierId"`
	VerifierName      string    `json:"verifierName"`
	InstitutionCode   string    `json:"institutionCode"`
	VerificationMethod string    `json:"verificationMethod"` // hash, file, qr_code, digital
	Result            string    `json:"result"`              // valid, invalid, pending, failed
	IPAddress         string    `json:"ipAddress"`
	UserAgent         string    `json:"userAgent"`
	Timestamp         time.Time `json:"timestamp"`
	TransactionID     string    `json:"transactionId"`
	VerificationData  string    `json:"verificationData,omitempty"` // Additional verification data
	ConfidenceScore   float64   `json:"confidenceScore,omitempty"`
	ProcessingTime    int64     `json:"processingTime,omitempty"` // in milliseconds
}

// InstitutionNode represents an institution node configuration
type InstitutionNode struct {
	NodeID          string            `json:"nodeId"`
	InstitutionCode string            `json:"institutionCode"`
	InstitutionName string            `json:"institutionName"`
	NodeType        string            `json:"nodeType"`        // issuer, verifier, both
	MSPID           string            `json:"mspId"`
	PeerID          string            `json:"peerId"`
	ChannelName     string            `json:"channelName"`
	Status          string            `json:"status"`          // active, inactive, maintenance
	PublicKey       string            `json:"publicKey"`
	NodeConfig      map[string]string `json:"nodeConfig"`
	CreatedAt       time.Time         `json:"createdAt"`
	UpdatedAt       time.Time         `json:"updatedAt"`
	LastActivity     time.Time         `json:"lastActivity"`
	CertificatesIssued int            `json:"certificatesIssued"`
	VerificationsPerformed int        `json:"verificationsPerformed"`
}

// AuditLog represents an audit log entry
type AuditLog struct {
	LogID          string            `json:"logId"`
	Timestamp      time.Time         `json:"timestamp"`
	EventType      string            `json:"eventType"`      // issue, verify, revoke, update
	ActorID        string            `json:"actorId"`
	ActorName      string            `json:"actorName"`
	InstitutionCode string            `json:"institutionCode"`
	CertificateHash string            `json:"certificateHash,omitempty"`
	Action         string            `json:"action"`
	Result         string            `json:"result"`         // success, failure, error
	Details        map[string]string `json:"details"`
	IPAddress      string            `json:"ipAddress"`
	UserAgent      string            `json:"userAgent"`
	TransactionID  string            `json:"transactionId"`
}

// Private data collections configuration
const (
	// Collection for sensitive certificate data
	CertificatePrivateCollection = "certificatePrivateData"
	
	// Collection for verification details
	VerificationPrivateCollection = "verificationPrivateData"
	
	// Collection for institution private data
	InstitutionPrivateCollection = "institutionPrivateData"
)

// InitLedger initializes the ledger with default data
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	log.Println("Initializing LGCSE Certificate Verification Ledger")

	// Create default institution nodes
	institutions := []InstitutionNode{
		{
			NodeID:                "ECOL_NODE_001",
			InstitutionCode:       "ECOL",
			InstitutionName:       "Ecol LGCSE",
			NodeType:              "issuer",
			MSPID:                 "EcolOrgMSP",
			PeerID:                "peer0.ecol.example.com",
			ChannelName:           "lgcse-channel",
			Status:                "active",
			PublicKey:             "ecol_public_key_placeholder",
			NodeConfig:            map[string]string{"region": "lesotho", "type": "LGCSE", "role": "issuer"},
			CreatedAt:             time.Now(),
			UpdatedAt:             time.Now(),
			LastActivity:          time.Now(),
			CertificatesIssued:    0,
			VerificationsPerformed: 0,
		},
		{
			NodeID:                "LIMKOWING_NODE_001",
			InstitutionCode:       "LIMKOWING",
			InstitutionName:       "Limkokwing University",
			NodeType:              "verifier",
			MSPID:                 "LimkokwingOrgMSP",
			PeerID:                "peer0.limkokwing.example.com",
			ChannelName:           "lgcse-channel",
			Status:                "active",
			PublicKey:             "limkokwing_public_key_placeholder",
			NodeConfig:            map[string]string{"region": "lesotho", "type": "university", "role": "verifier"},
			CreatedAt:             time.Now(),
			UpdatedAt:             time.Now(),
			LastActivity:          time.Now(),
			CertificatesIssued:    0,
			VerificationsPerformed: 0,
		},
		{
			NodeID:                "BOTHO_NODE_001",
			InstitutionCode:       "BOTHO",
			InstitutionName:       "Botho University",
			NodeType:              "verifier",
			MSPID:                 "BothoOrgMSP",
			PeerID:                "peer0.botho.example.com",
			ChannelName:           "lgcse-channel",
			Status:                "active",
			PublicKey:             "botho_public_key_placeholder",
			NodeConfig:            map[string]string{"region": "lesotho", "type": "university", "role": "verifier"},
			CreatedAt:             time.Now(),
			UpdatedAt:             time.Now(),
			LastActivity:          time.Now(),
			CertificatesIssued:    0,
			VerificationsPerformed: 0,
		},
		{
			NodeID:                "NUL_NODE_001",
			InstitutionCode:       "NUL",
			InstitutionName:       "National University of Lesotho",
			NodeType:              "verifier",
			MSPID:                 "NulOrgMSP",
			PeerID:                "peer0.nul.example.com",
			ChannelName:           "lgcse-channel",
			Status:                "active",
			PublicKey:             "nul_public_key_placeholder",
			NodeConfig:            map[string]string{"region": "lesotho", "type": "university", "role": "verifier"},
			CreatedAt:             time.Now(),
			UpdatedAt:             time.Now(),
			LastActivity:          time.Now(),
			CertificatesIssued:    0,
			VerificationsPerformed: 0,
		},
	}

	for _, institution := range institutions {
		institutionJSON, err := json.Marshal(institution)
		if err != nil {
			return fmt.Errorf("failed to marshal institution %s: %v", institution.InstitutionCode, err)
		}

		err = ctx.GetStub().PutState(fmt.Sprintf("INSTITUTION_%s", institution.InstitutionCode), institutionJSON)
		if err != nil {
			return fmt.Errorf("failed to put institution %s to world state: %v", institution.InstitutionCode, err)
		}

		// Store private data in collection
		err = ctx.GetStub().PutPrivateData(InstitutionPrivateCollection, fmt.Sprintf("INSTITUTION_PRIVATE_%s", institution.InstitutionCode), institutionJSON)
		if err != nil {
			return fmt.Errorf("failed to put private institution data %s: %v", institution.InstitutionCode, err)
		}
	}

	// Create audit log for initialization
	initLog := AuditLog{
		LogID:          fmt.Sprintf("AUDIT_%d", time.Now().UnixNano()),
		Timestamp:      time.Now(),
		EventType:      "init",
		ActorID:        "system",
		ActorName:      "System Initialization",
		InstitutionCode: "SYSTEM",
		Action:         "ledger_initialization",
		Result:         "success",
		Details:        map[string]string{"institutions_count": strconv.Itoa(len(institutions))},
		TransactionID:  ctx.GetStub().GetTxID(),
	}

	initLogJSON, err := json.Marshal(initLog)
	if err != nil {
		return fmt.Errorf("failed to marshal init audit log: %v", err)
	}

	err = ctx.GetStub().PutState(initLog.LogID, initLogJSON)
	if err != nil {
		return fmt.Errorf("failed to put init audit log: %v", err)
	}

	log.Println("Ledger initialized successfully with institution nodes")
	return nil
}

// IssueCertificate issues a new certificate to the ledger
func (s *SmartContract) IssueCertificate(ctx contractapi.TransactionContextInterface, certificateHash string, studentID string, studentName string, studentSurname string, examinationYear int, subjectsJSON string, credits int, issueDate string, issuer string, institutionCode string, privateData string) error {
	// Get client ID and MSP
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	mspID, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		return fmt.Errorf("failed to get MSP ID: %v", err)
	}

	// Check if certificate already exists
	exists, err := s.CertificateExists(ctx, certificateHash)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the certificate %s already exists", certificateHash)
	}

	// Verify institution exists and is authorized to issue
	institution, err := s.GetInstitution(ctx, institutionCode)
	if err != nil {
		return fmt.Errorf("institution not found: %v", err)
	}

	if institution.NodeType != "issuer" && institution.NodeType != "both" {
		return fmt.Errorf("institution %s is not authorized to issue certificates", institutionCode)
	}

	// Parse subjects
	var subjects []Subject
	err = json.Unmarshal([]byte(subjectsJSON), &subjects)
	if err != nil {
		return fmt.Errorf("failed to parse subjects: %v", err)
	}

	// Validate certificate data
	if err := s.validateCertificateData(studentID, studentName, studentSurname, examinationYear, subjects, credits, issueDate); err != nil {
		return err
	}

	// Create certificate
	certificate := Certificate{
		CertificateHash:   certificateHash,
		StudentID:         studentID,
		StudentName:       studentName,
		StudentSurname:    studentSurname,
		ExaminationYear:   examinationYear,
		Subjects:          subjects,
		Credits:           credits,
		IssueDate:         issueDate,
		Issuer:            issuer,
		InstitutionCode:   institutionCode,
		Status:            "active",
		CreatedAt:         time.Now(),
		UpdatedAt:         time.Now(),
		VerificationCount: 0,
		PrivateData:       privateData,
	}

	certificateJSON, err := json.Marshal(certificate)
	if err != nil {
		return err
	}

	// Store certificate in public state
	err = ctx.GetStub().PutState(certificateHash, certificateJSON)
	if err != nil {
		return err
	}

	// Store private data in collection
	if privateData != "" {
		privateCert := Certificate{
			CertificateHash: certificateHash,
			PrivateData:     privateData,
		}
		privateCertJSON, err := json.Marshal(privateCert)
		if err != nil {
			return err
		}
		err = ctx.GetStub().PutPrivateData(CertificatePrivateCollection, fmt.Sprintf("CERT_PRIVATE_%s", certificateHash), privateCertJSON)
		if err != nil {
			return fmt.Errorf("failed to store private certificate data: %v", err)
		}
	}

	// Update institution statistics
	institution.CertificatesIssued++
	institution.LastActivity = time.Now()
	institution.UpdatedAt = time.Now()
	
	institutionJSON, err := json.Marshal(institution)
	if err != nil {
		return err
	}
	
	err = ctx.GetStub().PutState(fmt.Sprintf("INSTITUTION_%s", institutionCode), institutionJSON)
	if err != nil {
		return err
	}

	// Create audit log
	auditLog := AuditLog{
		LogID:          fmt.Sprintf("AUDIT_%d", time.Now().UnixNano()),
		Timestamp:      time.Now(),
		EventType:      "issue",
		ActorID:        clientID,
		ActorName:      issuer,
		InstitutionCode: institutionCode,
		CertificateHash: certificateHash,
		Action:         "certificate_issued",
		Result:         "success",
		Details: map[string]string{
			"studentID":   studentID,
			"studentName": studentName + " " + studentSurname,
			"year":        strconv.Itoa(examinationYear),
			"subjects":    strconv.Itoa(len(subjects)),
		},
		TransactionID: ctx.GetStub().GetTxID(),
	}

	auditLogJSON, err := json.Marshal(auditLog)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(auditLog.LogID, auditLogJSON)
	if err != nil {
		return err
	}

	log.Printf("Certificate %s issued successfully by %s", certificateHash, institutionCode)
	return nil
}

// VerifyCertificate verifies a certificate and records the verification
func (s *SmartContract) VerifyCertificate(ctx contractapi.TransactionContextInterface, certificateHash string, verifierID string, verifierName string, institutionCode string, verificationMethod string, ipAddress string, userAgent string, verificationData string) (*VerificationRequest, error) {
	// Get client ID and MSP
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return nil, fmt.Errorf("failed to get client identity: %v", err)
	}

	// Check if certificate exists
	certificate, err := s.GetCertificate(ctx, certificateHash)
	if err != nil {
		return nil, fmt.Errorf("certificate not found: %v", err)
	}

	// Verify institution exists and is authorized to verify
	institution, err := s.GetInstitution(ctx, institutionCode)
	if err != nil {
		return nil, fmt.Errorf("institution not found: %v", err)
	}

	if institution.NodeType != "verifier" && institution.NodeType != "both" {
		return nil, fmt.Errorf("institution %s is not authorized to verify certificates", institutionCode)
	}

	// Check certificate status
	if certificate.Status != "active" {
		return nil, fmt.Errorf("certificate %s is not active (status: %s)", certificateHash, certificate.Status)
	}

	// Perform verification logic
	startTime := time.Now()
	result, confidenceScore := s.performVerification(certificate, verificationMethod, verificationData)
	processingTime := time.Since(startTime).Milliseconds()

	// Create verification request
	requestID := fmt.Sprintf("VERIFY_%s_%d", certificateHash, time.Now().Unix())
	transactionID := ctx.GetStub().GetTxID()

	verification := VerificationRequest{
		RequestID:          requestID,
		CertificateHash:    certificateHash,
		VerifierID:          verifierID,
		VerifierName:        verifierName,
		InstitutionCode:     institutionCode,
		VerificationMethod:  verificationMethod,
		Result:              result,
		IPAddress:           ipAddress,
		UserAgent:           userAgent,
		Timestamp:           time.Now(),
		TransactionID:       transactionID,
		VerificationData:    verificationData,
		ConfidenceScore:     confidenceScore,
		ProcessingTime:      processingTime,
	}

	verificationJSON, err := json.Marshal(verification)
	if err != nil {
		return nil, err
	}

	// Store verification record
	err = ctx.GetStub().PutState(requestID, verificationJSON)
	if err != nil {
		return nil, err
	}

	// Store private verification data
	if verificationData != "" {
		privateVerification := VerificationRequest{
			RequestID:         requestID,
			VerificationData:  verificationData,
			ConfidenceScore:   confidenceScore,
			ProcessingTime:    processingTime,
		}
		privateVerificationJSON, err := json.Marshal(privateVerification)
		if err != nil {
			return nil, err
		}
		err = ctx.GetStub().PutPrivateData(VerificationPrivateCollection, fmt.Sprintf("VERIFY_PRIVATE_%s", requestID), privateVerificationJSON)
		if err != nil {
			return nil, fmt.Errorf("failed to store private verification data: %v", err)
		}
	}

	// Update certificate verification count and last verified timestamp
	certificate.VerificationCount++
	certificate.LastVerified = time.Now()
	certificate.UpdatedAt = time.Now()

	updatedCertificateJSON, err := json.Marshal(certificate)
	if err != nil {
		return nil, err
	}

	err = ctx.GetStub().PutState(certificateHash, updatedCertificateJSON)
	if err != nil {
		return nil, err
	}

	// Update institution statistics
	institution.VerificationsPerformed++
	institution.LastActivity = time.Now()
	institution.UpdatedAt = time.Now()
	
	institutionJSON, err := json.Marshal(institution)
	if err != nil {
		return nil, err
	}
	
	err = ctx.GetStub().PutState(fmt.Sprintf("INSTITUTION_%s", institutionCode), institutionJSON)
	if err != nil {
		return nil, err
	}

	// Create audit log
	auditLog := AuditLog{
		LogID:          fmt.Sprintf("AUDIT_%d", time.Now().UnixNano()),
		Timestamp:      time.Now(),
		EventType:      "verify",
		ActorID:        clientID,
		ActorName:      verifierName,
		InstitutionCode: institutionCode,
		CertificateHash: certificateHash,
		Action:         "certificate_verified",
		Result:         result,
		Details: map[string]string{
			"verificationMethod": verificationMethod,
			"confidenceScore":    fmt.Sprintf("%.2f", confidenceScore),
			"processingTime":     strconv.FormatInt(processingTime, 10),
		},
		IPAddress:     ipAddress,
		UserAgent:     userAgent,
		TransactionID: transactionID,
	}

	auditLogJSON, err := json.Marshal(auditLog)
	if err != nil {
		return nil, err
	}

	err = ctx.GetStub().PutState(auditLog.LogID, auditLogJSON)
	if err != nil {
		return nil, err
	}

	log.Printf("Certificate %s verified by %s with result: %s", certificateHash, institutionCode, result)
	return &verification, nil
}

// RevokeCertificate revokes a certificate
func (s *SmartContract) RevokeCertificate(ctx contractapi.TransactionContextInterface, certificateHash string, reason string, revokedBy string, institutionCode string) error {
	// Get client ID and MSP
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	// Check if certificate exists
	certificate, err := s.GetCertificate(ctx, certificateHash)
	if err != nil {
		return fmt.Errorf("certificate not found: %v", err)
	}

	// Verify institution exists and is authorized to revoke
	institution, err := s.GetInstitution(ctx, institutionCode)
	if err != nil {
		return fmt.Errorf("institution not found: %v", err)
	}

	// Only issuing institution can revoke
	if certificate.InstitutionCode != institutionCode {
		return fmt.Errorf("only the issuing institution can revoke this certificate")
	}

	// Check if certificate is already revoked
	if certificate.Status == "revoked" {
		return fmt.Errorf("certificate %s is already revoked", certificateHash)
	}

	// Revoke certificate
	certificate.Status = "revoked"
	certificate.RevocationReason = reason
	certificate.RevokedAt = time.Now()
	certificate.UpdatedAt = time.Now()

	updatedCertificateJSON, err := json.Marshal(certificate)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(certificateHash, updatedCertificateJSON)
	if err != nil {
		return err
	}

	// Create audit log
	auditLog := AuditLog{
		LogID:          fmt.Sprintf("AUDIT_%d", time.Now().UnixNano()),
		Timestamp:      time.Now(),
		EventType:      "revoke",
		ActorID:        clientID,
		ActorName:      revokedBy,
		InstitutionCode: institutionCode,
		CertificateHash: certificateHash,
		Action:         "certificate_revoked",
		Result:         "success",
		Details: map[string]string{
			"reason": reason,
		},
		TransactionID: ctx.GetStub().GetTxID(),
	}

	auditLogJSON, err := json.Marshal(auditLog)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(auditLog.LogID, auditLogJSON)
	if err != nil {
		return err
	}

	log.Printf("Certificate %s revoked by %s for reason: %s", certificateHash, institutionCode, reason)
	return nil
}

// GetCertificate returns the certificate stored in the ledger with given hash
func (s *SmartContract) GetCertificate(ctx contractapi.TransactionContextInterface, certificateHash string) (*Certificate, error) {
	certificateJSON, err := ctx.GetStub().GetState(certificateHash)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if certificateJSON == nil {
		return nil, fmt.Errorf("the certificate %s does not exist", certificateHash)
	}

	var certificate Certificate
	err = json.Unmarshal(certificateJSON, &certificate)
	if err != nil {
		return nil, err
	}

	return &certificate, nil
}

// GetCertificatePrivateData returns private data for a certificate
func (s *SmartContract) GetCertificatePrivateData(ctx contractapi.TransactionContextInterface, certificateHash string) (*Certificate, error) {
	privateDataJSON, err := ctx.GetStub().GetPrivateData(CertificatePrivateCollection, fmt.Sprintf("CERT_PRIVATE_%s", certificateHash))
	if err != nil {
		return nil, fmt.Errorf("failed to read private data: %v", err)
	}
	if privateDataJSON == nil {
		return nil, fmt.Errorf("no private data found for certificate %s", certificateHash)
	}

	var privateCert Certificate
	err = json.Unmarshal(privateDataJSON, &privateCert)
	if err != nil {
		return nil, err
	}

	return &privateCert, nil
}

// CertificateExists returns true when certificate with given hash exists in world state
func (s *SmartContract) CertificateExists(ctx contractapi.TransactionContextInterface, certificateHash string) (bool, error) {
	certificateJSON, err := ctx.GetStub().GetState(certificateHash)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return certificateJSON != nil, nil
}

// GetAllCertificates returns all certificates found in world state
func (s *SmartContract) GetAllCertificates(ctx contractapi.TransactionContextInterface) ([]*Certificate, error) {
	// range query with empty string for startKey and endKey does an open-ended query of all certificates in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var certificates []*Certificate
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var certificate Certificate
		err = json.Unmarshal(queryResponse.Value, &certificate)
		if err != nil {
			return nil, err
		}

		// Only include certificate records (skip institutions, verifications, and audit logs)
		if certificate.CertificateHash != "" {
			certificates = append(certificates, &certificate)
		}
	}

	return certificates, nil
}

// GetCertificatesByInstitution returns all certificates issued by a specific institution
func (s *SmartContract) GetCertificatesByInstitution(ctx contractapi.TransactionContextInterface, institutionCode string) ([]*Certificate, error) {
	queryString := fmt.Sprintf(`{"selector":{"institutionCode":"%s"}}`, institutionCode)
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var certificates []*Certificate
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var certificate Certificate
		err = json.Unmarshal(queryResponse.Value, &certificate)
		if err != nil {
			return nil, err
		}

		certificates = append(certificates, &certificate)
	}

	return certificates, nil
}

// GetCertificatesByStudent returns all certificates for a specific student
func (s *SmartContract) GetCertificatesByStudent(ctx contractapi.TransactionContextInterface, studentID string) ([]*Certificate, error) {
	queryString := fmt.Sprintf(`{"selector":{"studentId":"%s"}}`, studentID)
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var certificates []*Certificate
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var certificate Certificate
		err = json.Unmarshal(queryResponse.Value, &certificate)
		if err != nil {
			return nil, err
		}

		certificates = append(certificates, &certificate)
	}

	return certificates, nil
}

// GetInstitution returns institution configuration
func (s *SmartContract) GetInstitution(ctx contractapi.TransactionContextInterface, institutionCode string) (*InstitutionNode, error) {
	institutionJSON, err := ctx.GetStub().GetState(fmt.Sprintf("INSTITUTION_%s", institutionCode))
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if institutionJSON == nil {
		return nil, fmt.Errorf("the institution %s does not exist", institutionCode)
	}

	var institution InstitutionNode
	err = json.Unmarshal(institutionJSON, &institution)
	if err != nil {
		return nil, err
	}

	return &institution, nil
}

// GetAllInstitutions returns all institutions
func (s *SmartContract) GetAllInstitutions(ctx contractapi.TransactionContextInterface) ([]*InstitutionNode, error) {
	queryString := `{"selector":{"nodeType":{"$in":["issuer","verifier","both"]}}}`
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var institutions []*InstitutionNode
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var institution InstitutionNode
		err = json.Unmarshal(queryResponse.Value, &institution)
		if err != nil {
			return nil, err
		}

		institutions = append(institutions, &institution)
	}

	return institutions, nil
}

// UpdateInstitution updates institution node configuration
func (s *SmartContract) UpdateInstitution(ctx contractapi.TransactionContextInterface, nodeID string, institutionCode string, institutionName string, nodeType string, mspId string, peerId string, channelName string, status string, publicKey string, nodeConfigJSON string) error {
	// Get client ID and MSP
	clientID, err := ctx.GetClientIdentity().GetID()
	if err != nil {
		return fmt.Errorf("failed to get client identity: %v", err)
	}

	institutionKey := fmt.Sprintf("INSTITUTION_%s", institutionCode)
	
	institutionJSON, err := ctx.GetStub().GetState(institutionKey)
	if err != nil {
		return fmt.Errorf("failed to read from world state: %v", err)
	}
	if institutionJSON == nil {
		return fmt.Errorf("the institution %s does not exist", institutionCode)
	}

	var institution InstitutionNode
	err = json.Unmarshal(institutionJSON, &institution)
	if err != nil {
		return err
	}

	// Update fields
	institution.NodeID = nodeID
	institution.InstitutionName = institutionName
	institution.NodeType = nodeType
	institution.MSPID = mspId
	institution.PeerID = peerId
	institution.ChannelName = channelName
	institution.Status = status
	institution.PublicKey = publicKey
	institution.UpdatedAt = time.Now()
	institution.LastActivity = time.Now()

	if nodeConfigJSON != "" {
		var nodeConfig map[string]string
		err = json.Unmarshal([]byte(nodeConfigJSON), &nodeConfig)
		if err != nil {
			return fmt.Errorf("failed to parse node config: %v", err)
		}
		institution.NodeConfig = nodeConfig
	}

	updatedInstitutionJSON, err := json.Marshal(institution)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(institutionKey, updatedInstitutionJSON)
	if err != nil {
		return err
	}

	// Update private data
	err = ctx.GetStub().PutPrivateData(InstitutionPrivateCollection, fmt.Sprintf("INSTITUTION_PRIVATE_%s", institutionCode), updatedInstitutionJSON)
	if err != nil {
		return fmt.Errorf("failed to update private institution data: %v", err)
	}

	// Create audit log
	auditLog := AuditLog{
		LogID:          fmt.Sprintf("AUDIT_%d", time.Now().UnixNano()),
		Timestamp:      time.Now(),
		EventType:      "update",
		ActorID:        clientID,
		ActorName:      "System Admin",
		InstitutionCode: institutionCode,
		Action:         "institution_updated",
		Result:         "success",
		Details: map[string]string{
			"nodeType": nodeType,
			"status":   status,
		},
		TransactionID: ctx.GetStub().GetTxID(),
	}

	auditLogJSON, err := json.Marshal(auditLog)
	if err != nil {
		return err
	}

	err = ctx.GetStub().PutState(auditLog.LogID, auditLogJSON)
	if err != nil {
		return err
	}

	return nil
}

// GetVerificationHistory returns verification history for a certificate
func (s *SmartContract) GetVerificationHistory(ctx contractapi.TransactionContextInterface, certificateHash string) ([]*VerificationRequest, error) {
	queryString := fmt.Sprintf(`{"selector":{"certificateHash":"%s"}}`, certificateHash)
	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var verifications []*VerificationRequest
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var verification VerificationRequest
		err = json.Unmarshal(queryResponse.Value, &verification)
		if err != nil {
			return nil, err
		}

		verifications = append(verifications, &verification)
	}

	return verifications, nil
}

// GetVerificationPrivateData returns private verification data
func (s *SmartContract) GetVerificationPrivateData(ctx contractapi.TransactionContextInterface, requestID string) (*VerificationRequest, error) {
	privateDataJSON, err := ctx.GetStub().GetPrivateData(VerificationPrivateCollection, fmt.Sprintf("VERIFY_PRIVATE_%s", requestID))
	if err != nil {
		return nil, fmt.Errorf("failed to read private verification data: %v", err)
	}
	if privateDataJSON == nil {
		return nil, fmt.Errorf("no private verification data found for request %s", requestID)
	}

	var privateVerification VerificationRequest
	err = json.Unmarshal(privateDataJSON, &privateVerification)
	if err != nil {
		return nil, err
	}

	return &privateVerification, nil
}

// GetAuditLogs returns audit logs with optional filtering
func (s *SmartContract) GetAuditLogs(ctx contractapi.TransactionContextInterface, eventType string, institutionCode string, certificateHash string, limit int) ([]*AuditLog, error) {
	// Build query based on filters
	var queryString string
	if eventType != "" && institutionCode != "" && certificateHash != "" {
		queryString = fmt.Sprintf(`{"selector":{"eventType":"%s","institutionCode":"%s","certificateHash":"%s"}}`, eventType, institutionCode, certificateHash)
	} else if eventType != "" && institutionCode != "" {
		queryString = fmt.Sprintf(`{"selector":{"eventType":"%s","institutionCode":"%s"}}`, eventType, institutionCode)
	} else if eventType != "" {
		queryString = fmt.Sprintf(`{"selector":{"eventType":"%s"}}`, eventType)
	} else if institutionCode != "" {
		queryString = fmt.Sprintf(`{"selector":{"institutionCode":"%s"}}`, institutionCode)
	} else {
		queryString = `{"selector":{"eventType":{"$exists":true}}}`
	}

	resultsIterator, err := ctx.GetStub().GetQueryResult(queryString)
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var auditLogs []*AuditLog
	count := 0
	for resultsIterator.HasNext() && (limit <= 0 || count < limit) {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var auditLog AuditLog
		err = json.Unmarshal(queryResponse.Value, &auditLog)
		if err != nil {
			return nil, err
		}

		auditLogs = append(auditLogs, &auditLog)
		count++
	}

	return auditLogs, nil
}

// GetNetworkStatistics returns network-wide statistics
func (s *SmartContract) GetNetworkStatistics(ctx contractapi.TransactionContextInterface) (map[string]interface{}, error) {
	// Get total certificates
	certificates, err := s.GetAllCertificates(ctx)
	if err != nil {
		return nil, err
	}

	// Get all institutions
	institutions, err := s.GetAllInstitutions(ctx)
	if err != nil {
		return nil, err
	}

	// Get all audit logs
	auditLogs, err := s.GetAuditLogs(ctx, "", "", "", 0)
	if err != nil {
		return nil, err
	}

	// Calculate statistics
	stats := map[string]interface{}{
		"totalCertificates":      len(certificates),
		"totalInstitutions":      len(institutions),
		"totalAuditLogs":         len(auditLogs),
		"activeCertificates":     0,
		"revokedCertificates":    0,
		"totalVerifications":     0,
		"institutionStats":       make([]map[string]interface{}, 0),
	}

	// Certificate status breakdown
	for _, cert := range certificates {
		if cert.Status == "active" {
			stats["activeCertificates"] = stats["activeCertificates"].(int) + 1
		} else if cert.Status == "revoked" {
			stats["revokedCertificates"] = stats["revokedCertificates"].(int) + 1
		}
		stats["totalVerifications"] = stats["totalVerifications"].(int) + cert.VerificationCount
	}

	// Institution statistics
	for _, inst := range institutions {
		instStats := map[string]interface{}{
			"institutionCode":          inst.InstitutionCode,
			"institutionName":          inst.InstitutionName,
			"nodeType":                 inst.NodeType,
			"status":                   inst.Status,
			"certificatesIssued":       inst.CertificatesIssued,
			"verificationsPerformed":   inst.VerificationsPerformed,
			"lastActivity":             inst.LastActivity,
		}
		stats["institutionStats"] = append(stats["institutionStats"].([]map[string]interface{}), instStats)
	}

	return stats, nil
}

// Helper functions

// validateCertificateData validates certificate data
func (s *SmartContract) validateCertificateData(studentID string, studentName string, studentSurname string, examinationYear int, subjects []Subject, credits int, issueDate string) error {
	// Validate required fields
	if studentID == "" || studentName == "" || studentSurname == "" {
		return fmt.Errorf("student ID, name, and surname are required")
	}

	if examinationYear < 2000 || examinationYear > time.Now().Year() {
		return fmt.Errorf("invalid examination year: %d", examinationYear)
	}

	if len(subjects) == 0 {
		return fmt.Errorf("at least one subject is required")
	}

	if credits < 0 {
		return fmt.Errorf("credits cannot be negative")
	}

	if issueDate == "" {
		return fmt.Errorf("issue date is required")
	}

	// Validate subjects
	for _, subject := range subjects {
		if subject.Name == "" || subject.Grade == "" {
			return fmt.Errorf("subject name and grade are required")
		}
	}

	return nil
}

// performVerification performs the actual verification logic
func (s *SmartContract) performVerification(certificate *Certificate, verificationMethod string, verificationData string) (string, float64) {
	// Simple verification logic - in production, this would be more sophisticated
	confidenceScore := 0.95 // Default confidence score

	switch verificationMethod {
	case "hash":
		// Hash-based verification
		confidenceScore = 0.98
	case "file":
		// File-based verification
		confidenceScore = 0.92
	case "qr_code":
		// QR code verification
		confidenceScore = 0.95
	case "digital":
		// Digital signature verification
		confidenceScore = 0.99
	default:
		confidenceScore = 0.85
	}

	// Check certificate status
	if certificate.Status != "active" {
		return "invalid", 0.0
	}

	// Check if certificate is too old (simple validation)
	if certificate.ExaminationYear < 2000 {
		return "invalid", 0.0
	}

	return "valid", confidenceScore
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating certificate chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting certificate chaincode: %v", err)
	}
}
