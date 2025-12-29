# backend/main.py (COMPLETE VERSION)
from fastapi import FastAPI, WebSocket, UploadFile, File, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import base64
import logging
import json
import os

from config import settings
from services.vision import VisionService
from services.voice import VoiceService
from services.rag import RAGService
from mcp_protocol import ToolRegistry, ToolParameter, ToolParameterType

from agents.reasoning import ReasoningAgent
from agents.orchestrator import AgentOrchestrator
from realtime.voice_Stream import VoiceStreamHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="SentinelAI",
    description="Real-Time Multimodal Autonomous Intelligence Agent",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
logger.info("Initializing services...")
vision_service = VisionService(settings.OPENAI_API_KEY)
voice_service = VoiceService(settings.OPENAI_API_KEY)
rag_service = RAGService(settings.OPENAI_API_KEY, settings.VECTOR_DB_PATH)

# Initialize agent system
logger.info("Initializing agent system...")
reasoning_agent = ReasoningAgent(settings.OPENAI_API_KEY)
registry = ToolRegistry()

# ==================== REGISTER TOOLS ====================

# Vision tools
async def analyze_image_tool(image_data: str, prompt: str = "Describe this image"):
    return await vision_service.analyze_image(image_data, prompt)

registry.register(
    name="analyze_image",
    handler=analyze_image_tool,
    description="Analyze an image and extract information, detect objects, or answer questions about visual content",
    parameters=[
        ToolParameter(name="image_data", type=ToolParameterType.STRING, description="Base64 encoded image", required=True),
        ToolParameter(name="prompt", type=ToolParameterType.STRING, description="Analysis instruction", required=False, default="Describe this image")
    ],
    category="vision"
)

async def extract_text_tool(image_data: str):
    return await vision_service.extract_text(image_data)

registry.register(
    name="extract_text",
    handler=extract_text_tool,
    description="Extract and OCR all text visible in an image",
    parameters=[ToolParameter(name="image_data", type=ToolParameterType.STRING, description="Base64 encoded image", required=True)],
    category="vision"
)

# Knowledge tools
async def search_knowledge_tool(query: str, k: int = 3):
    results = await rag_service.search(query, k)
    if not results:
        return "No relevant documents found in knowledge base."
    return "\n\n".join([f"[Document {i+1}] {r['text']}" for i, r in enumerate(results)])

registry.register(
    name="search_knowledge",
    handler=search_knowledge_tool,
    description="Search internal knowledge base for documentation, procedures, or previously stored information",
    parameters=[
        ToolParameter(name="query", type=ToolParameterType.STRING, description="Search query", required=True),
        ToolParameter(name="k", type=ToolParameterType.INTEGER, description="Number of results", required=False, default=3)
    ],
    category="data"
)

# Voice tools
async def transcribe_audio_tool(audio_data: bytes):
    return await voice_service.transcribe(audio_data)

registry.register(
    name="transcribe_audio",
    handler=transcribe_audio_tool,
    description="Convert speech to text from audio data",
    parameters=[ToolParameter(name="audio_data", type=ToolParameterType.STRING, description="Audio bytes", required=True)],
    category="voice"
)

# Weather tool
async def get_weather_tool(city: str, country_code: str = "US"):
    # Mock weather data since we're using OpenAI-only
    return f"Weather in {city}: Currently unavailable (OpenAI-only mode). Recommend checking weather.com"

registry.register(
    name="get_weather",
    handler=get_weather_tool,
    description="Get current weather conditions for a city",
    parameters=[
        ToolParameter(name="city", type=ToolParameterType.STRING, description="City name", required=True),
        ToolParameter(name="country_code", type=ToolParameterType.STRING, description="ISO country code", required=False, default="US")
    ],
    category="live_data"
)

# Stock price tool
async def get_stock_price_tool(symbol: str):
    # Mock stock data since we're using OpenAI-only
    return f"{symbol}: Price currently unavailable (OpenAI-only mode). Recommend checking a financial website"

registry.register(
    name="get_stock_price",
    handler=get_stock_price_tool,
    description="Get current stock price and change for a ticker symbol",
    parameters=[ToolParameter(name="symbol", type=ToolParameterType.STRING, description="Stock ticker (e.g., AAPL, GOOGL)", required=True)],
    category="live_data"
)

# Crypto price tool
async def get_crypto_price_tool(symbol: str):
    # Mock crypto data since we're using OpenAI-only
    return f"{symbol}: Price currently unavailable (OpenAI-only mode). Recommend checking a crypto exchange"

registry.register(
    name="get_crypto_price",
    handler=get_crypto_price_tool,
    description="Get current cryptocurrency price",
    parameters=[ToolParameter(name="symbol", type=ToolParameterType.STRING, description="Crypto symbol (e.g., BTC, ETH)", required=True)],
    category="live_data"
)

# News tool
async def get_news_tool(query: str, limit: int = 5):
    # Mock news data since we're using OpenAI-only
    return f"News about '{query}': Currently unavailable (OpenAI-only mode). Recommend checking news websites"

registry.register(
    name="get_news",
    handler=get_news_tool,
    description="Get latest news articles about a topic",
    parameters=[
        ToolParameter(name="query", type=ToolParameterType.STRING, description="News search query", required=True),
        ToolParameter(name="limit", type=ToolParameterType.INTEGER, description="Number of articles", required=False, default=5)
    ],
    category="live_data"
)

# Web search tool
async def web_search_tool(query: str, limit: int = 5):
    # Mock search data since we're using OpenAI-only
    return f"Search results for '{query}': Currently unavailable (OpenAI-only mode). Recommend using Google search"

registry.register(
    name="web_search",
    handler=web_search_tool,
    description="Search the web for information",
    parameters=[
        ToolParameter(name="query", type=ToolParameterType.STRING, description="Search query", required=True),
        ToolParameter(name="limit", type=ToolParameterType.INTEGER, description="Number of results", required=False, default=5)
    ],
    category="live_data"
)

# Initialize orchestrator
orchestrator = AgentOrchestrator(reasoning_agent, registry, max_iterations=3)

logger.info(f"✅ Registered {len(registry)} tools across {len(set(t.category for t in registry.list_tools()))} categories")

# ==================== ROUTES ====================

@app.get("/")
async def root():
    return {
        "name": "SentinelAI",
        "version": "1.0.0",
        "status": "running",
        "features": ["voice", "vision", "screen_capture", "live_data", "rag"],
        "tools": len(registry)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "vision": "ready",
            "voice": "ready",
            "rag": "ready",
            "live_data": "ready",
            "agent": "ready"
        },
        "tools": len(registry),
        "documents_indexed": len(rag_service)
    }

@app.get("/tools")
async def list_tools():
    tools_by_category = {}
    for tool in registry.list_tools():
        if tool.category not in tools_by_category:
            tools_by_category[tool.category] = []
        tools_by_category[tool.category].append(tool.dict())
    
    return {
        "total": len(registry),
        "categories": list(tools_by_category.keys()),
        "tools_by_category": tools_by_category
    }

@app.post("/query")
async def process_query(query: str, context: dict = None):
    try:
        result = await orchestrator.process_query(query, context)
        return result
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(500, str(e))

@app.post("/knowledge/add")
async def add_knowledge(text: str, metadata: dict = None):
    try:
        doc_id = await rag_service.add_document(text, metadata)
        rag_service.save()
        return {"doc_id": doc_id, "message": "Document added"}
    except Exception as e:
        raise HTTPException(500, str(e))

# ==================== WEBSOCKET - UNIFIED ====================

@app.websocket("/ws/sentinel")
async def sentinel_websocket(websocket: WebSocket):
    """
    Unified WebSocket endpoint for:
    - Voice streaming
    - Agent queries
    - Real-time responses
    """
    await websocket.accept()
    logger.info("Client connected to SentinelAI")
    
    # Initialize voice handler
    voice_handler = VoiceStreamHandler(settings.OPENAI_API_KEY)
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            # Voice streaming
            if msg_type == "audio_chunk":
                transcript = await voice_handler.process_audio_chunk(
                    data["data"],
                    data.get("timestamp", 0)
                )
                
                if transcript:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript
                    })
                    
                    # Auto-process with agent
                    async for update in orchestrator.process_query_stream(transcript):
                        await websocket.send_json(update)
            
            # Screen capture (simplified)
            elif msg_type == "screen_frame":
                analysis = {
                    "analysis": "Screen analysis requires active connection",
                    "has_significant_change": False
                }
                await websocket.send_json({
                    "type": "screen_analysis",
                    "data": analysis
                })
            
            # Text query
            elif msg_type == "query":
                async for update in orchestrator.process_query_stream(
                    data["query"],
                    data.get("context", {})
                ):
                    await websocket.send_json(update)
            
            # Ping/pong
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Services closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)