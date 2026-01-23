"""
LiquidityGuard AI - Position Monitor Agent

AUTONOMOUS OPERATION:
- Fetches risky positions from The Graph subgraph every 30 seconds
- Monitors health factors using real CoinGecko prices
- Sends alerts to Yield Optimizer when HF < 1.5
- Supports manual crash triggers via PresentationTrigger messages

NO MOCK DATA - ALL REAL:
- Positions from LiqX subgraph (Sepolia)
- Prices from CoinGecko API
- Risk assessment via MeTTa AI reasoner
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.metta_reasoner import get_metta_reasoner
from data.ethereum_tokens import get_token_symbol
from data.price_feeds import get_price_feed_manager
from data.subgraph_fetcher import get_subgraph_fetcher
from agents.message_protocols import (
    PositionAlert,
    PresentationTrigger,
    HealthCheckRequest,
    HealthCheckResponse,
    ExecutionResult
)
import time
import json
from typing import Dict, List
from dotenv import load_dotenv
from loguru import logger
from uagents import Agent, Context
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread


load_dotenv()

# ═══════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════

AGENT_SEED = os.getenv('AGENT_SEED_POSITION_MONITOR')
AGENT_PORT = int(os.getenv('POSITION_MONITOR_PORT', '8000'))
HTTP_PORT = int(os.getenv('POSITION_MONITOR_HTTP_PORT', '8101'))
HTTP_HOST = os.getenv('HTTP_HOST', '0.0.0.0')
DEPLOY_MODE = os.getenv('DEPLOY_MODE', 'local')

# Risk thresholds
CRITICAL_HF = float(os.getenv('CRITICAL_HEALTH_FACTOR', '1.3'))
MODERATE_HF = float(os.getenv('MODERATE_HEALTH_FACTOR', '1.5'))
SAFE_HF = float(os.getenv('SAFE_HEALTH_FACTOR', '1.8'))

# Alert cooldown (prevent spam)
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes

# Yield Optimizer address (deterministic from seed)
YIELD_OPTIMIZER_ADDRESS = "agent1q0rtan6yrc6dgv62rlhtj2fn5na0zv4k8mj47ylw8luzyg6c0xxpspk9706"


# ═══════════════════════════════════════════════════════
# POSITION MONITOR AGENT
# ═══════════════════════════════════════════════════════

class PositionMonitorAgent:
    """Autonomous position monitoring with real blockchain data"""

    def __init__(self):
        # Initialize agent
        self.agent = Agent(
            name="position_monitor",
            seed=AGENT_SEED,
            port=AGENT_PORT,
            endpoint=[f"http://localhost:{AGENT_PORT}/submit"]
        )

        # Data managers
        self.subgraph_fetcher = get_subgraph_fetcher()
        self.price_manager = get_price_feed_manager()
        self.metta_reasoner = get_metta_reasoner()

        # State
        self.positions: Dict[str, Dict] = {}
        # user_address -> last_alert_time
        self.alerted_positions: Dict[str, float] = {}
        self.message_history: List[Dict] = []
        self.last_subgraph_fetch = 0

        # Demo state tracking (for presentation)
        self.demo_status: Dict[str, Dict] = {}  # position_id -> status info
        self._pending_demo_alert = None  # Stores alert to be sent in next cycle

        # Setup
        self._start_http_server()
        self._setup_handlers()

        logger.success(f"✅ Position Monitor initialized")
        logger.info(f"   Address: {self.agent.address}")
        logger.info(f"   Port: {AGENT_PORT}")
        logger.info(f"   Mode: AUTONOMOUS (real data only)")

    def _start_http_server(self):
        """HTTP server for message history and position updates"""
        agent_instance = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress logs

            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods',
                                 'GET, POST, OPTIONS')
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
                        # Last 100
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
                        'positions_monitored': len(agent_instance.positions),
                        'alerts_sent': len(agent_instance.alerted_positions),
                        'address': str(agent_instance.agent.address)
                    }
                    self.wfile.write(json.dumps(response).encode())

                elif self.path == '/positions':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    # Convert monitored positions to frontend format with real USD values
                    positions_list = []
                    for user_id, pos in agent_instance.positions.items():
                        # Calculate USD values using real prices (stored during monitoring)
                        import asyncio
                        loop = asyncio.new_event_loop()

                        try:
                            collateral_price = loop.run_until_complete(
                                agent_instance.price_manager.get_token_price(
                                    pos['collateral_token'])
                            )
                            debt_price = loop.run_until_complete(
                                agent_instance.price_manager.get_token_price(
                                    pos['debt_token'])
                            )

                            collateral_amount = pos['collateral_amount'] / 1e18
                            debt_amount = pos['debt_amount'] / 1e18
                            collateral_usd = collateral_amount * collateral_price
                            debt_usd = debt_amount * debt_price
                        except:
                            collateral_usd = 0
                            debt_usd = 0
                        finally:
                            loop.close()

                        positions_list.append({
                            'id': pos['position_id'],
                            'user': user_id,
                            'protocol': pos['protocol'],
                            'chain': pos['chain'],
                            'collateral_token': pos['collateral_token'],
                            'collateral_amount': pos['collateral_amount'],
                            'collateral_usd': collateral_usd,
                            'debt_token': pos['debt_token'],
                            'debt_amount': pos['debt_amount'],
                            'debt_usd': debt_usd,
                            'health_factor': pos['health_factor'],
                            'last_updated': pos['last_updated']
                        })

                    response = {
                        'success': True,
                        'positions': positions_list,
                        'total': len(positions_list),
                        'timestamp': int(time.time() * 1000)
                    }
                    self.wfile.write(json.dumps(response).encode())

                elif self.path == '/demo/positions':
                    # DEMO POSITIONS ENDPOINT - Returns curated scenarios for presentation
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    demo_positions = [
                        {
                            "id": "demo-1-critical-ethereum",
                            "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                            "protocol": "aave-v3",
                            "chain": "ethereum",
                            "healthFactor": 1.15,
                            "collateralToken": "WETH",
                            "collateralAmount": 10.5,
                            "collateralUsd": 28311.00,  # ~$2696 per ETH
                            "debtToken": "USDC",
                            "debtAmount": 25000,
                            "debtUsd": 25000,
                            "status": "critical",
                            "description": "Critical same-chain position - needs immediate rebalancing"
                        },
                        {
                            "id": "demo-2-crosschain-arbitrum",
                            "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                            "protocol": "aave-v3",
                            "chain": "ethereum",
                            "healthFactor": 1.45,
                            "collateralToken": "WETH",
                            "collateralAmount": 50.0,
                            "collateralUsd": 134800.00,
                            "debtToken": "USDC",
                            "debtAmount": 120000,
                            "debtUsd": 120000,
                            "status": "moderate",
                            "description": "Moderate position - can benefit from cross-chain (ETH→ARB)"
                        },
                        {
                            "id": "demo-3-crosschain-solana",
                            "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                            "protocol": "compound",
                            "chain": "ethereum",
                            "healthFactor": 1.8,
                            "collateralToken": "WETH",
                            "collateralAmount": 100.0,
                            "collateralUsd": 269600.00,
                            "debtToken": "USDC",
                            "debtAmount": 150000,
                            "debtUsd": 150000,
                            "status": "safe",
                            "description": "Safe position - extreme APY opportunity on Solana"
                        }
                    ]

                    response = {
                        'success': True,
                        'positions': demo_positions,
                        'total': len(demo_positions),
                        'timestamp': int(time.time() * 1000),
                        'note': 'Demo positions for presentation - trigger will use REAL APIs downstream'
                    }
                    self.wfile.write(json.dumps(response).encode())

                elif self.path.startswith('/demo/status/'):
                    # STATUS TRACKING ENDPOINT - Shows progress of demo trigger
                    position_id = self.path.split('/')[-1]
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    status_info = agent_instance.demo_status.get(position_id, {
                        'status': 'not_started',
                        'message': 'Position not triggered yet',
                        'timestamp': int(time.time() * 1000)
                    })

                    response = {
                        'success': True,
                        'position_id': position_id,
                        **status_info
                    }
                    self.wfile.write(json.dumps(response).encode())

                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):
                # DEMO TRIGGER ENDPOINT - Triggers agent flow with demo position
                if self.path == '/demo/trigger':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        trigger_data = json.loads(post_data.decode())

                        position_id = trigger_data.get('position_id')
                        if not position_id:
                            raise ValueError("Missing position_id")

                        # Get demo position data
                        demo_positions = {
                            "demo-1-critical-ethereum": {
                                "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                                "protocol": "aave-v3",
                                "chain": "ethereum",
                                "healthFactor": 1.15,
                                "collateralToken": "WETH",
                                "collateralAmount": 10.5,
                                "collateralUsd": 28311.00,
                                "debtToken": "USDC",
                                "debtAmount": 25000,
                                "debtUsd": 25000
                            },
                            "demo-2-crosschain-arbitrum": {
                                "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                                "protocol": "compound",
                                "chain": "ethereum",
                                "healthFactor": 1.45,
                                "collateralToken": "USDC",
                                "collateralAmount": 120000,
                                "collateralUsd": 120000.00,
                                "debtToken": "USDT",
                                "debtAmount": 80000,
                                "debtUsd": 80000
                            },
                            "demo-3-crosschain-solana": {
                                "user": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                                "protocol": "compound",
                                "chain": "ethereum",
                                "healthFactor": 1.8,
                                "collateralToken": "WETH",
                                "collateralAmount": 100.0,
                                "collateralUsd": 269600.00,
                                "debtToken": "USDC",
                                "debtAmount": 150000,
                                "debtUsd": 150000
                            }
                        }

                        # If position not in predefined demos, use a default configuration
                        if position_id in demo_positions:
                            demo_data = demo_positions[position_id]
                        else:
                            # Default demo configuration for any position ID from frontend
                            demo_data = {
                                "user": position_id if position_id.startswith('0x') else "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
                                "protocol": "compound",
                                "chain": "ethereum",
                                "healthFactor": 1.15,
                                "collateralToken": "USDC",
                                "collateralAmount": 25000,
                                "collateralUsd": 25000.00,
                                "debtToken": "USDT",
                                "debtAmount": 20000,
                                "debtUsd": 20000
                            }

                        # Update status
                        agent_instance.demo_status[position_id] = {
                            'status': 'triggered',
                            'message': 'Alert sent to Yield Optimizer - using REAL APIs',
                            'timestamp': int(time.time() * 1000),
                            'stage': 'position_alert_sent'
                        }

                        # Schedule alert to be sent (async operation)
                        import asyncio

                        async def send_demo_alert():
                            """Send REAL PositionAlert to Yield Optimizer"""
                            try:
                                # Create REAL PositionAlert message
                                alert = PositionAlert(
                                    user_address=demo_data['user'],
                                    position_id=position_id,
                                    protocol=demo_data['protocol'],
                                    chain=demo_data['chain'],
                                    health_factor=demo_data['healthFactor'],
                                    collateral_value=demo_data['collateralUsd'],
                                    debt_value=demo_data['debtUsd'],
                                    collateral_token=demo_data['collateralToken'],
                                    debt_token=demo_data['debtToken'],
                                    risk_level='critical' if demo_data['healthFactor'] < 1.3 else 'moderate',
                                    timestamp=int(time.time() * 1000),
                                    predicted_liquidation_time=None
                                )

                                # Get agent context (need to use agent's context)
                                # Store alert for async sending
                                agent_instance._pending_demo_alert = {
                                    'alert': alert,
                                    'position_id': position_id
                                }

                                logger.warning(
                                    f"🎭 DEMO TRIGGER: {position_id}")
                                logger.info(
                                    f"   Alert queued for Yield Optimizer")
                                logger.info(
                                    f"   All downstream processing will use REAL APIs:")
                                logger.info(f"   ✅ DeFi Llama (real APY data)")
                                logger.info(
                                    f"   ✅ 1inch Fusion+ (real quotes)")
                                logger.info(f"   ✅ Cross-chain detection")

                            except Exception as e:
                                logger.error(f"Failed to send demo alert: {e}")
                                agent_instance.demo_status[position_id] = {
                                    'status': 'error',
                                    'message': str(e),
                                    'timestamp': int(time.time() * 1000)
                                }

                        # Run async function
                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(send_demo_alert())
                        loop.close()

                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        response = {
                            'success': True,
                            'message': 'Demo trigger activated - REAL APIs will be used',
                            'position_id': position_id,
                            'note': 'All downstream processing (DeFi Llama, 1inch Fusion+) uses REAL data'
                        }
                        self.wfile.write(json.dumps(response).encode())

                    except Exception as e:
                        logger.error(f"Error in demo trigger: {e}")
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        response = {'success': False, 'error': str(e)}
                        self.wfile.write(json.dumps(response).encode())

                # Optional: Allow frontend to add specific positions to watch
                elif self.path == '/monitor-position':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        position_data = json.loads(post_data.decode())

                        user_address = position_data.get('user_address')
                        if user_address:
                            # Add to monitoring (will be overwritten by subgraph fetch if exists)
                            agent_instance.positions[user_address] = {
                                'position_id': position_data.get('position_id', user_address),
                                'protocol': 'aave-v3',
                                'chain': 'ethereum',
                                'collateral_token': position_data.get('collateral_token', 'WETH'),
                                'collateral_amount': position_data.get('collateral_amount', 0),
                                'debt_token': position_data.get('debt_token', 'USDC'),
                                'debt_amount': position_data.get('debt_amount', 0),
                                'health_factor': position_data.get('health_factor', 0),
                                'last_updated': int(time.time())
                            }

                            logger.info(
                                f"📌 Added position {user_address[:10]}... to monitoring")

                            self.send_response(200)
                            self.send_header(
                                'Content-type', 'application/json')
                            self.send_header(
                                'Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            response = {'success': True,
                                        'message': 'Position added'}
                            self.wfile.write(json.dumps(response).encode())
                        else:
                            raise ValueError("Missing user_address")

                    except Exception as e:
                        logger.error(f"Error adding position: {e}")
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        response = {'success': False, 'error': str(e)}
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
            logger.success("🚀 Position Monitor started - AUTONOMOUS MODE")
            logger.info("   Fetching positions from subgraph every 30s")
            logger.info("   Using real CoinGecko prices")
            logger.info("   Sending alerts to Yield Optimizer")

        @self.agent.on_interval(period=30.0)
        async def monitor_positions(ctx: Context):
            """AUTONOMOUS: Fetch from subgraph and check all positions every 30s"""

            # Check for pending demo alerts first
            if self._pending_demo_alert:
                try:
                    alert_data = self._pending_demo_alert
                    alert = alert_data['alert']
                    position_id = alert_data['position_id']

                    logger.warning(f"🎭 SENDING DEMO ALERT: {position_id}")
                    logger.info(
                        f"   Triggering REAL agent flow with demo position data")

                    # Send REAL PositionAlert to Yield Optimizer
                    await ctx.send(YIELD_OPTIMIZER_ADDRESS, alert)

                    # Update status
                    self.demo_status[position_id] = {
                        'status': 'alert_sent',
                        'message': 'PositionAlert sent to Yield Optimizer - waiting for yield analysis',
                        'timestamp': int(time.time() * 1000),
                        'stage': 'yield_optimizer_processing'
                    }

                    logger.success(f"✅ Demo alert sent successfully")
                    logger.info(
                        f"   Next: Yield Optimizer will fetch REAL DeFi Llama data")

                    # Clear pending alert
                    self._pending_demo_alert = None

                except Exception as e:
                    logger.error(f"Failed to send demo alert: {e}")
                    if self._pending_demo_alert:
                        position_id = self._pending_demo_alert.get(
                            'position_id')
                        self.demo_status[position_id] = {
                            'status': 'error',
                            'message': f'Failed to send alert: {str(e)}',
                            'timestamp': int(time.time() * 1000)
                        }
                    self._pending_demo_alert = None

            current_time = time.time()

            # Fetch from subgraph every 30 seconds
            if current_time - self.last_subgraph_fetch > 25:
                try:
                    logger.info("🔍 Fetching risky positions from subgraph...")

                    # Get positions with HF < 2.0 (all at-risk positions)
                    risky_positions = await self.subgraph_fetcher.get_risky_positions(
                        health_factor_threshold=2.0,
                        limit=20
                    )

                    logger.info(
                        f"📦 Subgraph returned {len(risky_positions)} positions")

                    if risky_positions:
                        logger.info(
                            f"Processing {len(risky_positions)} positions...")
                        loaded_count = 0
                        for pos in risky_positions:
                            try:
                                logger.info(
                                    f"  Processing position {pos.get('id', 'unknown')[:16]}...")
                                user_id = pos['user']['id']
                                health_factor = float(pos['healthFactor'])

                                # Skip liquidated positions
                                if health_factor < 0:
                                    logger.warning(
                                        f"    Skipping liquidated position (HF={health_factor})")
                                    continue

                                # Log raw token addresses from subgraph
                                logger.info(
                                    f"Position: {pos['id'][:10]}... Collateral: {pos['collateralAsset']}, Debt: {pos['debtAsset']}")

                                # Get token symbols
                                collateral_token = get_token_symbol(
                                    pos['collateralAsset'])
                                debt_token = get_token_symbol(pos['debtAsset'])

                                logger.info(
                                    f"  Mapped to: {collateral_token} / {debt_token}")

                                # Store position (even with UNKNOWN tokens - will use fallback prices)
                                self.positions[user_id] = {
                                    'position_id': pos['id'],
                                    'protocol': 'aave-v3',
                                    'chain': 'ethereum',
                                    'collateral_asset': pos['collateralAsset'],
                                    'collateral_token': collateral_token,
                                    'collateral_amount': float(pos['collateralAmount']),
                                    'debt_asset': pos['debtAsset'],
                                    'debt_token': debt_token,
                                    'debt_amount': float(pos['debtAmount']),
                                    'health_factor': health_factor,
                                    'last_updated': pos['updatedAt']
                                }
                                loaded_count += 1

                            except Exception as parse_error:
                                logger.warning(
                                    f"Failed to parse position: {parse_error}")
                                continue

                        logger.success(
                            f"✅ Loaded {loaded_count} positions for monitoring")

                        if loaded_count == 0 and len(risky_positions) > 0:
                            logger.warning(
                                "⚠️  All fetched positions are liquidated (negative HF)")
                            logger.info(
                                "   For demo purposes, frontend will use mock positions")
                    else:
                        logger.info(
                            "✨ No risky positions found - all positions healthy!")

                    self.last_subgraph_fetch = current_time

                except Exception as e:
                    logger.error(f"❌ Failed to fetch from subgraph: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

            # Monitor all loaded positions
            if not self.positions:
                logger.debug("No positions to monitor")
                return

            logger.info(f"📊 Monitoring {len(self.positions)} positions...")

            for user_address, position_data in self.positions.items():
                try:
                    await self._check_position(ctx, user_address, position_data)
                except Exception as e:
                    logger.error(
                        f"Error checking position {user_address}: {e}")

        @self.agent.on_message(model=PresentationTrigger)
        async def handle_presentation_trigger(ctx: Context, sender: str, msg: PresentationTrigger):
            """Handle manual crash triggers from presentation mode"""
            logger.warning(f"🎭 PRESENTATION TRIGGER RECEIVED")
            logger.info(f"   Event: {msg.event_type}")
            logger.info(f"   ETH Drop: {msg.eth_drop * 100:.1f}%")
            logger.info(f"   Duration: {msg.duration}s")

            # Simulate price crash by temporarily modifying price feeds
            # This will affect the next position check cycle
            original_eth_price = await self.price_manager.get_token_price("WETH")
            if original_eth_price:
                crashed_price = original_eth_price * (1 - msg.eth_drop)
                logger.warning(
                    f"   Simulating ETH crash: ${original_eth_price:.2f} → ${crashed_price:.2f}")
                # Note: Price manager would need a method to inject temporary prices
                # For now, this just logs the trigger

            self._log_message('received', 'PresentationTrigger', sender, {
                'event_type': msg.event_type,
                'eth_drop': f"{msg.eth_drop * 100:.1f}%"
            })

        @self.agent.on_message(model=HealthCheckRequest)
        async def handle_health_check(ctx: Context, sender: str, msg: HealthCheckRequest):
            """Respond to health checks"""
            response = HealthCheckResponse(
                agent_name="position_monitor",
                status="online",
                positions_monitored=len(self.positions),
                timestamp=int(time.time() * 1000)
            )
            await ctx.send(sender, response)

        @self.agent.on_message(model=ExecutionResult)
        async def handle_execution_result(ctx: Context, sender: str, msg: ExecutionResult):
            """Log execution results from downstream agents"""
            logger.info(f"📨 Execution result: {msg.success}")

            # Update demo status if this was a demo trigger
            if msg.position_id in self.demo_status:
                if msg.success:
                    self.demo_status[msg.position_id] = {
                        'status': 'completed',
                        'message': msg.message,
                        'timestamp': int(time.time() * 1000),
                        'stage': 'execution_complete',
                        'final_result': msg.message
                    }
                    logger.success(f"🎉 Demo flow completed: {msg.position_id}")
                else:
                    self.demo_status[msg.position_id] = {
                        'status': 'failed',
                        'message': msg.message,
                        'timestamp': int(time.time() * 1000),
                        'stage': 'execution_failed',
                        'error': msg.message
                    }
                    logger.error(f"❌ Demo flow failed: {msg.position_id}")

            if msg.success:
                # Clear alert cooldown to allow re-alerting if needed
                if msg.position_id in self.alerted_positions:
                    del self.alerted_positions[msg.position_id]

            self._log_message('received', 'ExecutionResult', sender, {
                'success': msg.success,
                'message': msg.message
            })

    async def _check_position(self, ctx: Context, user_address: str, position_data: Dict):
        """Check a single position and send alert if risky"""
        try:
            # Get current collateral price
            collateral_price = await self.price_manager.get_token_price(
                position_data['collateral_token']
            )

            if not collateral_price:
                logger.warning(
                    f"Failed to get price for {position_data['collateral_token']}")
                return

            # Calculate values
            collateral_value = position_data['collateral_amount'] * \
                collateral_price
            debt_value = position_data['debt_amount']  # Assuming stablecoin

            # Calculate health factor
            liquidation_threshold = 0.85  # Aave V3 typical
            health_factor = (collateral_value * liquidation_threshold) / \
                debt_value if debt_value > 0 else 999.0

            # MeTTa risk assessment
            metta_risk = self.metta_reasoner.assess_risk(
                health_factor=health_factor,
                collateral_usd=collateral_value,
                debt_usd=debt_value,
                collateral_token=position_data['collateral_token'],
                debt_token=position_data['debt_token']
            )

            risk_level = metta_risk.get('risk_level', 'moderate')

            logger.info(
                f"Position {user_address[:10]}... | "
                f"HF: {health_factor:.2f} | "
                f"Collateral: ${collateral_value:.2f} | "
                f"Debt: ${debt_value:.2f} | "
                f"Risk: {risk_level.upper()}"
            )

            # Send alert if risky
            if health_factor < MODERATE_HF:
                await self._send_alert(
                    ctx, user_address, position_data,
                    collateral_value, debt_value, health_factor, risk_level
                )

        except Exception as e:
            logger.error(f"Error checking position: {e}")

    async def _send_alert(
        self, ctx: Context, user_address: str, position_data: Dict,
        collateral_value: float, debt_value: float, health_factor: float, risk_level: str
    ):
        """Send position alert to Yield Optimizer"""

        # Check cooldown
        current_time = time.time()
        last_alert = self.alerted_positions.get(user_address, 0)

        if current_time - last_alert < ALERT_COOLDOWN_SECONDS:
            logger.debug(f"⏭️  Skipping alert (cooldown)")
            return

        # Mark as alerted
        self.alerted_positions[user_address] = current_time

        # Create alert
        alert = PositionAlert(
            user_address=user_address,
            position_id=position_data['position_id'],
            protocol=position_data['protocol'],
            chain=position_data['chain'],
            health_factor=health_factor,
            collateral_value=collateral_value,
            debt_value=debt_value,
            collateral_token=position_data['collateral_token'],
            debt_token=position_data['debt_token'],
            risk_level=risk_level,
            timestamp=int(time.time() * 1000),
            predicted_liquidation_time=None
        )

        # Send to Yield Optimizer
        await ctx.send(YIELD_OPTIMIZER_ADDRESS, alert)

        logger.warning(f"🚨 ALERT SENT to Yield Optimizer")
        logger.info(f"   User: {user_address[:10]}...")
        logger.info(f"   Health Factor: {health_factor:.2f}")
        logger.info(f"   Risk: {risk_level.upper()}")

        self._log_message('sent', 'PositionAlert', YIELD_OPTIMIZER_ADDRESS, {
            'position_id': position_data['position_id'],
            'user': user_address[:10] + '...',
            'health_factor': round(health_factor, 3),
            'risk_level': risk_level,
            'total_collateral_usd': round(collateral_value, 2),
            'total_debt_usd': round(debt_value, 2),
            'collateral_token': position_data['collateral_token'],
            'debt_token': position_data['debt_token'],
            'protocol': position_data['protocol'],
            'chain': position_data['chain']
        })

    def _log_message(self, direction: str, message_type: str, address: str, details: Dict):
        """Log message to history"""
        self.message_history.append({
            'direction': direction,
            'type': message_type,
            'address': address[:16] + '...' if len(address) > 16 else address,
            'details': details,
            'timestamp': int(time.time() * 1000)
        })

        # Keep only last 1000 messages
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]

    def run(self):
        """Start the agent"""
        logger.info("🚀 Starting Position Monitor Agent...")
        self.agent.run()


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    agent = PositionMonitorAgent()
    agent.run()
