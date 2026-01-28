import httpx
import asyncio
from typing import List, Optional
from core.models import CapturedRequest, ExecutionResult, ResponseData, ExecutionMetadata
from datetime import datetime

class Replayer:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def execute(self, request: CapturedRequest, scenario_name: str = "baseline") -> ExecutionResult:
        """
        Replay a single captured request.
        """
        start_time = datetime.now()
        
        try:
            # Prepare arguments
            kwargs = {
                "method": request.method,
                "url": request.url,
                "headers": request.headers,
            }
            
            # Handle skipping auto-calculated headers if needed, to be faithful
            # But httpx handles content-length usually.
            
            if request.body:
                # Basic handling, assuming string or dict. 
                # Real implementation needs to handle form-data, json, bytes.
                # For now, pass as content if string, else json
                if isinstance(request.body, str):
                    kwargs["content"] = request.body
                elif isinstance(request.body, dict):
                    kwargs["json"] = request.body
            
            response = await self.client.request(**kwargs)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            result = ExecutionResult(
                request_id=request.request_id,
                scenario_name=scenario_name,
                status="SUCCESS" if response.status_code < 500 else "FAILURE",
                response=ResponseData(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.text,
                ),
                metadata=ExecutionMetadata(
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration
                )
            )
            return result

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() * 1000
            
            return ExecutionResult(
                request_id=request.request_id,
                scenario_name=scenario_name,
                status="ERROR",
                response=ResponseData(
                    status_code=0,
                    error=str(e)
                ),
                metadata=ExecutionMetadata(
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration
                )
            )

    async def execute_batch(self, requests: List[CapturedRequest], parallelism: int = 5) -> List[ExecutionResult]:
        """
        Execute a batch of requests with limited parallelism.
        """
        semaphore = asyncio.Semaphore(parallelism)
        
        async def _sem_exec(req):
            async with semaphore:
                return await self.execute(req)
        
        tasks = [_sem_exec(req) for req in requests]
        return await asyncio.gather(*tasks)
