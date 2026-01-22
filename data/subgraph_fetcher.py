"""
LiqX Subgraph Data Fetcher
Queries The Graph for Aave V3 position data on Ethereum Mainnet
"""

import os
import aiohttp
from typing import Dict, List, Optional
from loguru import logger

SUBGRAPH_URL = os.getenv(
    "LIQX_SUBGRAPH_URL", "https://api.studio.thegraph.com/query/1723368/cashew-subgraph/version/latest")


class SubgraphFetcher:
    """Fetches position data from The Graph subgraph"""

    def __init__(self):
        self.url = SUBGRAPH_URL
        logger.info(f"SubgraphFetcher initialized with URL: {self.url}")

    async def _query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against the subgraph"""
        try:
            # Create SSL context that doesn't verify certificates (for development)
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {"query": query}
                if variables:
                    payload["variables"] = variables

                async with session.post(self.url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(
                            f"Subgraph query failed with status {response.status}")
                        return {}

                    data = await response.json()

                    if "errors" in data:
                        logger.error(f"GraphQL errors: {data['errors']}")
                        return {}

                    return data.get("data", {})

        except Exception as e:
            logger.error(f"Subgraph query error: {e}")
            return {}

    async def get_risky_positions(
        self,
        health_factor_threshold: float = 1.5,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get all active positions below a certain health factor

        Args:
            health_factor_threshold: Maximum health factor to include
            limit: Maximum number of positions to return

        Returns:
            List of position dictionaries
        """
        query = """
        query GetRiskyPositions($threshold: BigDecimal!, $limit: Int!) {
            positions(
                where: { healthFactor_lt: $threshold }
                orderBy: healthFactor
                orderDirection: asc
                first: $limit
            ) {
                id
                user {
                    id
                    liquidationCount
                }
                collateralAsset
                collateralAmount
                debtAsset
                debtAmount
                healthFactor
                createdAt
                updatedAt
            }
        }
        """

        variables = {
            "threshold": str(health_factor_threshold),
            "limit": limit
        }

        data = await self._query(query, variables)
        positions = data.get("positions", [])

        logger.info(
            f"Found {len(positions)} risky positions (HF < {health_factor_threshold})")
        return positions

    async def get_user_position(self, user_address: str) -> Optional[Dict]:
        """
        Get a specific user's positions and stats

        Args:
            user_address: Ethereum address of the user

        Returns:
            User data dictionary or None if not found
        """
        query = """
        query GetUserPosition($userId: ID!) {
            user(id: $userId) {
                id
                totalSupplied
                totalBorrowed
                liquidationCount
                lastUpdated
                positions {
                    id
                    collateralAsset
                    collateralAmount
                    debtAsset
                    debtAmount
                    healthFactor
                    createdAt
                    updatedAt
                }
            }
        }
        """

        variables = {"userId": user_address.lower()}

        data = await self._query(query, variables)
        user = data.get("user")

        if user:
            logger.info(
                f"Found user {user_address} with {len(user.get('positions', []))} active positions")
        else:
            logger.warning(f"User {user_address} not found in subgraph")

        return user

    async def get_recent_liquidations(self, limit: int = 20) -> List[Dict]:
        """
        Get recent liquidation events

        Args:
            limit: Maximum number of liquidations to return

        Returns:
            List of liquidation dictionaries
        """
        query = """
        query GetRecentLiquidations($limit: Int!) {
            liquidations(
                first: $limit
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                position {
                    id
                    user {
                        id
                    }
                }
                collateralAsset
                debtAsset
                debtToCover
                liquidatedCollateralAmount
                liquidator
                timestamp
                txHash
            }
        }
        """

        variables = {"limit": limit}

        data = await self._query(query, variables)
        liquidations = data.get("liquidations", [])

        logger.info(f"Found {len(liquidations)} recent liquidations")
        return liquidations

    async def get_protocol_stats(self) -> Optional[Dict]:
        """
        Get overall protocol statistics

        Returns:
            Protocol stats dictionary or None
        """
        query = """
        query GetProtocolStats {
            protocol(id: "1") {
                id
                totalValueLocked
                totalBorrowed
                totalLiquidations
                lastUpdated
            }
        }
        """

        data = await self._query(query)
        protocol = data.get("protocol")

        if protocol:
            logger.info(
                f"Protocol TVL: {protocol.get('totalValueLocked')}, Liquidations: {protocol.get('totalLiquidations')}")

        return protocol

    async def get_positions_by_asset(
        self,
        asset_address: str,
        is_collateral: bool = True,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get positions using a specific asset as collateral or debt

        Args:
            asset_address: Token contract address
            is_collateral: True to search collateral, False for debt
            limit: Maximum number of positions to return

        Returns:
            List of position dictionaries
        """
        field = "collateralAsset" if is_collateral else "debtAsset"

        query = f"""
        query GetPositionsByAsset($asset: String!, $limit: Int!) {{
            positions(
                where: {{ {field}: $asset }}
                orderBy: healthFactor
                orderDirection: asc
                first: $limit
            ) {{
                id
                user {{
                    id
                }}
                collateralAsset
                collateralAmount
                debtAsset
                debtAmount
                healthFactor
                updatedAt
            }}
        }}
        """

        variables = {
            "asset": asset_address.lower(),
            "limit": limit
        }

        data = await self._query(query, variables)
        positions = data.get("positions", [])

        asset_type = "collateral" if is_collateral else "debt"
        logger.info(
            f"Found {len(positions)} positions using {asset_address} as {asset_type}")
        return positions

    async def get_critical_positions(self, limit: int = 50) -> List[Dict]:
        """
        Get positions in critical danger (HF < 1.3)

        Args:
            limit: Maximum number of positions to return

        Returns:
            List of critical position dictionaries
        """
        critical_threshold = float(os.getenv("CRITICAL_HEALTH_FACTOR", "1.3"))
        return await self.get_risky_positions(critical_threshold, limit)

    async def get_user_liquidation_history(self, user_address: str) -> List[Dict]:
        """
        Get all liquidations for a specific user

        Args:
            user_address: Ethereum address of the user

        Returns:
            List of liquidation dictionaries
        """
        query = """
        query GetUserLiquidations($userId: ID!) {
            liquidations(
                where: { position_: { user: $userId } }
                orderBy: timestamp
                orderDirection: desc
            ) {
                id
                collateralAsset
                debtAsset
                debtToCover
                liquidatedCollateralAmount
                liquidator
                timestamp
                txHash
            }
        }
        """

        variables = {"userId": user_address.lower()}

        data = await self._query(query, variables)
        liquidations = data.get("liquidations", [])

        logger.info(
            f"User {user_address} has {len(liquidations)} liquidations")
        return liquidations


# Singleton instance
_fetcher = None


def get_subgraph_fetcher() -> SubgraphFetcher:
    """Get or create the subgraph fetcher singleton"""
    global _fetcher
    if _fetcher is None:
        _fetcher = SubgraphFetcher()
    return _fetcher


# Quick test function
async def test_subgraph():
    """Test subgraph queries"""
    fetcher = get_subgraph_fetcher()

    logger.info("Testing subgraph connection...")

    # Test 1: Get risky positions
    risky = await fetcher.get_risky_positions(health_factor_threshold=2.0, limit=5)
    logger.info(f"Test 1 - Risky positions: {len(risky)} found")

    # Test 2: Get recent liquidations
    liquidations = await fetcher.get_recent_liquidations(limit=5)
    logger.info(f"Test 2 - Recent liquidations: {len(liquidations)} found")

    # Test 3: Get protocol stats
    stats = await fetcher.get_protocol_stats()
    logger.info(f"Test 3 - Protocol stats: {stats}")

    logger.info("✅ Subgraph tests complete!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_subgraph())
