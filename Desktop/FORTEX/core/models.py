from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RequestMetadata(BaseModel):
    """Metadata for a captured request"""
    url: str
    method: str
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class CapturedRequest(RequestMetadata):
    """A full request captured from traffic"""
    request_id: str

class ExecutionMetadata(BaseModel):
    """Metadata about the execution environment"""
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

class ResponseData(BaseModel):
    """Captured response data"""
    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    error: Optional[str] = None

class ExecutionResult(BaseModel):
    """Result of replaying a request"""
    request_id: str
    scenario_name: str
    status: str  # SUCCESS, FAILURE, ERROR
    response: Optional[ResponseData] = None
    metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)

class ChaosScenario(BaseModel):
    """Definition of a chaos scenario"""
    name: str
    description: str
    mutation_type: str  # e.g., "race_condition", "retry_storm"
    parameters: Dict[str, Any] = Field(default_factory=dict)

class CrashSnapshot(BaseModel):
    """Snapshot of a system failure"""
    id: str
    scenario: ChaosScenario
    requests: List[CapturedRequest]
    results: List[ExecutionResult]
    timestamp: datetime = Field(default_factory=datetime.now)
    analysis: Optional[str] = None
