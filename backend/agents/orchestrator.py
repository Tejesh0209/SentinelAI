# backend/agents/orchestrator.py
import logging
from typing import Dict, Any, Optional, AsyncIterator
from mcp_protocol import MCPRequest, AgentState, ToolRegistry
from .reasoning import ReasoningAgent
from .executor import ConcurrentToolExecutor

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    High-level orchestrator that manages the complete agent workflow:
    1. Receive user query
    2. Agent reasons about what to do
    3. Execute tools (parallel or sequential)
    4. Synthesize results
    5. Return response
    """
    
    def __init__(
        self,
        reasoning_agent: ReasoningAgent,
        tool_registry: ToolRegistry,
        max_iterations: int = 3
    ):
        self.agent = reasoning_agent
        self.registry = tool_registry
        self.executor = ConcurrentToolExecutor(tool_registry)
        self.max_iterations = max_iterations
        logger.info("Agent orchestrator initialized")
    
    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user query end-to-end
        
        Args:
            query: User's question/request
            context: Additional context (image_data, etc.)
            stream: Whether to stream intermediate results
            
        Returns:
            Complete response with reasoning, tool results, and final answer
        """
        context = context or {}
        state = AgentState(iteration=0, context=context)
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Step 1: Agent decides what to do
            mcp_request = MCPRequest(
                query=query,
                context=context,
                available_tools=self.registry.list_tools(),
                max_iterations=self.max_iterations,
                stream=stream
            )
            
            logger.info("Step 1: Agent reasoning...")
            agent_response = await self.agent.reason(mcp_request)
            
            # If no tools needed, return direct response
            if not agent_response.tool_calls:
                logger.info("No tools needed, returning direct response")
                return {
                    "reasoning": agent_response.reasoning,
                    "tool_calls": [],
                    "tool_results": {},
                    "response": agent_response.response,
                    "execution_time": 0.0
                }
            
            # Step 2: Execute tools
            logger.info(f"Step 2: Executing {len(agent_response.tool_calls)} tools...")
            tool_results = await self.executor.execute_all(
                agent_response.tool_calls,
                context
            )
            
            # Step 3: Synthesize results
            logger.info("Step 3: Synthesizing results...")
            
            # Convert ToolResult objects to simple dict for synthesis
            simple_results = {
                name: result.result if result.error is None else f"Error: {result.error}"
                for name, result in tool_results.items()
            }
            
            final_response = await self.agent.synthesize_results(
                original_query=query,
                tool_results=simple_results,
                reasoning=agent_response.reasoning
            )
            
            # Calculate total execution time
            total_execution_time = sum(
                result.execution_time 
                for result in tool_results.values()
            )
            
            logger.info(f"Query processed successfully in {total_execution_time:.2f}s")
            
            return {
                "reasoning": agent_response.reasoning,
                "tool_calls": [
                    {
                        "tool_name": tc.tool_name,
                        "arguments": tc.arguments
                    }
                    for tc in agent_response.tool_calls
                ],
                "tool_results": {
                    name: {
                        "result": result.result,
                        "error": result.error,
                        "execution_time": result.execution_time
                    }
                    for name, result in tool_results.items()
                },
                "response": final_response,
                "execution_time": total_execution_time
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return {
                "reasoning": "",
                "tool_calls": [],
                "tool_results": {},
                "response": f"I encountered an error: {str(e)}",
                "execution_time": 0.0,
                "error": str(e)
            }
    
    async def process_query_stream(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process query with streaming updates
        
        Yields:
            Status updates as they happen
        """
        context = context or {}
        
        # Yield initial status
        yield {
            "type": "status",
            "message": "Agent is thinking...",
            "stage": "reasoning"
        }
        
        # Step 1: Reasoning
        mcp_request = MCPRequest(
            query=query,
            context=context,
            available_tools=self.registry.list_tools(),
            stream=True
        )
        
        agent_response = await self.agent.reason(mcp_request)
        
        yield {
            "type": "reasoning",
            "data": {
                "reasoning": agent_response.reasoning,
                "tool_calls": [tc.dict() for tc in agent_response.tool_calls],
                "response": agent_response.response
            },
            "stage": "reasoning_complete"
        }
        
        # If no tools needed
        if not agent_response.tool_calls:
            yield {
                "type": "final_response",
                "data": {
                    "response": agent_response.response
                },
                "stage": "complete"
            }
            return
        
        # Step 2: Execute tools
        yield {
            "type": "status",
            "message": f"Executing {len(agent_response.tool_calls)} tools...",
            "stage": "executing_tools"
        }
        
        tool_results = await self.executor.execute_all(
            agent_response.tool_calls,
            context
        )
        
        yield {
            "type": "tool_results",
            "data": {
                name: {
                    "result": str(result.result)[:200] if result.result else None,  # Truncate for streaming
                    "error": result.error,
                    "execution_time": result.execution_time
                }
                for name, result in tool_results.items()
            },
            "stage": "tools_complete"
        }
        
        # Step 3: Synthesize
        yield {
            "type": "status",
            "message": "Synthesizing results...",
            "stage": "synthesizing"
        }
        
        simple_results = {
            name: result.result if result.error is None else f"Error: {result.error}"
            for name, result in tool_results.items()
        }
        
        final_response = await self.agent.synthesize_results(
            original_query=query,
            tool_results=simple_results,
            reasoning=agent_response.reasoning
        )
        
        yield {
            "type": "final_response",
            "data": {
                "response": final_response
            },
            "stage": "complete"
        }
    
    async def multi_turn_conversation(
        self,
        query: str,
        conversation_history: list,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle multi-turn conversations with memory
        
        Args:
            query: Current query
            conversation_history: Previous Q&A pairs
            context: Additional context
            
        Returns:
            Response considering conversation history
        """
        # Build enhanced query with history
        enhanced_query = query
        if conversation_history:
            history_text = "\n".join([
                f"User: {turn['query']}\nAssistant: {turn['response']}"
                for turn in conversation_history[-3:]  # Last 3 turns
            ])
            enhanced_query = f"""Previous conversation:
{history_text}

Current query: {query}"""
        
        return await self.process_query(enhanced_query, context)