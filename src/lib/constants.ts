// Design System Constants for LiquidityGuard AI

// ============ Colors ============

export const COLORS = {
  // Gradient colors (Purple/Indigo theme)
  gradient: {
    from: '#667eea',
    via1: '#764ba2',
    via2: '#f093fb',
    to: '#4facfe',
  },

  // Status colors
  status: {
    safe: '#10B981',      // Green (HF > 1.5)
    warning: '#F59E0B',   // Yellow (HF 1.2-1.5)
    critical: '#EF4444',  // Red (HF < 1.2)
  },

  // Chart colors
  chart: {
    eth: '#2E5BFF',       // Blue
    wbtc: '#FF6B35',      // Orange
    usdc: '#6B7280',      // Gray
    steth: '#8B5CF6',     // Purple
    dai: '#F0B90B',       // Yellow
  },

  // Background colors
  background: {
    dark: '#0A0B14',
    darker: '#1A1B2E',
    card: 'rgba(255, 255, 255, 0.05)',
  },
} as const;

// ============ Health Factor Thresholds ============

export const HEALTH_FACTOR_THRESHOLDS = {
  CRITICAL: 1.2,
  WARNING: 1.5,
  SAFE: 2.0,
} as const;

// ============ API Configuration ============

export const API_CONFIG = {
  // CoinGecko API
  coingecko: {
    baseUrl: 'https://api.coingecko.com/api/v3',
    updateInterval: 30000, // 30 seconds
  },

  // The Graph API
  theGraph: {
    // Using your custom LiqX subgraph on Ethereum Mainnet (always uses latest version)
    // Falls back to mock data if unavailable (expected for hackathon demo)
    subgraphUrl: process.env.NEXT_PUBLIC_LIQX_SUBGRAPH_URL || 'https://api.studio.thegraph.com/query/1723368/cashew-subgraph/version/latest',
    fallbackUrl: 'https://api.studio.thegraph.com/query/52869/aave-v3-ethereum/version/latest',
    updateInterval: 10000, // 10 seconds
  },

  // Python Agents
  agents: {
    positionMonitor: 'http://localhost:8101',
    yieldOptimizer: 'http://localhost:8102',
    swapOptimizer: 'http://localhost:8103',
    crossChainExecutor: 'http://localhost:8122',
    presentationTrigger: 'http://localhost:8005',
    statusInterval: 5000, // 5 seconds
  },
} as const;

// ============ Token Configuration ============

export const TOKENS = {
  ETH: {
    symbol: 'ETH',
    name: 'Ethereum',
    address: '0x0000000000000000000000000000000000000000',
    coingeckoId: 'ethereum',
    decimals: 18,
    color: COLORS.chart.eth,
  },
  WETH: {
    symbol: 'WETH',
    name: 'Wrapped Ethereum',
    address: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
    coingeckoId: 'weth',
    decimals: 18,
    color: COLORS.chart.eth,
  },
  WBTC: {
    symbol: 'WBTC',
    name: 'Wrapped Bitcoin',
    address: '0x29f2D40B0605204364af54EC677bD022dA425d03',
    coingeckoId: 'wrapped-bitcoin',
    decimals: 8,
    color: COLORS.chart.wbtc,
  },
  USDC: {
    symbol: 'USDC',
    name: 'USD Coin',
    address: '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8',
    coingeckoId: 'usd-coin',
    decimals: 6,
    color: COLORS.chart.usdc,
  },
  DAI: {
    symbol: 'DAI',
    name: 'Dai Stablecoin',
    address: '0xFF34B3d4Aee8ddCd6F9AFFFB6Fe49bD371b8a357',
    coingeckoId: 'dai',
    decimals: 18,
    color: COLORS.chart.dai,
  },
} as const;

// ============ Demo Mode Configuration ============

export const DEMO_CONFIG = {
  // Animation duration (2 minutes)
  totalDuration: 120000, // 120 seconds

  // Timeline events (in seconds)
  timeline: {
    normal: 0,              // 0:00 - Normal market
    crashStart: 20,         // 0:20 - Flash crash begins
    crashPeak: 30,          // 0:30 - Crash peak (ETH -30%, HF 1.12)
    agentDetect: 25,        // 0:25 - Position Monitor detects
    agentPlan: 40,          // 0:40 - Agents plan strategy
    agentExecute: 45,       // 0:45 - Executor performs swap
    recovery: 50,           // 0:50 - Market recovers
    complete: 120,          // 2:00 - Success metrics shown
  },

  // Mock position data
  mockPosition: {
    initialCollateral: 10000, // $10,000
    initialDebt: 5000,        // $5,000
    initialHF: 1.87,
    criticalHF: 1.12,
    finalHF: 1.65,
    savedAmount: 45000,       // $45K protected
    preventedLiquidations: 3,
  },

  // Price crash simulation
  crash: {
    ethDrop: 0.30,           // 30% drop
    duration: 10,            // 10 seconds
    volatility: 0.02,        // 2% volatility
  },
} as const;

// ============ Chart Configuration ============

export const CHART_CONFIG = {
  height: {
    landing: 400,
    demo: 350,
    presentation: 500,
  },

  margin: {
    top: 20,
    right: 30,
    left: 20,
    bottom: 20,
  },

  gradients: {
    eth: {
      id: 'ethGradient',
      start: 'rgba(46, 91, 255, 0.4)',
      end: 'rgba(46, 91, 255, 0.0)',
    },
    wbtc: {
      id: 'wbtcGradient',
      start: 'rgba(255, 107, 53, 0.4)',
      end: 'rgba(255, 107, 53, 0.0)',
    },
    usdc: {
      id: 'usdcGradient',
      start: 'rgba(107, 114, 128, 0.4)',
      end: 'rgba(107, 114, 128, 0.0)',
    },
  },

  timeRanges: [
    { label: '1D', days: 1 },
    { label: '7D', days: 7 },
    { label: '30D', days: 30 },
  ],
} as const;

// ============ Presentation Mode Configuration ============

export const PRESENTATION_CONFIG = {
  // Crash trigger options
  triggers: {
    marketCrash: {
      label: 'Market Crash',
      ethDrop: 0.30,        // 30%
      duration: 10,         // 10 seconds
    },
    flashCrash: {
      label: 'Flash Crash',
      ethDrop: 0.50,        // 50%
      duration: 1,          // Instant
    },
    gradualDecline: {
      label: 'Gradual Decline',
      ethDrop: 0.20,        // 20%
      duration: 60,         // 60 seconds
    },
    randomVolatility: {
      label: 'Random Volatility',
      ethDrop: 0.15,        // 15% average
      duration: 30,         // 30 seconds
      volatility: 0.05,     // 5% volatility
    },
  },

  // Performance metrics
  metrics: {
    responseTimeTarget: 5,    // 5 seconds
    successRateTarget: 95,    // 95%
  },
} as const;

// ============ Animation Configuration ============

export const ANIMATION_CONFIG = {
  // Framer Motion variants
  duration: {
    fast: 0.2,
    normal: 0.3,
    slow: 0.5,
  },

  ease: 'easeInOut',

  // Transitions
  fadeIn: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },

  slideIn: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 50 },
  },

  scale: {
    initial: { opacity: 0, scale: 0.8 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.8 },
  },
} as const;

// ============ Network Configuration ============

export const NETWORK_CONFIG = {
  sepolia: {
    chainId: 11155111,
    name: 'Sepolia',
    rpcUrl: process.env.NEXT_PUBLIC_ALCHEMY_SEPOLIA_URL || '',
    explorerUrl: 'https://sepolia.etherscan.io',
  },

  // Aave V3 on Sepolia
  aave: {
    poolAddress: '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951',
    dataProviderAddress: '0x3e9708d80f7B3e43118013075F7e95CE3AB31F31',
  },
} as const;

// ============ Format Configuration ============

export const FORMAT_CONFIG = {
  currency: {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  },

  percentage: {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  },

  number: {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  },
} as const;
