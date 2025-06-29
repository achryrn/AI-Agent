#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.search import SearchTool

async def test_rc_search():
    """Test the SearchTool with RC car query"""
    
    print("🔍 TESTING RC CAR SEARCH TOOL")
    print("=" * 50)
    
    # Initialize the search tool
    search_tool = SearchTool(max_sites=3, max_depth=2)
    
    # Test input for RC car parts
    test_input = {
        "query": "RC car parts components building guide",
        "target_info": "Complete list of parts needed to build an RC car from scratch"
    }
    
    print(f"🎯 Query: {test_input['query']}")
    print(f"🎯 Target: {test_input['target_info']}")
    print("⏱️  Starting search...")
    
    try:
        # Run the search
        result = search_tool.run(test_input)
        
        print("\n✅ SEARCH COMPLETED!")
        print("=" * 50)
        print("📋 RESULTS:")
        print(result)
        
        # Analyze the result
        if "No search results found" in result:
            print("\n⚠️  No web results found, but should have fallback content")
        elif "RC Car Building Components Guide" in result:
            print("\n✅ Fallback content provided successfully")
        elif "COMPREHENSIVE SEARCH RESULTS" in result:
            print("\n✅ Web search results obtained successfully")
        else:
            print("\n❓ Unexpected result format")
            
    except Exception as e:
        print(f"\n❌ Search failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_sync_search():
    """Test synchronous version"""
    print("\n🔍 TESTING SYNCHRONOUS RC CAR SEARCH")
    print("=" * 50)
    
    search_tool = SearchTool(max_sites=2, max_depth=1)
    
    test_input = {
        "query": "RC car motors batteries ESC servo parts",
        "target_info": "Essential electronic components for RC car"
    }
    
    print(f"🎯 Query: {test_input['query']}")
    print("⏱️  Starting synchronous search...")
    
    try:
        result = search_tool.run(test_input)
        print("\n✅ SYNCHRONOUS SEARCH COMPLETED!")
        print("=" * 50)
        print("📋 RESULTS:")
        print(result[:500] + "..." if len(result) > 500 else result)
        
    except Exception as e:
        print(f"\n❌ Synchronous search failed: {e}")

if __name__ == "__main__":
    # Test async version
    asyncio.run(test_rc_search())
    
    # Test sync version
    test_sync_search()
    
    print("\n🎉 RC CAR SEARCH TESTING COMPLETED!")