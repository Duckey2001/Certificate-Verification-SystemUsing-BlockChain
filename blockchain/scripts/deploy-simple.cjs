const hre = require("hardhat");

async function main() {
  console.log("Starting deployment...");
  console.log("Network:", hre.network.name);
  
  // Get the contract factory
  const Lock = await hre.ethers.getContractFactory("Lock");
  console.log("✅ Contract factory loaded");
  
  // Set unlock time to 1 day from now
  const unlockTime = Math.floor(Date.now() / 1000) + 86400;
  console.log(`🔓 Unlock time set to: ${new Date(unlockTime * 1000).toLocaleString()}`);
  
  // Deploy
  console.log("📤 Deploying contract...");
  const lock = await Lock.deploy(unlockTime);
  await lock.waitForDeployment();
  
  const address = await lock.getAddress();
  console.log(`✅ Contract deployed to: ${address}`);
  
  // Save to file
  const fs = require("fs");
  const deploymentInfo = {
    contractAddress: address,
    contractName: "Lock",
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    unlockTime: unlockTime,
    unlockTimeDate: new Date(unlockTime * 1000).toLocaleString()
  };
  
  fs.writeFileSync("deployment-info.json", JSON.stringify(deploymentInfo, null, 2));
  console.log("📝 Deployment info saved to deployment-info.json");
  
  // Show balance if any was sent
  const balance = await hre.ethers.provider.getBalance(address);
  console.log(`💰 Contract balance: ${hre.ethers.formatEther(balance)} ETH`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
