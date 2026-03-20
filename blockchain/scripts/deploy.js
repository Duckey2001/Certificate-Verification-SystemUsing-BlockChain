import { ethers } from "hardhat";
import fs from "fs";

async function main() {
  console.log("🚀 Deploying LGCSE Certificate Contracts...");
  
  const deploymentInfo = {
    network: "localhost",
    timestamp: new Date().toISOString(),
    contracts: {}
  };
  
  // Deploy CertificateRegistry
  console.log("📜 Deploying CertificateRegistry...");
  const CertificateRegistry = await ethers.getContractFactory("CertificateRegistry");
  const certificateRegistry = await CertificateRegistry.deploy();
  await certificateRegistry.waitForDeployment();
  const certRegistryAddress = await certificateRegistry.getAddress();
  console.log(`✅ CertificateRegistry deployed to: ${certRegistryAddress}`);
  deploymentInfo.contracts.CertificateRegistry = certRegistryAddress;
  
  // Deploy LGCSEToken
  console.log("🪙 Deploying LGCSEToken...");
  const LGCSEToken = await ethers.getContractFactory("LGCSEToken");
  const lgcseToken = await LGCSEToken.deploy();
  await lgcseToken.waitForDeployment();
  const tokenAddress = await lgcseToken.getAddress();
  console.log(`✅ LGCSEToken deployed to: ${tokenAddress}`);
  deploymentInfo.contracts.LGCSEToken = tokenAddress;
  
  // Deploy Lock (if needed for testing)
  console.log("🔒 Deploying Lock...");
  const Lock = await ethers.getContractFactory("Lock");
  const unlockTime = Math.floor(Date.now() / 1000) + 60 * 60 * 24; // 1 day from now
  const lock = await Lock.deploy(unlockTime);
  await lock.waitForDeployment();
  const lockAddress = await lock.getAddress();
  console.log(`✅ Lock contract deployed to: ${lockAddress}`);
  deploymentInfo.contracts.Lock = lockAddress;
  
  // Save deployment info
  fs.writeFileSync(
    "../deployment-info.json", 
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("📝 Deployment info saved to deployment-info.json");
  
  console.log("\n🎉 All contracts deployed successfully!");
  console.log("📊 Contract Summary:");
  console.log(`   CertificateRegistry: ${certRegistryAddress}`);
  console.log(`   LGCSEToken: ${tokenAddress}`);
  console.log(`   Lock: ${lockAddress}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
