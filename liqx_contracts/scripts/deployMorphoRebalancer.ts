import { ethers } from "hardhat";

async function main() {
  console.log("Deploying MorphoRebalancer contract...");

  // Get the deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);

  // Get account balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH");

  // Deploy the contract
  const MorphoRebalancer = await ethers.getContractFactory("MorphoRebalancer");
  const rebalancer = await MorphoRebalancer.deploy();

  await rebalancer.waitForDeployment();

  const address = await rebalancer.getAddress();
  console.log("MorphoRebalancer deployed to:", address);

  // Verify USDC address is correct for Base
  const usdcAddress = await rebalancer.USDC();
  console.log("USDC address configured:", usdcAddress);

  if (usdcAddress !== "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913") {
    console.warn("⚠️  WARNING: USDC address doesn't match Base mainnet!");
  } else {
    console.log("✓ USDC address verified for Base mainnet");
  }

  console.log("\n✅ Deployment complete!");
  console.log("\nNext steps:");
  console.log("1. Verify contract on Basescan:");
  console.log(`   npx hardhat verify --network base ${address}`);
  console.log("2. Update frontend with contract address");
  console.log("3. Test EIP-7702 authorization flow");

  // Save deployment info
  const deploymentInfo = {
    network: "base",
    contractName: "MorphoRebalancer",
    address: address,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    usdcAddress: usdcAddress,
  };

  console.log("\nDeployment Info:");
  console.log(JSON.stringify(deploymentInfo, null, 2));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
