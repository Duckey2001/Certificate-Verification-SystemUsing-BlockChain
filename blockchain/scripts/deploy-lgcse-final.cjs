const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await deployer.provider.getBalance(deployer.address)).toString());
  console.log("Network:", network.name);

  // Deploy LGCSEToken first (if needed separately)
  console.log("\n--- Deploying LGCSEToken ---");
  const LGCSEToken = await ethers.getContractFactory("LGCSEToken");
  const lgcseToken = await LGCSEToken.deploy();
  await lgcseToken.waitForDeployment();
  const tokenAddress = await lgcseToken.getAddress();
  console.log("✅ LGCSEToken deployed to:", tokenAddress);

  // Deploy CertificateRegistry
  console.log("\n--- Deploying CertificateRegistry ---");
  const CertificateRegistry = await ethers.getContractFactory("CertificateRegistry");
  
  // If CertificateRegistry needs the token address in constructor, uncomment next line
  // const certificateRegistry = await CertificateRegistry.deploy(tokenAddress);
  // If it doesn't need parameters, use this:
  const certificateRegistry = await CertificateRegistry.deploy();
  
  await certificateRegistry.waitForDeployment();
  const registryAddress = await certificateRegistry.getAddress();
  console.log("✅ CertificateRegistry deployed to:", registryAddress);

  // Save addresses to a file for easy reference
  const fs = require('fs');
  const deploymentInfo = {
    network: network.name,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      LGCSEToken: tokenAddress,
      CertificateRegistry: registryAddress
    }
  };
  
  fs.writeFileSync('deployment-localhost.json', JSON.stringify(deploymentInfo, null, 2));
  console.log("\n📄 Deployment info saved to deployment-localhost.json");
  
  console.log("\n🎉 Deployment complete!");
  console.log("\nAdd these to your backend .env file:");
  console.log(`BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545/`);
  console.log(`CERTIFICATE_CONTRACT_ADDRESS=${registryAddress}`);
  console.log(`LGCSE_TOKEN_ADDRESS=${tokenAddress}`);
  console.log(`PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:", error);
    process.exit(1);
  });
