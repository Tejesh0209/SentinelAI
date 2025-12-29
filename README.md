# SentinelAI

Real-Time Multimodal Autonomous Intelligence Agent

SentinelAI is a production-grade autonomous AI agent that integrates vision, voice, knowledge retrieval, and live data streams into a single intelligent system. Unlike traditional chatbots, SentinelAI can see, listen, reason autonomously about which tools to use, and take actions—all in real-time.

## Key Features

### Autonomous Agent
- Intelligent Reasoning: Uses Claude Sonnet 4 to autonomously decide which tools to invoke
- Parallel Execution: Runs multiple tools concurrently for 60-70% faster response times
- Context-Aware: Maintains conversation history and synthesizes results from multiple sources

### Multimodal Input
- Vision: Image analysis, OCR, object detection using GPT-4 Vision
- Voice: Real-time speech-to-text with streaming audio chunks (Whisper)
- Screen Capture: Automatic screenshot analysis every 5 seconds with change detection
- Text: Natural language queries with full conversational context

### Extensible Tool System
Built on custom Model Context Protocol (MCP) with 10+ tools:

Vision Tools:
- analyze_image - Comprehensive image analysis
- extract_text - OCR from images

Data Tools:
- search_knowledge - RAG-powered knowledge base search
- get_weather - Current weather for any city
- get_stock_price - Real-time stock prices
- get_crypto_price - Cryptocurrency prices
- get_news - Latest news articles
- web_search - DuckDuckGo web search

Voice Tools:
- transcribe_audio - Speech-to-text conversion

### Real-Time Processing
- WebSocket Streaming: Bidirectional communication for instant updates
- Audio Buffering: 2-second chunks for low-latency transcription
- Frame Processing: Efficient screen capture with throttling
- Concurrent Execution: AsyncIO-based parallel tool invocation

## Table of Contents

- Architecture
- Installation
- Quick Start
- Usage Examples
- API Documentation
- Configuration
- Development
- Project Structure
- Testing
- Deployment
- Contributing
- License

## Architecture
```
Frontend (React)
  - Voice Input (MediaRecorder)
  - Screen Capture (getDisplayMedia)
  - Image Upload
  - Real-time Chat Interface
      |
      | WebSocket
      v
Backend (FastAPI)
  - Agent Orchestrator
    - Reasoning (Claude)
    - Executor (Parallel)
  - Tool Registry (MCP)
    - Vision Service (GPT-4V)
    - Voice Service (Whisper)
    - RAG Service (FAISS)
    - Live Data Service (External APIs)
      |
      v
External Services
  - OpenAI (GPT-4V, Whisper, Embeddings)
  - Anthropic (Claude Sonnet 4)
  - OpenWeatherMap, NewsAPI, Alpha Vantage, etc.
```

### Core Components

1. Agent Orchestrator (agents/orchestrator.py)
   - Manages end-to-end query processing
   - Coordinates reasoning, execution, synthesis

2. Reasoning Agent (agents/reasoning.py)
   - Analyzes queries and decides which tools to use
   - Powered by Claude Sonnet 4

3. Concurrent Executor (agents/executor.py)
   - Executes multiple tools in parallel
   - Handles timeouts and error recovery

4. Tool Registry (mcp_protocol/registry.py)
   - Custom MCP implementation
   - Dynamic tool discovery and invocation

5. Service Layer (services/)
   - Vision, Voice, RAG, Live Data services
   - Abstracts external API calls

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- API Keys:
  - OpenAI API key (required)
  - Anthropic API key (required)
  - Weather/News/Stock API keys (optional)

### Backend Setup
```bash
# Clone repository
git clone https://github.com/yourusername/sentinel-ai.git
cd sentinel-ai

# Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API keys
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Quick Start

### 1. Configure API Keys

Edit backend/.env:
```bash
# Required
OPENAI_API_KEY=sk-proj-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional (tools work without these, returning mock data)
WEATHER_API_KEY=your-openweathermap-key
NEWS_API_KEY=your-newsapi-key
ALPHA_VANTAGE_KEY=your-alphavantage-key
```

### 2. Start Backend
```bash
cd backend
python main.py
```

Backend runs at http://localhost:8000

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

Frontend runs at http://localhost:3000

### 4. Test the System
```bash
cd backend
python test_complete.py
```

## Usage Examples

### Text Queries
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Paris and the price of Bitcoin?"}'
```

Agent Decision:
- Recognizes need for 2 tools
- Executes get_weather and get_crypto_price in parallel
- Synthesizes results into natural response

### Image Analysis
```bash
curl -X POST http://localhost:8000/query/image \
  -F "query=What's in this dashboard?" \
  -F "file=@dashboard.png"
```

Agent Decision:
- Uses analyze_image to understand visual content
- May also use search_knowledge if related docs exist

### Voice Commands

1. Click microphone button in UI
2. Speak: "What's the latest news about artificial intelligence?"
3. Agent transcribes, processes, responds

### Screen Monitoring

1. Click monitor button
2. Grant screen share permission
3. Agent analyzes screen every 5 seconds
4. Alerts on significant changes

### Knowledge Base
```bash
# Add document
curl -X POST http://localhost:8000/knowledge/add \
  -H "Content-Type: application/json" \
  -d '{"text": "SentinelAI uses Claude for reasoning.", "metadata": {"source": "docs"}}'

# Query will now use this knowledge
curl -X POST http://localhost:8000/query \
  -d '{"query": "How does SentinelAI make decisions?"}'
```

## API Documentation

### REST Endpoints

#### GET /

Health check and version info

#### GET /health

Detailed service status

#### GET /tools

List all available tools by category

#### POST /query

Process a text query with agent

Request:
```json
{
  "query": "What's the weather in Tokyo?",
  "context": {}
}
```

Response:
```json
{
  "reasoning": "User wants weather, I'll use get_weather tool",
  "tool_calls": [
    {
      "tool_name": "get_weather",
      "arguments": {"city": "Tokyo", "country_code": "JP"}
    }
  ],
  "tool_results": {
    "get_weather": {
      "result": "Weather in Tokyo: 68°F, Clear sky...",
      "error": null,
      "execution_time": 0.45
    }
  },
  "response": "The weather in Tokyo is currently 68°F with clear skies...",
  "execution_time": 0.45
}
```

#### POST /query/image

Query with image attachment

#### POST /knowledge/add

Add document to knowledge base

### WebSocket Endpoints

#### WS /ws/sentinel

Unified real-time endpoint

Send Message Types:
```javascript
// Text query
{
  "type": "query",
  "query": "your question",
  "context": {}
}

// Audio chunk (streaming)
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio",
  "timestamp": 1234567890
}

// Screen frame
{
  "type": "screen_frame",
  "data": "base64_encoded_image",
  "timestamp": 1234567890
}
```

Receive Message Types:

- status - Processing updates
- reasoning - Agent's thought process
- tool_results - Tool execution results
- final_response - Complete answer
- transcript - Voice transcription
- screen_analysis - Screen capture analysis

## Configuration

### Environment Variables
```bash
# Core APIs
OPENAI_API_KEY=           # Required
ANTHROPIC_API_KEY=        # Required

# Live Data APIs (Optional)
WEATHER_API_KEY=          # openweathermap.org
NEWS_API_KEY=             # newsapi.org
ALPHA_VANTAGE_KEY=        # alphavantage.co

# Server Settings
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# File Upload
MAX_FILE_SIZE=10485760    # 10MB

# RAG Settings
VECTOR_DB_PATH=./data/vector_db
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Agent Configuration

Edit backend/agents/orchestrator.py:
```python
orchestrator = AgentOrchestrator(
    reasoning_agent=reasoning_agent,
    tool_registry=registry,
    max_iterations=3  # Max agent reasoning loops
)
```

### Tool Configuration

Edit backend/realtime/screen_stream.py:
```python
screen_handler = ScreenStreamHandler(
    vision_service,
    analysis_interval=5.0,     # Seconds between analyses
    change_threshold=0.3       # 30% change triggers alert
)
```

## Development

### Adding a New Tool

1. Create tool function:
```python
# backend/services/your_service.py
async def your_new_tool(param1: str, param2: int) -> str:
    # Your logic here
    return "result"
```

2. Register with MCP:
```python
# backend/main.py
registry.register(
    name="your_tool_name",
    handler=your_new_tool,
    description="What your tool does",
    parameters=[
        ToolParameter(
            name="param1",
            type=ToolParameterType.STRING,
            description="Parameter description",
            required=True
        )
    ],
    category="your_category"
)
```

3. Agent will automatically discover and use it

### Running Tests
```bash
# Backend tests
cd backend
python test_complete.py

# Individual test
python test_agent.py
```

### Code Quality
```bash
# Format code
black backend/

# Type checking
mypy backend/

# Linting
pylint backend/
```

## Project Structure
```
sentinel-ai/
├── backend/
│   ├── agents/
│   │   ├── reasoning.py       # Claude-based reasoning
│   │   ├── executor.py        # Parallel tool execution
│   │   └── orchestrator.py    # Workflow coordinator
│   ├── services/
│   │   ├── vision.py          # GPT-4V integration
│   │   ├── voice.py           # Whisper integration
│   │   ├── rag.py             # FAISS vector search
│   │   └── live_data.py       # External API integrations
│   ├── realtime/
│   │   ├── voice_stream.py    # Audio streaming handler
│   │   └── screen_stream.py   # Screen capture handler
│   ├── mcp_protocol/
│   │   ├── schema.py          # MCP data models
│   │   └── registry.py        # Tool registry
│   ├── main.py                # FastAPI application
│   ├── config.py              # Configuration
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── app/
│   │   └── page.tsx           # Main React component
│   ├── components/            # Reusable UI components
│   ├── hooks/                 # Custom React hooks
│   └── package.json           # Node dependencies
├── data/
│   ├── knowledge_base/        # Documents for RAG
│   ├── uploads/               # Temporary file storage
│   └── vector_db/             # FAISS index files
├── tests/
│   ├── test_agent.py
│   └── test_complete.py
├── .env                       # Environment variables (not committed)
├── .gitignore
└── README.md
```

## Testing

### Manual Testing Checklist

- Text Query: "What's 2+2?" (no tools)
- Weather: "What's the weather in Miami?"
- Stock: "What's Apple stock price?"
- Crypto: "Bitcoin price?"
- News: "Latest AI news"
- Multi-tool: "Weather in NYC and Tesla stock"
- Image: Upload image with question
- Voice: Record audio command
- Screen: Share screen and monitor
- Knowledge: Add doc, then search

### Automated Tests
```bash
# Run all tests
python backend/test_complete.py

# Expected output:
# Tools Listing - Pass
# Weather Tool - Pass
# Stock Tool - Pass
# Crypto Tool - Pass
# News Tool - Pass
# Web Search Tool - Pass
# Multi-Tool Query - Pass
```

## Deployment

### Docker (Coming Soon)
```bash
docker-compose up -d
```

### Manual Deployment

1. Backend (Railway, Render, AWS)
```bash
# Set environment variables in platform
# Deploy backend code
# Ensure websocket support is enabled
```

2. Frontend (Vercel, Netlify)
```bash
# Set NEXT_PUBLIC_API_URL environment variable
npm run build
# Deploy build folder
```

### Environment-Specific Config

Production:
```bash
ENVIRONMENT=production
DEBUG=False
ALLOWED_ORIGINS=https://your-domain.com
```

## How It Works

### Agent Decision Flow
```
1. User Query
   |
2. Reasoning Agent (Claude)
   - Analyzes query
   - Identifies required tools
   - Plans execution order
   |
3. Concurrent Executor
   - Executes tools in parallel
   - Handles errors/timeouts
   |
4. Synthesis
   - Agent combines results
   - Generates natural response
   |
5. User Response
```

### Example: Multi-Modal Query

Query: "Analyze this dashboard and tell me about recent tech news"
```
1. Agent Reasoning:
   "User uploaded image and wants news.
    I need: analyze_image + get_news"

2. Parallel Execution:
   - analyze_image(image_data) → "Dashboard shows..."
   - get_news("tech") → "Recent articles..."
   [Both execute simultaneously]

3. Synthesis:
   "The dashboard shows metrics for [X].
    Recent tech news includes [Y]..."
```

## Contributing

We welcome contributions. Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: git checkout -b feature/your-feature
3. Make changes and test
4. Commit: git commit -m "Add your feature"
5. Push: git push origin feature/your-feature
6. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint config for TypeScript/React
- Add tests for new features
- Update documentation
- Keep PRs focused and atomic

## Troubleshooting

### Common Issues

WebSocket connection failed
- Ensure backend is running on port 8000
- Check CORS settings in .env

Tool not found in registry
- Verify tool is registered in main.py
- Check tool name spelling

API key error
- Verify all required API keys in .env
- Check key format (should start with sk-)

Voice recording not working
- Allow microphone permissions in browser
- Use HTTPS in production (required for mic access)

Screen capture unavailable
- Use Chrome/Edge (best support)
- Grant screen share permission

## Performance

### Benchmarks

- Simple query: 1-2s response time
- Image analysis: 2-3s (GPT-4V)
- Voice transcription: 500ms per 2s chunk
- Multi-tool query: 2-4s (parallel execution)
- Screen analysis: 3-5s per frame

### Optimization Tips

- Use caching for repeated queries
- Increase analysis intervals for screen capture
- Batch knowledge base additions
- Use connection pooling for external APIs

## Security

- API Keys: Never commit .env to version control
- Input Validation: All inputs sanitized via Pydantic
- Rate Limiting: Implement in production
- CORS: Configure allowed origins properly
- WebSocket: Add authentication in production

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4V and Whisper
- Anthropic for Claude Sonnet 4
- FastAPI team for excellent async framework
- React team for frontend framework

## Contact

- GitHub: @yourusername
- Email: your.email@example.com
- Twitter: @yourhandle

## Roadmap

- Multi-modal input (text, voice, vision) - Complete
- Real-time streaming 
- Autonomous tool selection 
- Live data integrations 
- Custom tool marketplace 
- Multi-agent collaboration 
- Memory and personalization
- Docker deployment 
- Cloud hosting templates 

Built by Your Name

SentinelAI - Where AI Agents Meet Reality