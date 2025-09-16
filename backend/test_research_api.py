"""
Test script for the new research API functionality
"""
import requests
import json
import time

def test_research_api():
    base_url = "http://127.0.0.1:8000"
    
    # Test data
    research_request = {
        "query": "machine learning ethics",
        "max_results": 3,
        "min_year": 2020,
        "options": {
            "use_summary": True,
            "use_synthesis": True,
            "use_voice": False,
            "use_nft": False
        }
    }
    
    print("Testing Research API...")
    print(f"Query: {research_request['query']}")
    print("=" * 50)
    
    try:
        # Start research job
        print("1. Starting research job...")
        response = requests.post(f"{base_url}/api/research/start", json=research_request)
        
        if response.status_code != 200:
            print(f"Error starting research: {response.status_code}")
            print(response.text)
            return
        
        result = response.json()
        job_id = result["job_id"]
        print(f"✅ Research job started: {job_id}")
        
        # Poll for status
        print("\n2. Polling for status...")
        max_polls = 30  # 1 minute max
        poll_count = 0
        
        while poll_count < max_polls:
            poll_count += 1
            print(f"Poll {poll_count}/{max_polls}...")
            
            status_response = requests.get(f"{base_url}/api/research/status/{job_id}")
            if status_response.status_code != 200:
                print(f"Error getting status: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            print(f"Status: {status_data['status']}")
            
            if status_data["status"] == "completed":
                print("✅ Research completed!")
                
                # Print results
                if status_data.get("results"):
                    results = status_data["results"]
                    print(f"\n📊 Results Summary:")
                    print(f"Papers found: {len(results.get('papers', []))}")
                    print(f"Summaries generated: {len(results.get('summaries', []))}")
                    print(f"Report generated: {'Yes' if results.get('synthesized_report') else 'No'}")
                    
                    # Show paper titles
                    if results.get("papers"):
                        print("\n📄 Papers found:")
                        for i, paper in enumerate(results["papers"][:3], 1):
                            print(f"  {i}. {paper['title']} ({paper['publication_year']})")
                    
                    # Show report excerpt
                    if results.get("synthesized_report"):
                        report = results["synthesized_report"]
                        print(f"\n📋 Report excerpt:")
                        print(report[:300] + "..." if len(report) > 300 else report)
                
                break
                
            elif status_data["status"] == "error":
                print("❌ Research failed!")
                if status_data.get("progress", {}).get("error"):
                    print(f"Error: {status_data['progress']['error']['message']}")
                break
            
            time.sleep(2)  # Wait 2 seconds before next poll
        
        if poll_count >= max_polls:
            print("⏰ Timeout waiting for research to complete")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_research_api()