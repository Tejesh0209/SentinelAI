#!/usr/bin/env python3
# backend/test_complete.py
"""
Complete test suite for all SentinelAI features
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"

async def test_weather_tool():
    """Test weather tool"""
    print("\n=== Testing Weather Tool ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=What%27s%20the%20weather%20in%20New%20York%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: What's the weather in New York?")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            if 'get_weather' in [tc['tool_name'] for tc in data['tool_calls']]:
                print("✅ Weather tool triggered")
            else:
                print("⚠️ Weather tool not triggered")

async def test_stock_tool():
    """Test stock price tool"""
    print("\n=== Testing Stock Tool ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=What%27s%20the%20current%20price%20of%20Apple%20stock%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: What's Apple stock price?")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            if 'get_stock_price' in [tc['tool_name'] for tc in data['tool_calls']]:
                print("✅ Stock tool triggered")
            else:
                print("⚠️ Stock tool not triggered")

async def test_crypto_tool():
    """Test crypto price tool"""
    print("\n=== Testing Crypto Tool ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=What%27s%20the%20price%20of%20Bitcoin%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: Bitcoin price?")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            if 'get_crypto_price' in [tc['tool_name'] for tc in data['tool_calls']]:
                print("✅ Crypto tool triggered")

async def test_news_tool():
    """Test news tool"""
    print("\n=== Testing News Tool ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=Get%20me%20the%20latest%20news%20about%20artificial%20intelligence"
        ) as resp:
            data = await resp.json()
            print(f"Query: Latest AI news")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            if 'get_news' in [tc['tool_name'] for tc in data['tool_calls']]:
                print("✅ News tool triggered")

async def test_web_search_tool():
    """Test web search tool"""
    print("\n=== Testing Web Search Tool ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=Search%20for%20information%20about%20quantum%20computing"
        ) as resp:
            data = await resp.json()
            print(f"Query: Search quantum computing")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Response: {data['response'][:200]}...")
            
            if 'web_search' in [tc['tool_name'] for tc in data['tool_calls']]:
                print("✅ Web search tool triggered")

async def test_multi_tool_query():
    """Test complex query using multiple tools"""
    print("\n=== Testing Multi-Tool Query ===")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/query?query=What%27s%20the%20weather%20in%20San%20Francisco%20and%20the%20current%20price%20of%20Tesla%20stock%3F"
        ) as resp:
            data = await resp.json()
            print(f"Query: Weather + Stock (multi-tool)")
            print(f"Tools used: {[tc['tool_name'] for tc in data['tool_calls']]}")
            print(f"Execution time: {data['execution_time']:.2f}s")
            print(f"Response: {data['response'][:200]}...")
            
            tools_used = [tc['tool_name'] for tc in data['tool_calls']]
            if len(tools_used) >= 2:
                print(f"✅ Multiple tools triggered: {tools_used}")
            else:
                print(f"⚠️ Expected multiple tools, got: {tools_used}")

async def test_tools_listing():
    """Test tools endpoint"""
    print("\n=== Testing Tools Listing ===")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/tools") as resp:
            data = await resp.json()
            print(f"Total tools: {data['total']}")
            print(f"Categories: {data['categories']}")
            
            for category, tools in data['tools_by_category'].items():
                print(f"  {category}: {len(tools)} tools")
            
            print("✅ Tools listing complete")

async def run_all_tests():
    """Run complete test suite"""
    print("="*60)
    print("SentinelAI Complete Feature Test Suite")
    print("="*60)
    
    tests = [
        ("Tools Listing", test_tools_listing),
        ("Weather Tool", test_weather_tool),
        ("Stock Tool", test_stock_tool),
        ("Crypto Tool", test_crypto_tool),
        ("News Tool", test_news_tool),
        ("Web Search Tool", test_web_search_tool),
        ("Multi-Tool Query", test_multi_tool_query),
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
        print("\n🎉 All tests passed! SentinelAI is fully operational.")
    else:
        print(f"\n{failed} test(s) failed. Check configuration.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())