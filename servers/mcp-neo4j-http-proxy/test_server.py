#!/usr/bin/env python3
"""
Simple test script for the Neo4j MCP HTTP Proxy server.
Run this after starting the server to verify it's working correctly.
"""

import asyncio
import json
import httpx
from typing import Dict, Any


async def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed with status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return False


async def test_mcp_connection(base_url: str) -> bool:
    """Test basic MCP connection and tool listing."""
    try:
        async with httpx.AsyncClient() as client:
            # Initialize MCP connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await client.post(
                f"{base_url}/mcp",
                json=init_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                init_result = response.json()
                print(f"✅ MCP initialization successful")
                
                # Test listing tools
                tools_request = {
                    "jsonrpc": "2.0", 
                    "id": 2,
                    "method": "tools/list"
                }
                
                response = await client.post(
                    f"{base_url}/mcp",
                    json=tools_request,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    tools_result = response.json()
                    tools = tools_result.get("result", {}).get("tools", [])
                    print(f"✅ Tools listed successfully: {len(tools)} tools available")
                    for tool in tools[:3]:  # Show first 3 tools
                        print(f"   - {tool.get('name')}: {tool.get('description', 'No description')}")
                    return True
                else:
                    print(f"❌ Tools listing failed with status: {response.status_code}")
                    return False
            else:
                print(f"❌ MCP initialization failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ MCP connection test failed with error: {e}")
        return False


async def test_read_graph(base_url: str) -> bool:
    """Test the read_graph tool."""
    try:
        async with httpx.AsyncClient() as client:
            # Call read_graph tool
            tool_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "read_graph",
                    "arguments": {}
                }
            }
            
            response = await client.post(
                f"{base_url}/mcp",
                json=tool_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("result", {}).get("content", [])
                if content:
                    graph_data = json.loads(content[0].get("text", "{}"))
                    entities_count = len(graph_data.get("entities", []))
                    relations_count = len(graph_data.get("relations", []))
                    print(f"✅ Graph read successfully: {entities_count} entities, {relations_count} relations")
                    return True
                else:
                    print("✅ Graph read successful (empty graph)")
                    return True
            else:
                print(f"❌ Graph read failed with status: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Graph read test failed with error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 Testing Neo4j MCP HTTP Proxy Server")
    print("=" * 50)
    
    # Configure server URL
    host = "localhost"
    port = 8000
    base_url = f"http://{host}:{port}"
    
    print(f"Testing server at: {base_url}")
    print()
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("MCP Connection & Tools", test_mcp_connection),
        ("Read Graph Tool", test_read_graph),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        success = await test_func(base_url)
        if success:
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your HTTP proxy server is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 