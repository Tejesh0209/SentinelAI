# backend/mcp_protocol/registry.py
from typing import Dict, Callable, List, Optional
from .schema import Tool, ToolParameter
import inspect
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.metadata: Dict[str, Tool] = {}
        logger.info("Tool registry initialized")
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: List[ToolParameter],
        category: str = "general"
    ) -> None:
        """
        Register a new tool
        
        Args:
            name: Unique tool identifier
            handler: Async function to execute
            description: What the tool does
            parameters: List of parameters
            category: Tool category (vision, voice, data, etc.)
        """
        # Validate handler is async
        if not inspect.iscoroutinefunction(handler):
            raise ValueError(f"Handler for {name} must be async function")
        
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            category=category
        )
        
        self.tools[name] = handler
        self.metadata[name] = tool
        
        logger.info(f"Registered tool: {name} (category: {category})")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool handler by name"""
        return self.tools.get(name)
    
    def get_metadata(self, name: str) -> Optional[Tool]:
        """Get tool metadata"""
        return self.metadata.get(name)
    
    def list_tools(self, category: Optional[str] = None) -> List[Tool]:
        """
        List all registered tools
        
        Args:
            category: Filter by category (optional)
        """
        tools = list(self.metadata.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    def get_tools_for_prompt(self) -> str:
        """Format tools for LLM prompt"""
        tool_descriptions = []
        
        for tool in self.metadata.values():
            params = ", ".join([
                f"{p.name}: {p.type.value}" 
                for p in tool.parameters
            ])
            tool_descriptions.append(
                f"- {tool.name}({params}): {tool.description}"
            )
        
        return "\n".join(tool_descriptions)
    
    def unregister(self, name: str) -> bool:
        """Remove a tool from registry"""
        if name in self.tools:
            del self.tools[name]
            del self.metadata[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def __len__(self) -> int:
        return len(self.tools)
    
    def __contains__(self, name: str) -> bool:
        return name in self.tools