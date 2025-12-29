# backend/mcp_protocol/schema.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class ToolParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"

class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str
    type: ToolParameterType
    description: str
    required: bool = False
    default: Optional[Any] = None

class Tool(BaseModel):
    """Tool that the agent can use"""
    name: str
    description: str
    parameters: List[ToolParameter]
    category: str = "general"  # general, vision, voice, data
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                p.name: {
                    "type": p.type.value,
                    "description": p.description,
                    "required": p.required
                }
                for p in self.parameters
            }
        }

class ToolCall(BaseModel):
    """Request to execute a tool"""
    tool_name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None

class ToolResult(BaseModel):
    """Result from tool execution"""
    tool_name: str
    result: Any
    error: Optional[str] = None
    execution_time: float = 0.0

class MCPRequest(BaseModel):
    """Request sent to agent"""
    query: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    available_tools: List[Tool]
    max_iterations: int = 3
    stream: bool = False

class MCPResponse(BaseModel):
    """Response from agent"""
    reasoning: str
    tool_calls: List[ToolCall]
    response: str
    confidence: float = 1.0
    
class AgentState(BaseModel):
    """Current state of agent execution"""
    iteration: int = 0
    completed_tools: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False