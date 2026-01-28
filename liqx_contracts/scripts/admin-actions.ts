import hre from "hardhat";

async function main() {
  // Connect to the network
  const { viem } = await hre.network.connect();

  // Get the deployer wallet (Admin)
  const [deployer] = await viem.getWalletClients();
  const publicClient = await viem.getPublicClient();
  
  console.log("Acting as Admin:", deployer.account.address);

  // ---------------------------------------------------------
  // ⚠️ CONFIGURATION
  // ---------------------------------------------------------
  // Replace with your deployed contract address or set via env var
  // Example: "0x..."
  const VAULT_ADDRESS = process.env.VAULT_ADDRESS as `0x${string}`;
  
  // Replace with your AI Agent's wallet address or set via env var
  const AGENT_ADDRESS = process.env.AGENT_ADDRESS as `0x${string}`;

  if (!VAULT_ADDRESS) {
    console.error("❌ Error: VAULT_ADDRESS environment variable is not set.");
    console.log("Usage: VAULT_ADDRESS=0x... AGENT_ADDRESS=0x... npx hardhat run scripts/admin-actions.ts --network <network>");
    return;
  }

  if (!AGENT_ADDRESS) {
    console.error("❌ Error: AGENT_ADDRESS environment variable is not set.");
    return;
  }

  // Attach to Contract
  console.log(`Attaching to LiquidityGuardVault at ${VAULT_ADDRESS}...`);
  const vault = await viem.getContractAt("LiquidityGuardVault", VAULT_ADDRESS);

  // 1. Grant Agent Role
  console.log(`\n1. Checking AGENT_ROLE for ${AGENT_ADDRESS}...`);
  
  // Calculate AGENT_ROLE hash: keccak256("AGENT_ROLE")
  // In Viem/Solidity, we can rely on the public constant if available, or compute it.
  // The contract has 'public constant AGENT_ROLE'.
  const agentRoleHash = await vault.read.AGENT_ROLE();
  
  const hasRole = await vault.read.hasRole([agentRoleHash, AGENT_ADDRESS]);
  
  if (!hasRole) {
    console.log(`Granting AGENT_ROLE to ${AGENT_ADDRESS}...`);
    try {
      const hash = await vault.write.grantAgentRole([AGENT_ADDRESS]);
      console.log(`Tx sent: ${hash}`);
      await publicClient.waitForTransactionReceipt({ hash });
      console.log("✅ Agent Role Granted");
    } catch (error) {
      console.error("❌ Failed to grant role:", error);
    }
  } else {
    console.log("✅ Agent already has the role.");
  }

  // 2. Disable Circuit Breaker (Unpause)
  console.log(`\n2. Checking Circuit Breaker Status...`);
  try {
    const isPaused = await vault.read.circuitBreakerActive();
    console.log(`Current Circuit Breaker Status: ${isPaused ? "Active (Paused)" : "Inactive (Unpaused)"}`);
    
    if (isPaused) {
        console.log("Disabling circuit breaker (Unpausing system)...");
        const hash = await vault.write.toggleCircuitBreaker();
        console.log(`Tx sent: ${hash}`);
        await publicClient.waitForTransactionReceipt({ hash });
        console.log("✅ Circuit Breaker Toggled (System Unpaused)");
    } else {
        console.log("ℹ️ Circuit Breaker is already inactive. System is open.");
    }
  } catch (error) {
    console.error("❌ Failed to toggle circuit breaker:", error);
  }

  console.log("\n🎉 Admin Actions Completed!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
