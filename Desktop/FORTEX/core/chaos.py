import asyncio
from typing import List
from core.models import CapturedRequest, ExecutionResult, ChaosScenario
from core.replay import Replayer

class ChaosEngine:
    def __init__(self, replayer: Replayer):
        self.replayer = replayer

    async def execute_scenario(self, scenario: str, request: CapturedRequest) -> List[ExecutionResult]:
        if scenario == "double_submit":
            return await self._double_submit(request)
        elif scenario == "race_condition":
            return await self._race_condition(request)
        else:
            return []

    async def _double_submit(self, request: CapturedRequest) -> List[ExecutionResult]:
        """Fire the same request twice immediately."""
        tasks = [
            self.replayer.execute(request, scenario_name="double_submit_1"),
            self.replayer.execute(request, scenario_name="double_submit_2")
        ]
        return await asyncio.gather(*tasks)

    async def _race_condition(self, request: CapturedRequest, concurrency: int = 10) -> List[ExecutionResult]:
        """Fire N requests in parallel to trigger race conditions."""
        tasks = []
        for i in range(concurrency):
            tasks.append(self.replayer.execute(request, scenario_name=f"race_run_{i}"))
        return await asyncio.gather(*tasks)
