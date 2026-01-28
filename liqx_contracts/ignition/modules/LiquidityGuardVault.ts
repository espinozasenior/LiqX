import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

/**
 * LiquidityGuardVault Deployment Module
 * 
 * This module deploys the LiqX LiquidityGuardVault contract with protocol addresses.
 * Supports Ethereum Mainnet, Sepolia, Optimism, and Arbitrum.
 */

// ============================================
// ETHEREUM MAINNET ADDRESSES
// ============================================
const MAINNET_ADDRESSES = {
  AAVE_POOL: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2", // Aave V3 Pool
  LIDO: "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84", // Lido stETH
  WSTETH: "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0", // Wrapped stETH
  COMPOUND_COMPTROLLER: "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B", // Compound V2 Comptroller
  ONEINCH_ROUTER: "0x1111111254EEB25477B68fb85Ed929f73A960582", // 1inch Aggregation Router V5
  UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564", // Uniswap V3 SwapRouter
  UNISWAP_V2_ROUTER: "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D", // Uniswap V2 Router
  USDC: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC on Mainnet
};

// ============================================
// SEPOLIA TESTNET ADDRESSES
// ============================================
const SEPOLIA_ADDRESSES = {
  AAVE_POOL: "0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951", // Aave V3 Pool on Sepolia
  LIDO: "0x3e3FE7dBc6B4C189E7128855dD526361c49b40Af", // Lido stETH on Sepolia
  WSTETH: "0xB82381A3fBD3FaFA77B3a7bE693342618240067b", // Wrapped stETH on Sepolia
  COMPOUND_COMPTROLLER: "0x0000000000000000000000000000000000000001", // Placeholder - deploy mock for testing
  ONEINCH_ROUTER: "0x1111111254EEB25477B68fb85Ed929f73A960582", // 1inch V5 on Sepolia
  UNISWAP_V3_ROUTER: "0x3bFA4769FB09eefC5a80d6e87c3B9C650f7Ae48E", // Uniswap V3 SwapRouter on Sepolia
  UNISWAP_V2_ROUTER: "0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008", // Uniswap V2 Router on Sepolia
  USDC: "0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8", // USDC on Sepolia
};

// ============================================
// OPTIMISM ADDRESSES
// ============================================
const OPTIMISM_ADDRESSES = {
  AAVE_POOL: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  LIDO: "0x12d8Ce035c5DE3Ce39B1FDD4C1d5a745EAbA3b8C", // wstETH (No stETH on L2)
  WSTETH: "0x12d8Ce035c5DE3Ce39B1FDD4C1d5a745EAbA3b8C", // wstETH is the main token
  COMPOUND_COMPTROLLER: "0x0000000000000000000000000000000000000001", // Placeholder (Use Comet for V3)
  ONEINCH_ROUTER: "0x1111111254EEB25477B68fb85Ed929f73A960582",
  UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
  UNISWAP_V2_ROUTER: "0x0000000000000000000000000000000000000000", // No UniV2 on Optimism usually (Use V3)
  USDC: "0x0b2C639c53a9AD07A9793eb9d3C64d2139e37a1B", // Native USDC
};

// ============================================
// ARBITRUM ADDRESSES
// ============================================
const ARBITRUM_ADDRESSES = {
  AAVE_POOL: "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
  LIDO: "0x5979D7b546E38E414F7E9822514be443A4800529", // wstETH
  WSTETH: "0x5979D7b546E38E414F7E9822514be443A4800529",
  COMPOUND_COMPTROLLER: "0x0000000000000000000000000000000000000001",
  ONEINCH_ROUTER: "0x1111111254EEB25477B68fb85Ed929f73A960582",
  UNISWAP_V3_ROUTER: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
  UNISWAP_V2_ROUTER: "0x0000000000000000000000000000000000000000",
  USDC: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", // Native USDC
};

// ============================================
// BASE ADDRESSES
// ============================================
const BASE_ADDRESSES = {
  AAVE_POOL: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
  LIDO: "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452", // wstETH
  WSTETH: "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
  COMPOUND_COMPTROLLER: "0xb125E6687d4313864e53df431d5425969c15Eb2F", // cUSDCv3 Proxy
  ONEINCH_ROUTER: "0x1111111254EEB25477B68fb85Ed929f73A960582",
  UNISWAP_V3_ROUTER: "0x2626664c2603336E57B271c5C0b26F421741e481",
  UNISWAP_V2_ROUTER: "0x0000000000000000000000000000000000000000",
  USDC: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
};

// ============================================
// DEPLOYMENT MODULE
// ============================================
export default buildModule("LiquidityGuardVaultModule", (m) => {
  // ---------------------------------------------------------
  // ⚠️ SELECT NETWORK CONFIGURATION HERE
  // ---------------------------------------------------------
  // Change this variable to: MAINNET_ADDRESSES, OPTIMISM_ADDRESSES, ARBITRUM_ADDRESSES, or BASE_ADDRESSES
  const addresses = SEPOLIA_ADDRESSES; 
  // ---------------------------------------------------------

  console.log(`\n🚀 Deploying LiquidityGuardVault...`);
  console.log(`📍 Protocol Addresses:`);
  console.log(`  - Aave Pool: ${addresses.AAVE_POOL}`);
  console.log(`  - Lido (stETH): ${addresses.LIDO}`);
  console.log(`  - WstETH: ${addresses.WSTETH}`);
  console.log(`  - Compound Comptroller: ${addresses.COMPOUND_COMPTROLLER}`);
  console.log(`  - 1inch Router V5: ${addresses.ONEINCH_ROUTER}`);
  console.log(`  - Uniswap V3 Router: ${addresses.UNISWAP_V3_ROUTER}`);
  console.log(`  - Uniswap V2 Router: ${addresses.UNISWAP_V2_ROUTER}`);
  console.log(`  - USDC: ${addresses.USDC}\n`);

  // Deploy LiquidityGuardVault with all 8 constructor parameters
  const vault = m.contract("LiquidityGuardVault", [
    addresses.AAVE_POOL,
    addresses.LIDO,
    addresses.WSTETH,
    addresses.COMPOUND_COMPTROLLER,
    addresses.ONEINCH_ROUTER,
    addresses.UNISWAP_V3_ROUTER,
    addresses.UNISWAP_V2_ROUTER,
    addresses.USDC,
  ]);

  // Verify Admin Role
  m.call(vault, "hasRole", [
    "0x0000000000000000000000000000000000000000000000000000000000000000", // DEFAULT_ADMIN_ROLE
    m.getAccount(0),
  ], { id: "verify_admin_role" });

  console.log(`✅ LiquidityGuardVault deployment configured`);
  console.log(`📝 Deployer will receive DEFAULT_ADMIN_ROLE\n`);
  console.log(`⚠️  Note: Remember to call grantAgentRole() for AI agents after deployment\n`);

  return { vault };
});
