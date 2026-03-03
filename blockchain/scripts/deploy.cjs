const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const Factory = await ethers.getContractFactory("CertificateRegistry");
  const registry = await Factory.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("CertificateRegistry deployed to:", address);

  // Write config and ABI for the backend
  const outDir = path.resolve(__dirname, "../../backend/blockchain");
  fs.mkdirSync(outDir, { recursive: true });

  const registryPath = path.join(outDir, "registry.json");
  fs.writeFileSync(
    registryPath,
    JSON.stringify(
      {
        network: "hardhat",
        rpcUrl: "http://127.0.0.1:8545",
        address,
        deployer: deployer.address,
      },
      null,
      2
    )
  );
  console.log("Wrote backend config:", registryPath);

  // Copy ABI from Hardhat artifacts
  const artifactPath = path.resolve(
    __dirname,
    "../artifacts/contracts/CertificateRegistry.sol/CertificateRegistry.json"
  );
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const abiPath = path.join(outDir, "CertificateRegistry.abi.json");
  fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
  console.log("Wrote ABI:", abiPath);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
