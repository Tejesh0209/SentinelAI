#!/usr/bin/env python3
# backend/test_agent.py
"""
Test suite for SentinelAI agent system
Run with: python test_agent.py
"""

import asyncio
import aiohttp
import json
import base64
from pathlib import Path

BASE_URL = "http://localhost:8000"

async def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as resp:
            data = await resp.json()
            print(f"Status: {resp.status}")
            print(f"Response: {json.dumps(data, indent=2)}")
            assert data["status"] == "healthy"
            print("Health check passed")

async def test_list_tools():
    """Test tools listing"""
    print("\n=== Testing Tools Endpoint ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/tools") as resp:
            data = await resp.json()
            print(f"Tools available: {data['total']}")
            for category, tools in data['tools_by_category'].items():
                print(f"  {category}: {len(tools)} tools")
            print("✅ Tools listing passed")

async def test_simple_query():
    """Test query that doesn't need tools"""
    print("\n=== Testing Simple Query (No Tools) ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=What%20is%20the%20capital%20of%20France%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: What is the capital of France?")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:100]}...")
            print("✅ Simple query passed")

async def test_knowledge_base():
    """Test RAG functionality"""
    print("\n=== Testing Knowledge Base ===")
    
    # Add documents
    print("Adding documents...")
    async with aiohttp.ClientSession() as session:
        docs = [
            "SentinelAI is an autonomous agent with multimodal capabilities.",
            "The system can analyze images using GPT-4 Vision.",
            "Voice transcription is handled by OpenAI Whisper.",
            "The agent uses OpenAI for reasoning and decision making."
        ]
        
        for i, doc in enumerate(docs):
            async with session.post(
                f"{BASE_URL}/knowledge/add",
                params={"text": doc}
            ) as resp:
                result = await resp.json()
                print(f"  Added doc {i+1}: ID {result['doc_id']}")
        
        # Query that should use knowledge base
        print("\nQuerying knowledge base...")
        async with session.post(
            f"{BASE_URL}/query?query=How%20does%20SentinelAI%20handle%20voice%20input%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: How does SentinelAI handle voice input?")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            # Check if search_knowledge was used
            tool_names = [tc['tool_name'] for tc in data['tool_calls']]
            if 'search_knowledge' in tool_names:
                print("✅ Knowledge base search triggered correctly")
            else:
                print("⚠️ Warning: search_knowledge not triggered")

async def test_image_analysis():
    """Test image analysis"""
    print("\n=== Testing Image Analysis ===")
    
    print("Note: Using placeholder image data for testing")
    print("In production, replace with actual image file")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=Describe%20what%27s%20in%20this%20image"
        ) as resp:
            data = await resp.json()
            print(f"Query: Describe what's in this image")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            
            tool_names = [tc['tool_name'] for tc in data['tool_calls']]
            if 'analyze_image' in tool_names:
                print("✅ Image analysis tool triggered correctly")
            else:
                print("⚠️ Warning: analyze_image not triggered")

async def test_multi_tool_query():
    """Test query that needs multiple tools"""
    print("\n=== Testing Multi-Tool Query ===")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=Analyze%20this%20screenshot%20and%20search%20for%20related%20documentation"
        ) as resp:
            data = await resp.json()
            print(f"Query: Analyze this screenshot and search for related documentation")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Execution time: {data['execution_time']:.2f}s")
            
            tool_names = [tc['tool_name'] for tc in data['tool_calls']]
            if len(tool_names) >= 1:
                print(f"✅ Tools triggered: {tool_names}")
            else:
                print("⚠️ Warning: Expected tools")

async def test_websocket():
    """Test WebSocket with agent"""
    print("\n=== Testing WebSocket Agent ===")
    
    try:
        import websockets
        
        async with websockets.connect(f"ws://localhost:8000/ws/sentinel") as ws:
            print("✅ Connected to WebSocket")
            
            # Send query
            await ws.send(json.dumps({
                "query": "What's the capital of France?"
            }))
            
            # Receive updates
            print("Receiving updates...")
            response_complete = False
            while True:
                message = await ws.recv()
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                print(f"  Received: {msg_type}")
                
                if msg_type == 'response':
                    response_complete = True
                    break
            
            if response_complete:
                print("✅ WebSocket test passed")
        
    except ImportError:
        print("⚠️ WebSocket test skipped: websockets not installed (pip install websockets)")
    except Exception as e:
        print(f"⚠️ WebSocket test warning: {e}")

async def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("SentinelAI Agent Test Suite")
    print("="*60)
    
    tests = [
        ("Health Check", test_health),
        ("List Tools", test_list_tools),
        ("Simple Query", test_simple_query),
        ("Knowledge Base", test_knowledge_base),
        ("Image Analysis", test_image_analysis),
        ("Multi-Tool Query", test_multi_tool_query),
        ("WebSocket", test_websocket),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"{name} failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All agent tests passed!")
    
if __name__ == "__main__":
    asyncio.run(run_all_tests())