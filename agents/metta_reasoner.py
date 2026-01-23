"""
LiquidityGuard AI - MeTTa Reasoning Engine

Integrates MeTTa symbolic reasoning with Python agents for:
- Advanced risk assessment
- Strategic decision making
- Pattern-based optimization
- Self-learning capabilities
"""

import os
from typing import Dict, List, Optional, Any
from loguru import logger

try:
    from hyperon import MeTTa, E, S, V
    HYPERON_AVAILABLE = True
    logger.success(
        "✅ Hyperon module loaded - using real MeTTa symbolic reasoning")
except ImportError as e:
    HYPERON_AVAILABLE = False
    logger.warning(f"⚠️  Hyperon not available - using fallback logic. Error: {e}")


class MeTTaReasoner:
    """
    MeTTa Reasoning Engine for LiquidityGuard AI

    Provides symbolic AI reasoning for:
    - Risk assessment
    - Strategy selection
    - Pattern matching
    - Adaptive learning
    """

    def __init__(self, metta_files_path: str = "metta"):
        self.metta_path = metta_files_path
        self.risk_assessment_file = os.path.join(
            self.metta_path, "risk_assessment.metta")
        self.strategy_file = os.path.join(
            self.metta_path, "strategy_selection.metta")

        # Initialize MeTTa runtime
        self.metta_available = HYPERON_AVAILABLE
        self.metta = None

        if self.metta_available:
            try:
                self.metta = MeTTa()
                self._load_metta_files()
                logger.info(
                    "✅ MeTTa reasoning engine initialized with hyperon")
            except Exception as e:
                logger.error(f"Failed to initialize MeTTa: {e}")
                self.metta_available = False

        if not self.metta_available:
            logger.warning(
                "⚠️  MeTTa not available - agents will not use symbolic reasoning")

    def _load_metta_files(self):
        """Load MeTTa reasoning files into the runtime"""
        if not self.metta:
            return

        try:
            # Load risk assessment logic
            if os.path.exists(self.risk_assessment_file):
                with open(self.risk_assessment_file, 'r') as f:
                    risk_code = f.read()
                self.metta.run(risk_code)
                logger.info(f"✅ Loaded {self.risk_assessment_file}")

            # Load strategy selection logic
            if os.path.exists(self.strategy_file):
                with open(self.strategy_file, 'r') as f:
                    strategy_code = f.read()
                self.metta.run(strategy_code)
                logger.info(f"✅ Loaded {self.strategy_file}")

        except Exception as e:
            logger.error(f"Failed to load MeTTa files: {e}")

    def _execute_metta(self, expression: str) -> Optional[Any]:
        """Execute MeTTa expression and return result"""
        if not self.metta_available or not self.metta:
            return None

        try:
            result = self.metta.run(expression)
            if result and len(result) > 0:
                # MeTTa returns a list of results
                # Get the first result and convert to string
                first_result = result[0]
                result_str = str(first_result)

                # Check for errors in the result
                if "Error" in result_str or "IncorrectNumberOfArguments" in result_str:
                    logger.error(f"MeTTa execution error: {result_str}")
                    return None

                return result_str
            return None
        except Exception as e:
            logger.error(f"MeTTa execution failed: {e}")
            return None

    # ═══════════════════════════════════════════════════════
    # RISK ASSESSMENT
    # ═══════════════════════════════════════════════════════

    def calculate_risk_level(self, health_factor: float) -> str:
        """
        Calculate risk level using MeTTa reasoning

        Args:
            health_factor: Position health factor

        Returns:
            Risk level: critical, high, moderate, low, or safe
        """
        if self.metta_available and self.metta:
            expression = f"!(calculate-risk-level {health_factor})"
            result = self._execute_metta(expression)
            if result:
                # Clean up the result string
                risk_level = result.strip('[]() ')
                logger.debug(
                    f"🧠 MeTTa risk calculation: HF={health_factor} -> {risk_level}")
                return risk_level

        logger.error("MeTTa reasoning not available for risk calculation")
        raise RuntimeError("MeTTa reasoning is required but not available")

    def liquidation_probability(
        self,
        health_factor: float,
        volatility: float
    ) -> float:
        """
        Calculate liquidation probability using MeTTa

        Args:
            health_factor: Position health factor
            volatility: Market volatility percentage

        Returns:
            Probability (0-100%)
        """
        if self.metta_available and self.metta:
            expression = f"!(liquidation-probability {health_factor} {volatility})"
            result = self._execute_metta(expression)
            if result:
                try:
                    prob = float(result.strip('[]() '))
                    logger.debug(
                        f"🧠 MeTTa liquidation prob: HF={health_factor}, Vol={volatility} -> {prob}%")
                    return prob
                except ValueError:
                    pass

        logger.error(
            "MeTTa reasoning not available for liquidation probability")
        raise RuntimeError("MeTTa reasoning is required but not available")

    def urgency_score(
        self,
        health_factor: float,
        liquidation_prob: float,
        time_to_liquidation: int
    ) -> int:
        """
        Calculate urgency score (0-10)

        Args:
            health_factor: Position health factor
            liquidation_prob: Liquidation probability
            time_to_liquidation: Time to liquidation in seconds

        Returns:
            Urgency score (0-10)
        """
        if self.metta_available and self.metta:
            expression = f"!(urgency-score {health_factor} {liquidation_prob} {time_to_liquidation})"
            result = self._execute_metta(expression)
            if result:
                try:
                    score = int(float(result.strip('[]() ')))
                    logger.debug(f"🧠 MeTTa urgency score: {score}/10")
                    return score
                except ValueError:
                    pass

        logger.error("MeTTa reasoning not available for urgency calculation")
        raise RuntimeError("MeTTa reasoning is required but not available")

    def assess_risk(
        self,
        health_factor: float,
        collateral_usd: float = 0.0,
        debt_usd: float = 0.0,
        collateral_token: str = "",
        debt_token: str = "",
        volatility: float = 0.5,
        market_trend: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Comprehensive risk assessment using MeTTa reasoning

        Returns:
            Dictionary with complete risk analysis
        """
        try:
            risk_level = self.calculate_risk_level(health_factor)
            liq_prob = self.liquidation_probability(health_factor, volatility)
            urgency = self.urgency_score(health_factor, liq_prob, 3600)

            # Match risk scenario
            scenario = self._match_risk_scenario(health_factor, collateral_usd)

            # Get recommended actions
            actions = self._recommend_actions(scenario)

            # Determine priority
            priority = "EMERGENCY" if urgency >= 8 else \
                       "HIGH" if urgency >= 6 else \
                       "NORMAL" if urgency >= 5 else "LOW"

            result = {
                "risk_level": risk_level,
                "scenario": scenario,
                "liquidation_probability": liq_prob,
                "urgency_score": urgency,
                "execution_priority": priority,
                "recommended_actions": actions,
                "requires_immediate_action": urgency >= 7,
                "reasoning": f"Health factor {health_factor:.2f} with {volatility:.1f}% volatility in {market_trend} market",
                "using_metta": True  # Flag indicating real MeTTa was used
            }

            logger.info(
                f"🧠 MeTTa Risk Assessment: {risk_level.upper()} (urgency: {urgency}/10)")

            return result

        except Exception as e:
            logger.error(f"MeTTa risk assessment failed: {e}")
            # Return fallback response
            simple_risk = "critical" if health_factor < 1.3 else "high" if health_factor < 1.5 else "moderate"
            return {
                "risk_level": simple_risk,
                "scenario": "UNKNOWN",
                "liquidation_probability": 50.0,
                "urgency_score": 5,
                "execution_priority": "NORMAL",
                "recommended_actions": ["monitor"],
                "requires_immediate_action": health_factor < 1.3,
                "reasoning": f"Fallback assessment (MeTTa unavailable): HF {health_factor:.2f}",
                "using_metta": False  # Flag indicating fallback was used
            }

    def _match_risk_scenario(self, health_factor: float, collateral_usd: float) -> str:
        """Match position to risk scenario using MeTTa"""
        if self.metta_available and self.metta:
            expression = f"!(match-risk-scenario {health_factor} {collateral_usd})"
            result = self._execute_metta(expression)
            if result:
                # MeTTa returns symbols without quotes, convert to uppercase string
                scenario = result.strip('[]() ').replace('-', '_').upper()
                logger.debug(f"🧠 MeTTa scenario match: {scenario}")
                return scenario

        logger.error("MeTTa reasoning not available for scenario matching")
        raise RuntimeError("MeTTa reasoning is required but not available")

    def _recommend_actions(self, scenario: str) -> List[str]:
        """Generate action recommendations using MeTTa"""
        if self.metta_available and self.metta:
            # Convert scenario string to symbol format (remove underscores, lowercase with hyphens)
            scenario_symbol = scenario.replace('_', '-')
            expression = f'!(recommend-action {scenario_symbol})'
            result = self._execute_metta(expression)
            if result:
                # Parse the cons list result from MeTTa
                # Result format: (cons action1 (cons action2 (cons action3 empty)))
                actions_str = result.strip('[]() ')

                # Extract actions by finding symbols between 'cons' and next 'cons' or 'empty'
                actions = []
                parts = actions_str.split()
                i = 0
                while i < len(parts):
                    if parts[i] == 'cons' and i + 1 < len(parts):
                        action = parts[i + 1].strip('()')
                        if action != 'empty' and action != 'cons':
                            actions.append(action.replace('-', '_'))
                    i += 1

                logger.debug(f"🧠 MeTTa actions for {scenario}: {actions}")
                return actions if actions else ["manual-review"]

        logger.error(
            "MeTTa reasoning not available for action recommendations")
        raise RuntimeError("MeTTa reasoning is required but not available")

    # ═══════════════════════════════════════════════════════
    # STRATEGY SELECTION
    # ═══════════════════════════════════════════════════════

    def calculate_profitability(
        self,
        amount: float,
        current_apy: float,
        target_apy: float,
        execution_cost: float
    ) -> Dict[str, float]:
        """
        Calculate strategy profitability using MeTTa

        Returns:
            Dict with annual_profit, break_even_months, is_profitable
        """
        apy_diff = target_apy - current_apy

        if self.metta_available and self.metta:
            try:
                # Calculate using MeTTa

                # Annual profit calculation
                expr_profit = f"!(calculate-annual-profit {amount} {current_apy} {target_apy})"
                result_profit = self._execute_metta(expr_profit)

                if result_profit:
                    annual_profit = float(result_profit.strip('[]() '))

                    # Break-even calculation
                    expr_breakeven = f"!(break-even-months {annual_profit} {execution_cost})"
                    result_breakeven = self._execute_metta(expr_breakeven)

                    if result_breakeven:
                        break_even_months = float(
                            result_breakeven.strip('[]() '))
                        is_profitable = break_even_months < 6

                        logger.debug(
                            f"🧠 MeTTa profitability: profit=${annual_profit:.2f}, break-even={break_even_months:.1f}mo")

                        return {
                            "annual_profit": annual_profit,
                            "apy_improvement": apy_diff,
                            "break_even_months": break_even_months,
                            "is_profitable": is_profitable
                        }
            except Exception as e:
                logger.warning(f"MeTTa profitability calculation failed: {e}")

        # Fallback calculation
        logger.debug("Using fallback profitability calculation")
        annual_profit = amount * (apy_diff / 100)
        break_even_months = (execution_cost * 12) / \
            annual_profit if annual_profit > 0 else 999

        return {
            "annual_profit": annual_profit,
            "apy_improvement": apy_diff,
            "break_even_months": break_even_months,
            "is_profitable": break_even_months < 6
        }

    def score_strategy(
        self,
        apy_improvement: float,
        break_even_months: float,
        urgency: int,
        amount: float
    ) -> float:
        """
        Score a strategy (0-100)

        Uses MeTTa reasoning for intelligent scoring, falls back to heuristics
        """
        if self.metta_available and self.metta:
            expression = f"!(score-strategy {apy_improvement} {break_even_months} {urgency} {amount})"
            result = self._execute_metta(expression)
            if result:
                try:
                    score = float(result.strip('[]() '))
                    logger.debug(f"🧠 MeTTa strategy score: {score}/100")
                    return score
                except ValueError:
                    pass

        # Fallback heuristic scoring when MeTTa is not available
        logger.debug("Using fallback heuristic scoring (MeTTa not available)")

        # APY improvement: 0-40 points (higher is better)
        apy_score = min(40, (apy_improvement / 100) * 40)

        # Break-even time: 0-30 points (faster is better)
        if break_even_months <= 1:
            breakeven_score = 30
        elif break_even_months <= 3:
            breakeven_score = 20
        elif break_even_months <= 6:
            breakeven_score = 10
        else:
            breakeven_score = 0

        # Urgency: 0-20 points (higher urgency = prefer faster execution)
        urgency_score = (urgency / 10) * 20

        # Position size: 0-10 points (larger positions = worth higher costs)
        size_score = min(10, (amount / 50000) * 10)

        total_score = apy_score + breakeven_score + urgency_score + size_score
        logger.debug(
            f"📊 Fallback score: {total_score:.1f}/100 (APY: {apy_score:.1f}, BE: {breakeven_score:.1f}, Urgency: {urgency_score:.1f}, Size: {size_score:.1f})")

        return total_score

    def select_execution_method(
        self,
        from_chain: str,
        to_chain: str,
        amount: float,
        urgency: int
    ) -> str:
        """
        Select optimal execution method using MeTTa reasoning

        Returns:
            Execution method: direct-swap, layerzero-pyusd, standard-bridge, fusion-cross-chain
        """
        if self.metta_available and self.metta:
            # Pass urgency as number (not string)
            expression = f'!(select-execution-method "{from_chain}" "{to_chain}" {amount} {urgency})'
            result = self._execute_metta(expression)
            if result:
                method = result.strip('[]() "')
                logger.debug(f"🧠 MeTTa execution method: {method}")
                return method

        # Fallback heuristic execution method selection
        logger.debug(
            "Using fallback heuristic execution method selection (MeTTa not available)")

        # Same chain = direct swap
        if from_chain == to_chain:
            return "direct-swap"

        # PYUSD special handling
        if "pyusd" in from_chain.lower() or "pyusd" in to_chain.lower():
            return "layerzero-pyusd"

        # Solana cross-chain = use Fusion+ (1inch)
        if from_chain == "solana" or to_chain == "solana":
            return "fusion-cross-chain"

        # EVM cross-chain = use Fusion+ (1inch)
        if from_chain in ["ethereum", "arbitrum", "optimism", "base"] and to_chain in ["ethereum", "arbitrum", "optimism", "base"]:
            return "fusion-cross-chain"

        # Default fallback
        return "standard-bridge"

    def select_optimal_strategy(
        self,
        current_protocol: str,
        current_chain: str,
        current_apy: float,
        amount: float,
        risk_level: str,
        urgency: int,
        market_trend: str,
        available_strategies: List[Dict]
    ) -> Optional[Dict]:
        """
        Select optimal strategy using MeTTa reasoning

        Args:
            current_protocol: Current protocol name
            current_chain: Current chain
            current_apy: Current APY
            amount: Amount to move (USD)
            risk_level: Risk level from assessment
            urgency: Urgency score (0-10) or string ('low', 'medium', 'high')
            market_trend: Market trend (crash, declining, stable, rising)
            available_strategies: List of available target protocols

        Returns:
            Optimal strategy with reasoning
        """
        # Convert string urgency to integer (0-10 scale)
        if isinstance(urgency, str):
            urgency_map = {'low': 3, 'medium': 6, 'high': 9}
            urgency = urgency_map.get(urgency.lower(), 6)

        best_strategy = None
        best_score = 0

        for target in available_strategies:
            # Calculate profitability
            profitability = self.calculate_profitability(
                amount,
                current_apy,
                target['apy'],
                target.get('execution_cost', 50.0)
            )

            if not profitability['is_profitable']:
                continue

            # Score this strategy
            score = self.score_strategy(
                profitability['apy_improvement'],
                profitability['break_even_months'],
                urgency,
                amount
            )

            # Select execution method
            execution_method = self.select_execution_method(
                current_chain,
                target['chain'],
                amount,
                urgency
            )

            strategy = {
                "source_protocol": current_protocol,
                "source_chain": current_chain,
                "target_protocol": target['protocol'],
                "target_chain": target['chain'],
                # Include target asset
                "target_token": target.get('token', 'USDC'),
                "current_apy": current_apy,
                "target_apy": target['apy'],
                "apy_improvement": profitability['apy_improvement'],
                "annual_profit": profitability['annual_profit'],
                "execution_cost": target.get('execution_cost', 50.0),
                "break_even_months": profitability['break_even_months'],
                "strategy_score": score,
                "execution_method": execution_method,
                "is_profitable": True,
                "confidence": min(100, score)
            }

            if score > best_score:
                best_score = score
                best_strategy = strategy

        if best_strategy:
            logger.success(
                f"🧠 MeTTa selected strategy: {best_strategy['target_protocol']} (score: {best_score:.1f}/100)")
            best_strategy["reasoning"] = (
                f"Selected {best_strategy['target_protocol']} on {best_strategy['target_chain']} "
                f"for +{best_strategy['apy_improvement']:.2f}% APY improvement. "
                f"Break-even in {best_strategy['break_even_months']:.1f} months. "
                f"Confidence: {best_strategy['confidence']:.0f}%"
            )
        else:
            logger.warning("🧠 MeTTa found no profitable strategy")

        return best_strategy

    # ═══════════════════════════════════════════════════════
    # LEARNING & ADAPTATION
    # ═══════════════════════════════════════════════════════

    def learn_from_execution(
        self,
        strategy: Dict,
        success: bool,
        actual_profit: float,
        execution_time: int
    ):
        """
        Learn from strategy execution for adaptive improvement

        This enables the system to improve over time
        """
        logger.info(
            f"🧠 Learning from execution: {'✅ success' if success else '❌ failed'}")

        # In a full implementation, this would:
        # 1. Store outcome in knowledge base
        # 2. Update MeTTa rules based on patterns
        # 3. Adjust scoring algorithms
        # 4. Improve future predictions

        # For now, just log
        logger.debug(f"   Strategy: {strategy.get('target_protocol')}")
        logger.debug(
            f"   Predicted profit: ${strategy.get('annual_profit', 0):.2f}/year")
        logger.debug(f"   Actual profit: ${actual_profit:.2f}")
        logger.debug(f"   Execution time: {execution_time}s")


# Singleton instance
_metta_reasoner = None


def get_metta_reasoner() -> MeTTaReasoner:
    """Get singleton instance of MeTTa reasoner"""
    global _metta_reasoner
    if _metta_reasoner is None:
        _metta_reasoner = MeTTaReasoner()
    return _metta_reasoner


# Test function
async def test_metta_reasoning():
    """Test MeTTa reasoning capabilities"""
    logger.info("Testing MeTTa reasoning engine...")

    reasoner = get_metta_reasoner()

    # Test 1: Risk Assessment
    logger.info("\n🧪 Test 1: Risk Assessment")
    risk_result = reasoner.assess_risk(
        collateral=100000,  # $100k
        debt=60000,         # $60k
        health_factor=1.35,
        volatility=5.0,
        market_trend="declining"
    )
    logger.info(f"   Risk Level: {risk_result['risk_level']}")
    logger.info(f"   Scenario: {risk_result['scenario']}")
    logger.info(
        f"   Liquidation Probability: {risk_result['liquidation_probability']:.1f}%")
    logger.info(f"   Urgency: {risk_result['urgency_score']}/10")
    logger.info(f"   Priority: {risk_result['execution_priority']}")
    logger.info(f"   Actions: {', '.join(risk_result['recommended_actions'])}")

    # Test 2: Strategy Selection
    logger.info("\n🧪 Test 2: Strategy Selection")
    available_strategies = [
        {"protocol": "kamino", "chain": "solana",
            "apy": 9.1, "execution_cost": 65.0},
        {"protocol": "morpho", "chain": "ethereum",
            "apy": 6.5, "execution_cost": 50.0},
        {"protocol": "drift", "chain": "solana",
            "apy": 8.3, "execution_cost": 60.0},
    ]

    strategy = reasoner.select_optimal_strategy(
        current_protocol="aave",
        current_chain="ethereum",
        current_apy=5.2,
        amount=100000,
        risk_level="high",
        urgency=7,
        market_trend="declining",
        available_strategies=available_strategies
    )

    if strategy:
        logger.info(
            f"   Selected: {strategy['target_protocol']} ({strategy['target_chain']})")
        logger.info(f"   APY Improvement: +{strategy['apy_improvement']:.2f}%")
        logger.info(f"   Annual Profit: ${strategy['annual_profit']:.2f}")
        logger.info(
            f"   Break-even: {strategy['break_even_months']:.1f} months")
        logger.info(f"   Score: {strategy['strategy_score']:.1f}/100")
        logger.info(f"   Method: {strategy['execution_method']}")
        logger.info(f"   Reasoning: {strategy['reasoning']}")
    else:
        logger.warning("   No profitable strategy found")

    logger.success("\n✅ MeTTa reasoning tests complete!")


if __name__ == "__main__":
    import asyncio

    # Setup logging
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )

    # Run tests
    asyncio.run(test_metta_reasoning())
