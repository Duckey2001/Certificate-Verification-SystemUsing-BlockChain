// Simple blockchain implementation for LGCSE Certificate System
const crypto = require('crypto');

class Blockchain {
    constructor() {
        this.chain = [this.createGenesisBlock()];
        this.pendingTransactions = [];
        this.validators = ['LGCSE Certificate Authority', 'Ministry of Education', 'Examination Council', 'Independent Validators'];
        this.difficulty = 2;
    }

    createGenesisBlock() {
        return {
            index: 0,
            timestamp: Date.now(),
            data: {
                transactions: [],
                validator: 'Genesis'
            },
            hash: this.calculateHash(0, Date.now(), { transactions: [], validator: 'Genesis' }, '0'),
            previousHash: '0'
        };
    }

    calculateHash(index, timestamp, data, previousHash) {
        return crypto.createHash('sha256')
            .update(index + timestamp + JSON.stringify(data) + previousHash)
            .digest('hex');
    }

    createDiplomaTransaction(certHash, studentId, studentName, examYear, issuer) {
        return {
            id: crypto.randomUUID(),
            type: 'DIPLOMA_ISSUE',
            certHash,
            studentId,
            studentName,
            examYear,
            issuer,
            timestamp: Date.now()
        };
    }

    createVerificationTransaction(certHash, verifier, isValid) {
        return {
            id: crypto.randomUUID(),
            type: 'CERTIFICATE_VERIFY',
            certHash,
            verifier,
            isValid,
            timestamp: Date.now()
        };
    }

    addTransaction(transaction) {
        this.pendingTransactions.push(transaction);
    }

    async minePendingTransactions() {
        const validator = this.validators[Math.floor(Math.random() * this.validators.length)];
        
        const newBlock = {
            index: this.chain.length,
            timestamp: Date.now(),
            data: {
                transactions: [...this.pendingTransactions],
                validator
            },
            previousHash: this.chain[this.chain.length - 1].hash
        };

        // Mine the block (simple proof of work)
        newBlock.hash = this.mineBlock(newBlock);
        
        this.chain.push(newBlock);
        this.pendingTransactions = [];
        
        return newBlock;
    }

    mineBlock(block) {
        let nonce = 0;
        let hash = this.calculateHash(block.index, block.timestamp, block.data, block.previousHash);
        
        while (hash.substring(0, this.difficulty) !== Array(this.difficulty + 1).join('0')) {
            nonce++;
            hash = this.calculateHash(block.index, block.timestamp, block.data, block.previousHash);
        }
        
        return hash;
    }

    getCertificateHistory(certHash) {
        const history = [];
        
        for (const block of this.chain) {
            for (const transaction of block.data.transactions) {
                if (transaction.certHash === certHash) {
                    history.push({
                        ...transaction,
                        blockIndex: block.index,
                        blockHash: block.hash,
                        timestamp: block.timestamp,
                        validator: block.data.validator
                    });
                }
            }
        }
        
        return history;
    }

    isChainValid() {
        for (let i = 1; i < this.chain.length; i++) {
            const currentBlock = this.chain[i];
            const previousBlock = this.chain[i - 1];
            
            // Check hash
            if (currentBlock.hash !== this.calculateHash(
                currentBlock.index,
                currentBlock.timestamp,
                currentBlock.data,
                currentBlock.previousHash
            )) {
                return false;
            }
            
            // Check previous hash link
            if (currentBlock.previousHash !== previousBlock.hash) {
                return false;
            }
        }
        
        return true;
    }

    getInfo() {
        return {
            chainLength: this.chain.length,
            validators: this.validators,
            isValid: this.isChainValid(),
            pendingTransactions: this.pendingTransactions.length
        };
    }

    printChain() {
        console.log('\n🔗 Blockchain State:');
        console.log(`   Length: ${this.chain.length} blocks`);
        console.log(`   Valid: ${this.isChainValid() ? '✅ YES' : '❌ NO'}`);
        console.log(`   Pending: ${this.pendingTransactions.length} transactions`);
        console.log(`   Validators: ${this.validators.join(', ')}`);
    }
}

// Create singleton instance
const blockchain = new Blockchain();

module.exports = blockchain;
