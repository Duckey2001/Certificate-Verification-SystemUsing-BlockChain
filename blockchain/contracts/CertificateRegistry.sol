// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CertificateRegistry {
    address public owner;
    mapping(bytes32 => bool) private issued;

    event CertificateIssued(bytes32 indexed hash, address indexed issuer, uint256 timestamp, string metadataUri);
    event CertificateTamperReported(bytes32 indexed expectedHash, bytes32 indexed computedHash, address indexed reporter, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function issue(bytes32 hash, string calldata metadataUri) external onlyOwner {
        require(!issued[hash], "already issued");
        issued[hash] = true;
        emit CertificateIssued(hash, msg.sender, block.timestamp, metadataUri);
    }

    function exists(bytes32 hash) external view returns (bool) {
        return issued[hash];
    }

    function reportTamper(bytes32 expectedHash, bytes32 computedHash) external {
        emit CertificateTamperReported(expectedHash, computedHash, msg.sender, block.timestamp);
    }
}

