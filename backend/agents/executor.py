# backend/agents/executor.py
import asyncio
import time
import logging
from typing import List, Dict, Any
from mcp_protocol import ToolCall, ToolResult, ToolRegistry

logger = logging.getLogger(__name__)

class ConcurrentToolExecutor:
    """
    Executes multiple tools in parallel when possible.
    Handles dependencies, timeouts, and error recovery.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.default_timeout = 30.0  # seconds
    
    async def execute_all(
        self,
        tool_calls: List[ToolCall],
        context: Dict[str, Any] = None
    ) -> Dict[str, ToolResult]:
        """
        Execute all tool calls concurrently
        
        Args:
            tool_calls: List of tools to execute
            context: Shared context (e.g., image_data from user)
            
        Returns:
            Dictionary mapping tool names to results
        """
        if not tool_calls:
            return {}
        
        context = context or {}
        
        logger.info(f"Executing {len(tool_calls)} tools concurrently")
        
        # Create tasks for each tool
        tasks = []
        tool_names = []
        
        for tool_call in tool_calls:
            # Inject context data into arguments if needed
            arguments = self._prepare_arguments(tool_call.arguments, context)
            
            task = self._execute_single_tool(
                tool_call.tool_name,
                arguments
            )
            tasks.append(task)
            tool_names.append(tool_call.tool_name)
        
        # Execute all in parallel
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        logger.info(f"All tools completed in {total_time:.2f}s")
        
        # Map results to tool names
        tool_results = {}
        for name, result in zip(tool_names, results):
            if isinstance(result, Exception):
                tool_results[name] = ToolResult(
                    tool_name=name,
                    result=None,
                    error=str(result),
                    execution_time=0.0
                )
            else:
                tool_results[name] = result
        
        return tool_results
    
    def _prepare_arguments(
        self,
        arguments: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare arguments by injecting context data
        
        For example, if tool needs "image_data" but it's not in arguments,
        check if it's in context and inject it.
        """
        prepared = arguments.copy()
        
        # Common context keys that tools might need
        context_keys = ["image_data", "audio_data", "transcript"]
        
        for key in context_keys:
            if key in context and key not in prepared:
                # Check if this key is needed (crude check - improve later)
                prepared[key] = context[key]
        
        return prepared
    
    async def _execute_single_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolResult:
        """Execute a single tool with timeout and error handling"""
        
        start_time = time.time()
        
        try:
            # Get tool handler
            handler = self.registry.get_tool(tool_name)
            
            if handler is None:
                raise ValueError(f"Tool '{tool_name}' not found in registry")
            
            logger.info(f"Executing tool: {tool_name}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                handler(**arguments),
                timeout=self.default_timeout
            )
            
            execution_time = time.time() - start_time
            
            logger.info(f"Tool {tool_name} completed in {execution_time:.2f}s")
            
            return ToolResult(
                tool_name=tool_name,
                result=result,
                error=None,
                execution_time=execution_time
            )
        
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution timed out after {self.default_timeout}s"
            logger.error(f"{tool_name}: {error_msg}")
            
            return ToolResult(
                tool_name=tool_name,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"{tool_name}: {error_msg}")
            
            return ToolResult(
                tool_name=tool_name,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )
    
    async def execute_sequential(
        self,
        tool_calls: List[ToolCall],
        context: Dict[str, Any] = None
    ) -> Dict[str, ToolResult]:
        """
        Execute tools sequentially (when order matters)
        Each tool can access results from previous tools
        """
        if not tool_calls:
            return {}
        
        context = context or {}
        results = {}
        
        logger.info(f"Executing {len(tool_calls)} tools sequentially")
        
        for tool_call in tool_calls:
            # Inject previous results into context
            execution_context = {**context, "previous_results": results}
            arguments = self._prepare_arguments(tool_call.arguments, execution_context)
            
            # Execute
            result = await self._execute_single_tool(tool_call.tool_name, arguments)
            results[tool_call.tool_name] = result
            
            # Stop if tool failed and it was critical
            if result.error:
                logger.warning(f"Sequential execution stopped due to error in {tool_call.tool_name}")
                break
        
        return results
    
    def analyze_dependencies(
        self,
        tool_calls: List[ToolCall]
    ) -> tuple[List[ToolCall], List[ToolCall]]:
        """
        Analyze which tools can run in parallel vs need sequential execution
        
        Returns:
            (parallel_tools, sequential_tools)
        """
        # Simple heuristic: if a tool's arguments reference another tool's name,
        # it has a dependency
        
        tool_names = {tc.tool_name for tc in tool_calls}
        dependent_tools = []
        independent_tools = []
        
        for tool_call in tool_calls:
            # Check if arguments reference other tool names
            args_str = str(tool_call.arguments).lower()
            has_dependency = any(
                name.lower() in args_str 
                for name in tool_names 
                if name != tool_call.tool_name
            )
            
            if has_dependency:
                dependent_tools.append(tool_call)
            else:
                independent_tools.append(tool_call)
        
        return independent_tools, dependent_tools