const Web3 = require('web3');

async function test() {
  try {
    const web3 = new Web3('http://localhost:8545');
    
    // Check connection
    const version = await web3.eth.getNodeInfo();
    console.log('✅ Connected to blockchain:', version);
    
    // Get accounts
    const accounts = await web3.eth.getAccounts();
    console.log('✅ Accounts:', accounts.length, 'available');
    console.log('   First account:', accounts[0]);
    
    // Check contract (if deployed)
    const contractAddress = '0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab';
    const code = await web3.eth.getCode(contractAddress);
    console.log('✅ Contract at', contractAddress);
    console.log('   Code length:', code.length, '(0 means not deployed)');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

test();
