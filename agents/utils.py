from typing import List, Dict, Any, Optional
from uagents_core.registration import AgentRegistrationPolicy
from uagents_core.types import AgentEndpoint
from uagents_core.identity import Identity

class NoOpRegistrationPolicy(AgentRegistrationPolicy):
    """
    A registration policy that does nothing.
    Useful for local development or when almanac registration is failing/not needed.
    """
    async def register(
        self,
        agent_identifier: str,
        identity: Identity,
        protocols: List[str],
        endpoints: List[AgentEndpoint],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        # Do nothing - bypass registration
        pass
