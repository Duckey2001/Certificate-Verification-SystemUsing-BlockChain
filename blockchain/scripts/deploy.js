import { ethers } from "hardhat";
import fs from "fs";

async function main() {
  console.log("Deploying Lock contract...");
  
  // Get the contract factory for Lock
  const Lock = await ethers.getContractFactory("Lock");
  
  // Lock.sol typically takes an unlockTime parameter
  // If your Lock.sol doesn't need parameters, remove the unlockTime line
  const unlockTime = Math.floor(Date.now() / 1000) + 60 * 60 * 24; // 1 day from now
  
  console.log(`Deploying with unlock time: ${new Date(unlockTime * 1000).toLocaleString()}`);
  
  // Deploy the contract with constructor arguments
  // If your Lock.sol doesn't need parameters, use: const lock = await Lock.deploy();
  const lock = await Lock.deploy(unlockTime);
  
  // Wait for deployment
  await lock.waitForDeployment();
  
  // Get the deployed address
  const address = await lock.getAddress();
  console.log(`✅ Lock contract deployed to: ${address}`);
  
  // Save address to a file for backend/frontend to use
  const deploymentInfo = {
    contractAddress: address,
    contractName: "Lock",
    network: "localhost",
    timestamp: new Date().toISOString(),
    unlockTime: unlockTime
  };
  
  fs.writeFileSync(
    "deployment-info.json", 
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("📝 Deployment info saved to deployment-info.json");
  console.log("Contract address:", address);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
