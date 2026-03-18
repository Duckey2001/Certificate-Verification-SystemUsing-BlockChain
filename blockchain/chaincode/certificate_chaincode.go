/*
Certificate Verification Chaincode for LGCSE Institutions
Designed for Hyperledger Fabric deployment
*/

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing certificates
type SmartContract struct {
	contractapi.Contract
}

// Certificate represents a certificate record
type Certificate struct {
	CertificateHash   string    `json:"certificateHash"`
	StudentID         string    `json:"studentId"`
	StudentName       string    `json:"studentName"`
	StudentSurname    string    `json:"studentSurname"`
	ExaminationYear   int       `json:"examinationYear"`
	Subjects          []Subject `json:"subjects"`
	Credits           int       `json:"credits"`
	IssueDate         string    `json:"issueDate"`
	Issuer            string    `json:"issuer"`
	InstitutionCode   string    `json:"institutionCode"`
	Status            string    `json:"status"`
	CreatedAt         time.Time `json:"createdAt"`
	UpdatedAt         time.Time `json:"updatedAt"`
	VerificationCount int       `json:"verificationCount"`
	LastVerified      time.Time `json:"lastVerified,omitempty"`
}

// Subject represents a subject in the certificate
type Subject struct {
	Name   string `json:"name"`
	Grade  string `json:"grade"`
	Symbol string `json:"symbol"`
}

// VerificationRequest represents a verification request
type VerificationRequest struct {
	RequestID       string    `json:"requestId"`
	CertificateHash string    `json:"certificateHash"`
	VerifierID      string    `json:"verifierId"`
	VerifierName    string    `json:"verifierName"`
	InstitutionCode string    `json:"institutionCode"`
	VerificationMethod string  `json:"verificationMethod"` // hash, file, qr_code
	Result          string    `json:"result"`              // valid, invalid, pending
	IPAddress       string    `json:"ipAddress"`
	UserAgent       string    `json:"userAgent"`
	Timestamp       time.Time `json:"timestamp"`
	TransactionID   string    `json:"transactionId"`
}

// InstitutionNode represents an institution node configuration
type InstitutionNode struct {
	NodeID          string            `json:"nodeId"`
	InstitutionCode string            `json:"institutionCode"`
	InstitutionName string            `json:"institutionName"`
	NodeType        string            `json:"nodeType"`        // issuer, verifier
	MSPID           string            `json:"mspId"`
	PeerID          string            `json:"peerId"`
	ChannelName     string            `json:"channelName"`
	Status          string            `json:"status"`          // active, inactive, maintenance
	PublicKey       string            `json:"publicKey"`
	NodeConfig      map[string]string `json:"nodeConfig"`
	CreatedAt       time.Time         `json:"createdAt"`
	UpdatedAt       time.Time         `json:"updatedAt"`
}

// InitLedger initializes the ledger with default data
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	log.Println("Initializing LGCSE Certificate Verification Ledger")

	// Create default institution nodes
	institutions := []InstitutionNode{
		{
			NodeID:          "ECOL_NODE_001",
			InstitutionCode: "ECOL",
			InstitutionName: "Ecol University",
			NodeType:        "issuer",
			MSPID:           "EcolMSP",
			PeerID:          "peer0.ecol.example.com",
			ChannelName:     "lgcse-channel",
			Status:          "active",
			PublicKey:       "ecol_public_key_placeholder",
			NodeConfig:      map[string]string{"region": "lesotho", "type": "university"},
			CreatedAt:       time.Now(),
			UpdatedAt:       time.Now(),
		},
		{
			NodeID:          "LIMKOWING_NODE_001",
			InstitutionCode: "LIMKOWING",
			InstitutionName: "Limkokwing University",
			NodeType:        "verifier",
			MSPID:           "LimkokwingMSP",
			PeerID:          "peer0.limkokwing.example.com",
			ChannelName:     "lgcse-channel",
			Status:          "active",
			PublicKey:       "limkokwing_public_key_placeholder",
			NodeConfig:      map[string]string{"region": "lesotho", "type": "university"},
			CreatedAt:       time.Now(),
			UpdatedAt:       time.Now(),
		},
		{
			NodeID:          "BOTHO_NODE_001",
			InstitutionCode: "BOTHO",
			InstitutionName: "Botho University",
			NodeType:        "verifier",
			MSPID:           "BothoMSP",
			PeerID:          "peer0.botho.example.com",
			ChannelName:     "lgcse-channel",
			Status:          "active",
			PublicKey:       "botho_public_key_placeholder",
			NodeConfig:      map[string]string{"region": "lesotho", "type": "university"},
			CreatedAt:       time.Now(),
			UpdatedAt:       time.Now(),
		},
		{
			NodeID:          "NUL_NODE_001",
			InstitutionCode: "NUL",
			InstitutionName: "National University of Lesotho",
			NodeType:        "verifier",
			MSPID:           "NULMSP",
			PeerID:          "peer0.nul.example.com",
			ChannelName:     "lgcse-channel",
			Status:          "active",
			PublicKey:       "nul_public_key_placeholder",
			NodeConfig:      map[string]string{"region": "lesotho", "type": "university"},
			CreatedAt:       time.Now(),
			UpdatedAt:       time.Now(),
		},
	}

	for _, institution := range institutions {
		institutionJSON, err := json.Marshal(institution)
		if err != nil {
			return err
		}

		err = ctx.GetStub().PutState(fmt.Sprintf("INSTITUTION_%s", institution.InstitutionCode), institutionJSON)
		if err != nil {
			return fmt.Errorf("failed to put institution %s to world state: %v", institution.InstitutionCode, err)
		}
	}

	log.Println("Ledger initialized successfully with institution nodes")
	return nil
}

// IssueCertificate issues a new certificate to the ledger
func (s *SmartContract) IssueCertificate(ctx contractapi.TransactionContextInterface, certificateHash string, studentID string, studentName string, studentSurname string, examinationYear int, subjectsJSON string, credits int, issueDate string, issuer string, institutionCode string) error {
	// Check if certificate already exists
	exists, err := s.CertificateExists(ctx, certificateHash)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the certificate %s already exists", certificateHash)
	}

	// Parse subjects
	var subjects []Subject
	err = json.Unmarshal([]byte(subjectsJSON), &subjects)
	if err != nil {
		return fmt.Errorf("failed to parse subjects: %v", err)
	}

	// Verify institution exists and is authorized to issue
	institution, err := s.GetInstitution(ctx, institutionCode)
	if err != nil {
		return fmt.Errorf("institution not found: %v", err)
	}

	if institution.NodeType != "issuer" {
		return fmt.Errorf("institution %s is not authorized to issue certificates", institutionCode)
	}

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
	}

	certificateJSON, err := json.Marshal(certificate)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(certificateHash, certificateJSON)
}

// VerifyCertificate verifies a certificate and records the verification
func (s *SmartContract) VerifyCertificate(ctx contractapi.TransactionContextInterface, certificateHash string, verifierID string, verifierName string, institutionCode string, verificationMethod string, ipAddress string, userAgent string) (*VerificationRequest, error) {
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

	if institution.NodeType != "verifier" && institution.NodeType != "issuer" {
		return nil, fmt.Errorf("institution %s is not authorized to verify certificates", institutionCode)
	}

	// Create verification request
	requestID := fmt.Sprintf("VERIFY_%s_%d", certificateHash, time.Now().Unix())
	transactionID := ctx.GetStub().GetTxID()

	verification := VerificationRequest{
		RequestID:         requestID,
		CertificateHash:   certificateHash,
		VerifierID:        verifierID,
		VerifierName:      verifierName,
		InstitutionCode:   institutionCode,
		VerificationMethod: verificationMethod,
		Result:            "valid",
		IPAddress:         ipAddress,
		UserAgent:         userAgent,
		Timestamp:         time.Now(),
		TransactionID:     transactionID,
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

	return &verification, nil
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

		// Only include certificate records (skip institutions and verifications)
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

// UpdateInstitution updates institution node configuration
func (s *SmartContract) UpdateInstitution(ctx contractapi.TransactionContextInterface, nodeID string, institutionCode string, institutionName string, nodeType string, mspId string, peerId string, channelName string, status string, publicKey string, nodeConfigJSON string) error {
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

	return ctx.GetStub().PutState(institutionKey, updatedInstitutionJSON)
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

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		log.Panicf("Error creating certificate chaincode: %v", err)
	}

	if err := chaincode.Start(); err != nil {
		log.Panicf("Error starting certificate chaincode: %v", err)
	}
}
