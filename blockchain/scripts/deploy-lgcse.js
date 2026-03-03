const hre = require("hardhat");

async function main() {
  console.log("Deploying LGCSE Token contract...");
  
  // Get the contract factory
  const LGCSEToken = await hre.ethers.getContractFactory("LGCSEToken");
  
  // Deploy the contract
  const lgcseToken = await LGCSEToken.deploy();
  
  // Wait for deployment
  await lgcseToken.waitForDeployment();
  
  // Get the deployed address
  const address = await lgcseToken.getAddress();
  
  console.log(`✅ LGCSEToken deployed to: ${address}`);
  
  // Save deployment info
  const fs = require("fs");
  const deploymentInfo = {
    contractAddress: address,
    contractName: "LGCSEToken",
    network: hre.network.name,
    timestamp: new Date().toISOString(),
  };
  
  fs.writeFileSync("lgcse-deployment.json", JSON.stringify(deploymentInfo, null, 2));
  console.log("📝 Deployment info saved to lgcse-deployment.json");
  
  // Get the owner address
  const [owner] = await hre.ethers.getSigners();
  console.log(`👤 Owner address: ${owner.address}`);
  
  // Get initial balance
  const balance = await lgcseToken.balanceOf(owner.address);
  console.log(`💰 Owner initial balance: ${hre.ethers.formatEther(balance)} LGCSE`);
}

main().catch((error) => {
  console.error("❌ Deployment failed:", error);
  process.exit(1);
});
