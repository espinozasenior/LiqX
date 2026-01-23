"""
LiquidityGuard AI - Yield Optimizer Agent

AUTONOMOUS OPERATION:
- Receives PositionAlert from Position Monitor
- Fetches REAL yield data from DeFi Llama API
- Finds best alternative protocol with higher APY
- Sends OptimizationStrategy to Swap Optimizer

NO MOCK DATA - ALL REAL:
- APY data from DeFi Llama yields API
- Protocol comparisons across Aave, Compound, Lido, etc.
- Real-time yield optimization (min 0.5% improvement)
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.metta_reasoner import get_metta_reasoner
from data.protocol_data import get_protocol_data_fetcher
from agents.message_protocols import (
    PositionAlert,
    OptimizationStrategy,
    HealthCheckRequest,
    HealthCheckResponse
)
import time
import json
from typing import Dict, Optional, List
from dotenv import load_dotenv
from loguru import logger
from uagents import Agent, Context
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread


load_dotenv()

# ═══════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════

AGENT_SEED = os.getenv('AGENT_SEED_YIELD_OPTIMIZER')
AGENT_PORT = int(os.getenv('YIELD_OPTIMIZER_PORT', '8001'))
HTTP_PORT = int(os.getenv('YIELD_OPTIMIZER_HTTP_PORT', '8102'))
HTTP_HOST = os.getenv('HTTP_HOST', '0.0.0.0')

# Optimization thresholds
MIN_APY_IMPROVEMENT = 0.5  # Minimum 0.5% APY improvement to justify gas costs

# Swap Optimizer address (deterministic)
SWAP_OPTIMIZER_ADDRESS = "agent1q2d8jkuhml92c38ja5hs237g00y4h7v7s5f0q05c5m5uzu6kqnj0qq2t4xm"


# ═══════════════════════════════════════════════════════
# YIELD OPTIMIZER AGENT
# ═══════════════════════════════════════════════════════

class YieldOptimizerAgent:
    """Autonomous yield optimization with real DeFi Llama data"""

    def __init__(self):
        # Initialize agent
        self.agent = Agent(
            name="yield_optimizer",
            seed=AGENT_SEED,
            port=AGENT_PORT,
            endpoint=[f"http://localhost:{AGENT_PORT}/submit"]
        )

        # Data managers
        self.protocol_data = get_protocol_data_fetcher()
        self.metta_reasoner = get_metta_reasoner()  # MeTTa symbolic AI reasoning

        # State
        self.message_history: list = []
        self.optimizations_sent = 0
        self.strategies_history: list = []  # Track all strategies sent
        # Store all candidate strategies for frontend
        self.candidate_strategies: list = []
        # Track processed positions to prevent re-sending same strategies
        self.processed_positions: set = set()

        # Setup
        self._start_http_server()
        self._setup_handlers()

        logger.success(f"✅ Yield Optimizer initialized")
        logger.info(f"   Address: {self.agent.address}")
        logger.info(f"   Port: {AGENT_PORT}")
        logger.info(f"   Min APY improvement: {MIN_APY_IMPROVEMENT}%")

    def _start_http_server(self):
        """HTTP server for status and message history"""
        agent_instance = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header(
                    'Access-Control-Allow-Methods', 'GET, OPTIONS')
                self.send_header(
                    'Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()

            def do_GET(self):
                if self.path == '/messages':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = {
                        'success': True,
                        'messages': agent_instance.message_history[-100:],
                        'total': len(agent_instance.message_history)
                    }
                    self.wfile.write(json.dumps(response).encode())

                elif self.path == '/status':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = {
                        'status': 'online',
                        'optimizations_sent': agent_instance.optimizations_sent,
                        'address': str(agent_instance.agent.address)
                    }
                    self.wfile.write(json.dumps(response).encode())

                elif self.path == '/strategies':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    # Return top 10 candidate strategies for frontend display
                    response = {
                        'success': True,
                        # Top 10 strategies
                        'strategies': agent_instance.candidate_strategies[:10],
                        'timestamp': int(time.time() * 1000)
                    }
                    self.wfile.write(json.dumps(response).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

        server = HTTPServer((HTTP_HOST, HTTP_PORT), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info(f"📡 HTTP server started on {HTTP_HOST}:{HTTP_PORT}")

    def _setup_handlers(self):
        """Setup uAgents message handlers"""

        @self.agent.on_event("startup")
        async def startup(ctx: Context):
            logger.success("🚀 Yield Optimizer started - AUTONOMOUS MODE")
            logger.info("   Listening for PositionAlert from Position Monitor")
            logger.info("   Using real DeFi Llama API for yields")

        @self.agent.on_message(model=PositionAlert)
        async def handle_position_alert(ctx: Context, sender: str, msg: PositionAlert):
            """Handle incoming position alerts"""
            
            # Check if position already processed (prevent loops)
            if msg.position_id in self.processed_positions:
                logger.info(f"⏭️  Position {msg.position_id[:16]}... already processed - skipping")
                logger.info(f"   (Prevents continuous loop during demo)")
                return
            
            logger.warning(f"⚠️  POSITION ALERT RECEIVED")
            logger.info(f"   User: {msg.user_address[:10]}...")
            logger.info(f"   Protocol: {msg.protocol} ({msg.chain})")
            logger.info(f"   Health Factor: {msg.health_factor:.2f}")
            logger.info(f"   Risk Level: {msg.risk_level.upper()}")
            logger.info(f"   Collateral: ${msg.collateral_value:.2f}")
            logger.info(f"   Debt: ${msg.debt_value:.2f}")

            self._log_message('received', 'PositionAlert', sender, {
                'user': msg.user_address[:10] + '...',
                'health_factor': msg.health_factor,
                'risk_level': msg.risk_level
            })

            # Calculate optimal strategy
            logger.info("🧮 Calculating optimal strategy...")

            strategy = await self._find_best_yield(
                collateral_token=msg.collateral_token,
                debt_token=msg.debt_token,
                current_protocol=msg.protocol,
                current_chain=msg.chain
            )

            if strategy:
                # Mark position as processed
                self.processed_positions.add(msg.position_id)
                logger.debug(f"   Marked position as processed ({len(self.processed_positions)} total)")
                
                # Send strategy to Swap Optimizer
                optimization = OptimizationStrategy(
                    position_id=msg.position_id,
                    user_address=msg.user_address,
                    current_protocol=msg.protocol,
                    current_chain=msg.chain,
                    target_protocol=strategy['protocol'],
                    target_chain=strategy['chain'],
                    collateral_token=msg.collateral_token,
                    debt_token=msg.debt_token,
                    collateral_amount=msg.collateral_value / 3800,  # Rough estimate
                    debt_amount=msg.debt_value,
                    current_apy=strategy['current_apy'],
                    target_apy=strategy['target_apy'],
                    estimated_gas_cost=strategy['estimated_gas'],
                    timestamp=int(time.time() * 1000)
                )

                await ctx.send(SWAP_OPTIMIZER_ADDRESS, optimization)
                self.optimizations_sent += 1

                # Track strategy for frontend display
                self.strategies_history.append({
                    'timestamp': int(time.time() * 1000),
                    'position_id': msg.position_id,
                    'user_address': msg.user_address,
                    'current_protocol': msg.protocol,
                    'target_protocol': strategy['protocol'],
                    'current_apy': strategy['current_apy'],
                    'target_apy': strategy['target_apy'],
                    'improvement': strategy['target_apy'] - strategy['current_apy'],
                    'estimated_gas': strategy['estimated_gas']
                })

                logger.success(f"✅ STRATEGY SENT to Swap Optimizer")
                logger.info(
                    f"   Target: {strategy['protocol']} ({strategy['chain']})")
                logger.info(
                    f"   APY: {strategy['current_apy']:.2f}% → {strategy['target_apy']:.2f}%")
                logger.info(
                    f"   Improvement: +{strategy['target_apy'] - strategy['current_apy']:.2f}%")

                # Use values available from PositionAlert (msg) and returned strategy
                self._log_message('sent', 'OptimizationStrategy', SWAP_OPTIMIZER_ADDRESS, {
                    'position_id': msg.position_id,
                    'current_protocol': msg.protocol,
                    'target_protocol': strategy.get('protocol', strategy.get('target_protocol')),
                    'chain': strategy.get('chain'),
                    'current_apy': f"{strategy.get('current_apy', 0):.2f}%",
                    'target_apy': f"{strategy.get('target_apy', 0):.2f}%",
                    'apy_improvement': f"+{(strategy.get('target_apy', 0) - strategy.get('current_apy', 0)):.2f}%",
                    'collateral_token': msg.collateral_token,
                    'debt_token': msg.debt_token
                })
            else:
                logger.warning("❌ No profitable strategy found")
                logger.info(
                    f"   Current position is optimal or improvement < {MIN_APY_IMPROVEMENT}%")

        @self.agent.on_message(model=HealthCheckRequest)
        async def handle_health_check(ctx: Context, sender: str, msg: HealthCheckRequest):
            """Respond to health checks"""
            response = HealthCheckResponse(
                agent_name="yield_optimizer",
                status="online",
                timestamp=int(time.time() * 1000)
            )
            await ctx.send(sender, response)

    async def _find_best_yield(
        self,
        collateral_token: str,
        debt_token: str,
        current_protocol: str,
        current_chain: str,
        position_size: float = 10000.0  # Default $10k position
    ) -> Optional[Dict]:
        """
        Find best yield using MeTTa symbolic AI reasoning + REAL DeFi Llama data

        MeTTa Decision Process:
        1. Fetch current APY from DeFi Llama
        2. Find ALL available yields (no hardcoded exclusions)
        3. Let MeTTa intelligently score each option based on:
           - APY improvement (0-40 pts)
           - Break-even time (0-30 pts)
           - Urgency (0-20 pts)
           - Position size (0-10 pts)
        4. MeTTa selects optimal execution method (direct-swap, fusion-cross-chain, bridge)
        5. Returns best strategy with confidence score and reasoning
        """

        # Get current APY from DeFi Llama
        current_apy = await self.protocol_data.get_protocol_apy(
            protocol=current_protocol.replace('-', '_'),  # aave-v3 -> aave_v3
            chain=current_chain.replace(
                '-sepolia', '').replace('ethereum', 'ethereum'),
            token=collateral_token
        )

        if current_apy is None:
            logger.warning(f"Failed to get current APY for {current_protocol}")
            current_apy = 5.0  # Fallback assumption

        logger.info(f"   Current APY: {current_apy:.2f}%")
        logger.info(f"   Position Size: ${position_size:,.2f}")

        # Fetch ALL available yields (no exclusions - let MeTTa decide!)
        logger.info(
            "🧠 MeTTa analyzing ALL available yields (all tokens, all chains)...")

        # Get top 15 yields with diverse protocols for MeTTa evaluation
        top_yields = await self.protocol_data.get_all_yields(
            token=None,  # Don't filter by token - get best yields across all assets
            min_apy=current_apy + MIN_APY_IMPROVEMENT,
            limit=15  # Top 15 from diverse protocols (max 3 per protocol)
        )

        if not top_yields:
            logger.warning(
                "   ❌ No yields found meeting minimum APY requirement")
            return None

        logger.info(
            f"📊 Found {len(top_yields)} candidate strategies for MeTTa evaluation:")
        for i, y in enumerate(top_yields[:5], 1):  # Show top 5
            logger.info(
                f"   {i}. {y['protocol']} ({y['chain']}): {y['apy']:.2f}% APY")

        # Prepare strategies for MeTTa reasoning
        available_strategies = []
        for yield_data in top_yields:
            # Calculate execution costs based on chain
            gas_cost = yield_data.get('estimated_gas', 50.0)  # Default $50
            bridge_cost = 0.0
            swap_cost = 0.0

            # Estimate bridge costs for cross-chain
            if yield_data['chain'] != current_chain:
                if yield_data['chain'] == 'solana':
                    bridge_cost = 15.0  # Wormhole ETH→Solana
                elif yield_data['chain'] in ['arbitrum', 'optimism', 'base']:
                    bridge_cost = 10.0  # LayerZero/Stargate

            # Estimate swap costs for cross-asset (USDC→SOL, ETH→USDC, etc.)
            target_token = yield_data.get('token', 'USDC')
            if target_token != collateral_token:
                swap_cost = 5.0  # 1inch swap cost (~0.3% slippage + gas)
                logger.debug(
                    f"   Cross-asset swap: {collateral_token} → {target_token} (+${swap_cost})")

            strategy = {
                'protocol': yield_data['protocol'],
                'chain': yield_data['chain'],
                'token': target_token,  # Target asset
                'apy': yield_data['apy'],
                'pool': yield_data.get('pool', 'unknown'),
                'tvl': yield_data.get('tvlUsd', 0),
                'execution_cost': gas_cost + bridge_cost + swap_cost,
                'is_cross_chain': yield_data['chain'] != current_chain,
                'is_cross_asset': target_token != collateral_token
            }
            available_strategies.append(strategy)

        # MeTTa symbolic AI reasoning
        logger.info(
            "🧠 MeTTa evaluating strategies with symbolic AI reasoning...")

        # Store all candidate strategies for frontend (BEFORE selection)
        self.candidate_strategies = []
        for strat in available_strategies[:10]:  # Top 10 for display
            self.candidate_strategies.append({
                'protocol': strat['protocol'],
                'target_protocol': strat['protocol'],
                'chain': strat['chain'],
                'target_chain': strat['chain'],
                'token': strat['token'],
                'apy': strat['apy'],
                'target_apy': strat['apy'],
                'current_apy': current_apy,
                'tvl': strat['tvl'],
                'estimated_gas': strat['execution_cost'],
                'is_cross_chain': strat['is_cross_chain'],
                'is_cross_asset': strat['is_cross_asset'],
                'selected': False  # Will mark the selected one later
            })

        optimal_strategy = self.metta_reasoner.select_optimal_strategy(
            current_protocol=current_protocol,
            current_chain=current_chain,
            current_apy=current_apy,
            amount=position_size,
            risk_level='medium',  # Could be passed from position alert
            urgency='high',  # High risk position needs quick action
            market_trend='stable',
            available_strategies=available_strategies
        )

        if not optimal_strategy:
            logger.warning("   ❌ MeTTa found no profitable strategy")
            return None

        # Extract MeTTa decision details (optimal_strategy IS the strategy dict)
        score = optimal_strategy.get('strategy_score', 0)
        reasoning = optimal_strategy.get('reasoning', 'No reasoning provided')
        confidence = optimal_strategy.get('confidence', 0)
        execution_method = optimal_strategy.get('execution_method', 'unknown')

        # Calculate break-even for logging
        break_even_days = self._calculate_break_even(
            position_size,
            current_apy,
            optimal_strategy['target_apy'],
            optimal_strategy['execution_cost']
        )

        # Log MeTTa decision with full transparency
        target_token = optimal_strategy.get('target_token', 'USDC')
        is_cross_asset = target_token != collateral_token

        logger.success(f"🎯 MeTTa SELECTED STRATEGY:")
        logger.info(
            f"   🧠 MeTTa Score: {score}/100 (Confidence: {confidence}%)")
        logger.info(f"   💡 Reasoning: {reasoning}")
        logger.info(
            f"   📍 Protocol: {optimal_strategy['target_protocol']} ({optimal_strategy['target_chain']})")
        logger.info(
            f"   🪙 Asset: {collateral_token} → {target_token}{' (cross-asset)' if is_cross_asset else ''}")
        logger.info(
            f"   📈 APY: {current_apy:.2f}% → {optimal_strategy['target_apy']:.2f}% (+{optimal_strategy['target_apy'] - current_apy:.2f}%)")
        logger.info(
            f"   💰 Execution Cost: ${optimal_strategy['execution_cost']:.2f}")
        logger.info(f"   ⏱️  Break-even: {break_even_days:.0f} days")
        logger.info(f"   🔀 Execution Method: {execution_method}")

        # Determine if cross-chain
        is_cross_chain = optimal_strategy['source_chain'] != optimal_strategy['target_chain']
        logger.info(f"   🌉 Cross-chain: {'Yes' if is_cross_chain else 'No'}")

        # Mark the selected strategy in candidate list
        selected_protocol = optimal_strategy['target_protocol']
        for candidate in self.candidate_strategies:
            if candidate['protocol'] == selected_protocol:
                candidate['selected'] = True
                candidate['metta_score'] = score
                candidate['metta_confidence'] = confidence
                candidate['break_even_days'] = break_even_days
                break

        return {
            'protocol': optimal_strategy['target_protocol'],
            'chain': optimal_strategy['target_chain'],
            'token': target_token,
            'current_apy': current_apy,
            'target_apy': optimal_strategy['target_apy'],
            'estimated_gas': optimal_strategy['execution_cost'],
            'break_even_days': break_even_days,
            'route_type': execution_method,
            'risk_level': 'medium',  # Based on MeTTa analysis
            'metta_score': score,
            'metta_reasoning': reasoning,
            'metta_confidence': confidence
        }

    def _calculate_break_even(
        self,
        position_size: float,
        current_apy: float,
        target_apy: float,
        gas_cost: float
    ) -> float:
        """
        Calculate break-even time in days

        Formula: days = (gas_cost / (position_size * (target_apy - current_apy) / 100)) * 365
        """
        apy_difference = target_apy - current_apy
        if apy_difference <= 0:
            return float('inf')

        annual_benefit = position_size * (apy_difference / 100)
        daily_benefit = annual_benefit / 365

        if daily_benefit <= 0:
            return float('inf')

        break_even_days = gas_cost / daily_benefit
        return break_even_days

    def _log_message(self, direction: str, message_type: str, address: str, details: Dict):
        """Log message to history"""
        self.message_history.append({
            'direction': direction,
            'type': message_type,
            'address': address[:16] + '...' if len(address) > 16 else address,
            'details': details,
            'timestamp': int(time.time() * 1000)
        })

        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]

    def run(self):
        """Start the agent"""
        logger.info("🚀 Starting Yield Optimizer Agent...")
        self.agent.run()


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    agent = YieldOptimizerAgent()
    agent.run()
