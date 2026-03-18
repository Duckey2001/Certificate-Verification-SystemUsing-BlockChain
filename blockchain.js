const crypto = require('crypto');
const fs = require('fs');

class Block {
    constructor(index, timestamp, data, previousHash = '') {
        this.index = index;
        this.timestamp = timestamp;
        this.data = data;
        this.previousHash = previousHash;
        this.hash = this.calculateHash();
        this.nonce = 0;
    }

    calculateHash() {
        return crypto.createHash('sha256')
            .update(this.index + this.timestamp + JSON.stringify(this.data) + this.previousHash + this.nonce)
            .digest('hex');
    }

    mineBlock(difficulty) {
        while (this.hash.substring(0, difficulty) !== Array(difficulty + 1).join("0")) {
            this.nonce++;
            this.hash = this.calculateHash();
        }
        console.log(`🔗 Block mined: ${this.hash.substring(0, 20)}...`);
    }
}

class Blockchain {
    constructor() {
        // Initialize properties first
        this.difficulty = 2;
        this.pendingTransactions = [];
        this.miningReward = 100;
        
        // Validators (Proof of Authority)
        this.validators = [
            { name: 'LGCSE Certificate Authority', msp: 'LGCSEMSP', publicKey: 'lgcse_pub_key', isIssuer: true },
            { name: 'Ministry of Education', msp: 'EducationMSP', publicKey: 'education_pub_key', isIssuer: false },
            { name: 'Examination Council', msp: 'ExamCouncilMSP', publicKey: 'exam_pub_key', isIssuer: false },
            { name: 'Independent Validators', msp: 'IndependentMSP', publicKey: 'independent_pub_key', isIssuer: false }
        ];
        
        // Now create genesis block with initialized validators
        this.chain = [this.createGenesisBlock()];
        this.loadChain();
    }

    createGenesisBlock() {
        return new Block(0, Date.now(), {
            type: 'GENESIS',
            message: 'LGCSE Diploma Blockchain Network Initialized',
            validators: this.validators.map(v => v.name),
            timestamp: new Date().toISOString()
        }, '0');
    }

    getLatestBlock() {
        return this.chain[this.chain.length - 1];
    }

    addBlock(newBlock) {
        newBlock.previousHash = this.getLatestBlock().hash;
        newBlock.mineBlock(this.difficulty);
        this.chain.push(newBlock);
        this.saveChain();
        return newBlock;
    }

    isChainValid() {
        for (let i = 1; i < this.chain.length; i++) {
            const currentBlock = this.chain[i];
            const previousBlock = this.chain[i - 1];

            if (currentBlock.hash !== currentBlock.calculateHash()) {
                console.log(`❌ Block ${i} hash invalid`);
                return false;
            }

            if (currentBlock.previousHash !== previousBlock.hash) {
                console.log(`❌ Block ${i} previous hash invalid`);
                return false;
            }
        }
        return true;
    }

    // Add diploma transaction
    createDiplomaTransaction(certificateHash, studentId, studentName, examYear, issuer = 'LGCSE') {
        const transaction = {
            type: 'ISSUE_DIPLOMA',
            transactionId: crypto.randomBytes(16).toString('hex'),
            certificateHash: certificateHash,
            studentId: studentId,
            studentName: studentName,
            examYear: examYear,
            issuer: issuer,
            timestamp: new Date().toISOString(),
            validatorsSigned: []
        };
        
        this.pendingTransactions.push(transaction);
        console.log(`📝 Transaction created: ${transaction.transactionId.substring(0, 12)}...`);
        return transaction;
    }

    // Add verification transaction
    createVerificationTransaction(certificateHash, verifier, isValid) {
        const transaction = {
            type: 'VERIFY_DIPLOMA',
            transactionId: crypto.randomBytes(16).toString('hex'),
            certificateHash: certificateHash,
            verifier: verifier,
            isValid: isValid,
            timestamp: new Date().toISOString(),
            validatorsSigned: []
        };
        
        this.pendingTransactions.push(transaction);
        console.log(`🔍 Verification transaction created for ${certificateHash.substring(0, 15)}...`);
        return transaction;
    }

    // Simulate consensus (in real system, each validator would sign digitally)
    async achieveConsensus() {
        console.log('🔄 Achieving consensus among 4 universities...');
        
        // Simulate validator voting
        const votes = this.validators.map(validator => ({
            validator: validator.name,
            approved: Math.random() > 0.2, // 80% chance of approval
            signature: `sig_${crypto.randomBytes(8).toString('hex')}`
        }));
        
        const approvedVotes = votes.filter(v => v.approved);
        console.log(`📊 Consensus result: ${approvedVotes.length}/4 validators approved`);
        
        // Need at least 3 out of 4 approvals (Proof of Authority)
        const consensusAchieved = approvedVotes.length >= 3;
        
        if (consensusAchieved) {
            // Sign transactions with validator signatures
            this.pendingTransactions.forEach(tx => {
                tx.validatorsSigned = approvedVotes.map(v => ({
                    validator: v.validator,
                    signature: v.signature
                }));
                tx.consensusReached = true;
                tx.consensusTimestamp = new Date().toISOString();
            });
            console.log('✅ Consensus achieved!');
        } else {
            console.log('❌ Consensus failed - not enough validator approvals');
        }
        
        return consensusAchieved;
    }

    // Mine pending transactions into a block
    async minePendingTransactions() {
        if (this.pendingTransactions.length === 0) {
            console.log('ℹ️ No pending transactions to mine');
            return null;
        }
        
        console.log(`⛏️ Mining block with ${this.pendingTransactions.length} transactions...`);
        
        // Achieve consensus first
        const consensus = await this.achieveConsensus();
        if (!consensus) {
            console.log('❌ Consensus not reached - transaction rejected');
            // Remove failed transactions
            this.pendingTransactions = [];
            return null;
        }
        
        console.log(`✅ Consensus achieved! Creating block...`);
        
        const block = new Block(
            this.chain.length,
            Date.now(),
            {
                transactions: this.pendingTransactions,
                minedBy: 'LGCSE Network',
                consensus: 'Proof of Authority',
                validatorCount: 4,
                approvedBy: this.pendingTransactions[0]?.validatorsSigned?.map(v => v.validator) || []
            },
            this.getLatestBlock().hash
        );
        
        const minedBlock = this.addBlock(block);
        console.log(`🎉 Block #${minedBlock.index} mined successfully!`);
        
        // Clear pending transactions
        this.pendingTransactions = [];
        
        return minedBlock;
    }

    // Get all transactions for a certificate
    getCertificateHistory(certificateHash) {
        const history = [];
        
        for (const block of this.chain) {
            if (block.data.transactions) {
                for (const tx of block.data.transactions) {
                    if (tx.certificateHash === certificateHash) {
                        history.push({
                            blockIndex: block.index,
                            blockHash: block.hash.substring(0, 20) + '...',
                            transaction: tx
                        });
                    }
                }
            }
        }
        
        return history;
    }

    // Save chain to file (persistence)
    saveChain() {
        try {
            const chainData = JSON.stringify(this.chain, null, 2);
            fs.writeFileSync('blockchain-data.json', chainData);
            console.log(`💾 Blockchain saved to file (${this.chain.length} blocks)`);
        } catch (error) {
            console.error('❌ Error saving blockchain:', error.message);
        }
    }

    // Load chain from file
    loadChain() {
        try {
            if (fs.existsSync('blockchain-data.json')) {
                const chainData = fs.readFileSync('blockchain-data.json', 'utf8');
                const parsedChain = JSON.parse(chainData);
                
                // Recreate Block objects
                this.chain = parsedChain.map(blockData => {
                    const block = new Block(
                        blockData.index,
                        blockData.timestamp,
                        blockData.data,
                        blockData.previousHash
                    );
                    block.hash = blockData.hash;
                    block.nonce = blockData.nonce;
                    return block;
                });
                
                console.log(`📚 Blockchain loaded from file: ${this.chain.length} blocks`);
            } else {
                console.log('💡 No existing blockchain found, starting fresh chain');
            }
        } catch (error) {
            console.log('⚠️ Could not load blockchain, starting fresh:', error.message);
        }
    }

    // Get blockchain info
    getInfo() {
        const totalTransactions = this.chain.reduce((total, block) => {
            return total + (block.data.transactions ? block.data.transactions.length : 0);
        }, 0);
        
        return {
            chainLength: this.chain.length,
            pendingTransactions: this.pendingTransactions.length,
            totalTransactions: totalTransactions,
            isValid: this.isChainValid(),
            validators: this.validators.map(v => v.name),
            latestBlock: {
                index: this.getLatestBlock().index,
                hash: this.getLatestBlock().hash.substring(0, 20) + '...',
                timestamp: new Date(this.getLatestBlock().timestamp).toLocaleString(),
                transactionCount: this.getLatestBlock().data.transactions ? 
                    this.getLatestBlock().data.transactions.length : 0
            }
        };
    }

    // Print blockchain for debugging
    printChain() {
        console.log('\n========== BLOCKCHAIN LEDGER ==========');
        console.log(`Chain length: ${this.chain.length} blocks`);
        console.log(`Chain valid: ${this.isChainValid() ? '✅ YES' : '❌ NO'}`);
        console.log(`Validators: ${this.validators.map(v => v.name).join(', ')}`);
        console.log('----------------------------------------');
        
        this.chain.forEach(block => {
            console.log(`Block #${block.index}`);
            console.log(`Hash: ${block.hash.substring(0, 25)}...`);
            console.log(`Previous: ${block.previousHash.substring(0, 25)}...`);
            console.log(`Transactions: ${block.data.transactions ? block.data.transactions.length : 0}`);
            console.log(`Timestamp: ${new Date(block.timestamp).toLocaleString()}`);
            if (block.data.approvedBy) {
                console.log(`Approved by: ${block.data.approvedBy.length} validators`);
            }
            console.log('---');
        });
        console.log('========================================\n');
    }

    // Get a specific block
    getBlock(index) {
        return this.chain.find(block => block.index === index);
    }

    // Search for a transaction
    findTransaction(transactionId) {
        for (const block of this.chain) {
            if (block.data.transactions) {
                const transaction = block.data.transactions.find(tx => tx.transactionId === transactionId);
                if (transaction) {
                    return {
                        blockIndex: block.index,
                        blockHash: block.hash,
                        transaction: transaction
                    };
                }
            }
        }
        return null;
    }
}

// Create and export singleton instance
const blockchain = new Blockchain();
module.exports = blockchain;
