# backend/agents/reasoning.py
from openai import AsyncOpenAI
import json
import logging
from typing import List, Dict, Any, Optional
from mcp_protocol import (
    MCPRequest,
    MCPResponse,
    ToolCall,
    Tool,
    AgentState
)

logger = logging.getLogger(__name__)

class ReasoningAgent:
    """
    Autonomous agent that decides which tools to use based on user queries.
    Uses GPT-4 to reason about task decomposition and tool selection.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = 4096
        logger.info(f"Reasoning agent initialized with {model}")
    
    def _build_system_prompt(self, available_tools: List[Tool]) -> str:
        """Build system prompt with tool descriptions"""
        
        tools_desc = []
        for tool in available_tools:
            params = ", ".join([
                f"{p.name}: {p.type.value}" + 
                (f" (required)" if p.required else f" (optional, default: {p.default})")
                for p in tool.parameters
            ])
            tools_desc.append(
                f"• {tool.name}({params})\n  Category: {tool.category}\n  Description: {tool.description}"
            )
        
        tools_text = "\n\n".join(tools_desc)
        
        return f"""You are SentinelAI, an autonomous agent that can use tools to help users.

# YOUR ROLE
You are a reasoning engine that:
1. Understands user queries (text, voice transcripts, image descriptions)
2. Decides which tools to invoke and in what order
3. Synthesizes results into helpful responses

# AVAILABLE TOOLS
{tools_text}

# DECISION PROCESS
1. **Analyze the query**: What is the user asking for?
2. **Identify required tools**: Which tools are needed?
3. **Plan execution order**: Can tools run in parallel or must be sequential?
4. **Consider context**: Are there previous results to incorporate?

# RESPONSE FORMAT
You must respond with a JSON object:
{{
    "reasoning": "Explain your thought process and why you chose these tools",
    "tool_calls": [
        {{
            "tool_name": "exact_tool_name",
            "arguments": {{
                "param_name": "value"
            }}
        }}
    ],
    "response": "User-facing explanation of what you're doing"
}}

# IMPORTANT RULES
- If no tools are needed, return empty tool_calls array and provide direct response
- For image analysis queries, ALWAYS check if image_data is in context
- For voice queries, check if audio_data or transcript is available
- You can call multiple tools - they will execute in parallel when possible
- Keep reasoning concise but clear
- Make response conversational and helpful

# EXAMPLES

Example 1 - Simple query:
Query: "What's 2+2?"
Response: {{
    "reasoning": "This is a simple math question that doesn't require any tools.",
    "tool_calls": [],
    "response": "2 + 2 = 4"
}}

Example 2 - Image analysis:
Query: "What's in this image?"
Context: {{"image_data": "base64..."}}
Response: {{
    "reasoning": "User wants to analyze an image. I'll use the analyze_image tool.",
    "tool_calls": [
        {{
            "tool_name": "analyze_image",
            "arguments": {{
                "image_data": "base64...",
                "prompt": "Describe this image in detail"
            }}
        }}
    ],
    "response": "I'll analyze this image for you."
}}

Example 3 - Multi-tool query:
Query: "Analyze this dashboard and search for related metrics documentation"
Context: {{"image_data": "base64..."}}
Response: {{
    "reasoning": "This requires both image analysis and knowledge base search. I'll run both in parallel.",
    "tool_calls": [
        {{
            "tool_name": "analyze_image",
            "arguments": {{
                "image_data": "base64...",
                "prompt": "Describe the dashboard metrics and charts shown"
            }}
        }},
        {{
            "tool_name": "search_knowledge",
            "arguments": {{
                "query": "dashboard metrics documentation",
                "k": 3
            }}
        }}
    ],
    "response": "I'll analyze the dashboard and search our knowledge base for related documentation."
}}

Now respond to the user's query."""

    async def reason(
        self,
        request: MCPRequest
    ) -> MCPResponse:
        """
        Main reasoning method - decides what tools to use
        
        Args:
            request: User query with context and available tools
            
        Returns:
            Agent's decision on which tools to invoke
        """
        try:
            system_prompt = self._build_system_prompt(request.available_tools)
            
            # Build user message
            user_message = f"""Query: {request.query}"""
            
            if request.context:
                # Add context information (but not full binary data)
                context_summary = {}
                for key, value in request.context.items():
                    if key == "image_data" and value:
                        context_summary[key] = f"<base64_image_{len(value)}_chars>"
                    elif key == "audio_data" and value:
                        context_summary[key] = f"<audio_data_{len(value)}_bytes>"
                    else:
                        context_summary[key] = value
                
                user_message += f"\n\nContext: {json.dumps(context_summary, indent=2)}"
            
            logger.info(f"Agent reasoning on query: {request.query[:100]}...")
            
            # Call GPT-4
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            logger.debug(f"Raw agent response: {response_text}")
            
            # Extract JSON (handle markdown code blocks)
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Create response object
            mcp_response = MCPResponse(
                reasoning=result.get("reasoning", ""),
                tool_calls=[
                    ToolCall(
                        tool_name=tc["tool_name"],
                        arguments=tc["arguments"]
                    )
                    for tc in result.get("tool_calls", [])
                ],
                response=result.get("response", ""),
                confidence=1.0
            )
            
            logger.info(f"Agent decided to use {len(mcp_response.tool_calls)} tools")
            return mcp_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse agent response: {e}")
            logger.error(f"Response text: {response_text}")
            # Return fallback response
            return MCPResponse(
                reasoning="Failed to parse response",
                tool_calls=[],
                response="I had trouble understanding how to help with that. Could you rephrase?",
                confidence=0.0
            )
        except Exception as e:
            logger.error(f"Agent reasoning error: {e}")
            raise
    
    async def synthesize_results(
        self,
        original_query: str,
        tool_results: Dict[str, Any],
        reasoning: str
    ) -> str:
        """
        Synthesize tool results into final response
        
        Args:
            original_query: Original user query
            tool_results: Dictionary of tool_name -> result
            reasoning: Original reasoning
            
        Returns:
            Final synthesized response
        """
        try:
            # Build synthesis prompt
            results_text = json.dumps(tool_results, indent=2)
            
            synthesis_prompt = f"""# TASK
Synthesize the following tool results into a helpful, conversational response.

# ORIGINAL QUERY
{original_query}

# YOUR REASONING
{reasoning}

# TOOL RESULTS
{results_text}

# INSTRUCTIONS
- Provide a clear, direct answer to the user's query
- Incorporate relevant information from all tool results
- Be conversational and helpful
- If results are incomplete or conflicting, acknowledge it
- Keep response concise but complete
- Do NOT mention tool names or technical details unless relevant

Respond with just the synthesized answer, no JSON or formatting."""

            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": synthesis_prompt
                }]
            )
            
            final_response = response.choices[0].message.content.strip()
            logger.info("Results synthesized successfully")
            return final_response
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            # Fallback: just return tool results
            return f"Tool results: {json.dumps(tool_results, indent=2)}"