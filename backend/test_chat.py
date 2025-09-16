import requests
import json

def test_gemini_chat():
    url = "http://127.0.0.1:8000/api/chat_pdf"
    
    # Test question about the uploaded PDF
    payload = {
        "question": "What is the main topic of this paper?",
        "paper_id": None
    }
    
    try:
        print("Testing Gemini integration...")
        print(f"Sending request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse:")
            print(json.dumps(result, indent=2))
            
            # Check if Gemini was called
            if result.get('gemini_called'):
                print("\n✅ SUCCESS: Gemini integration is working!")
                print(f"Answer: {result.get('answer', 'No answer')}")
            else:
                print("\n❌ ISSUE: Gemini was not called")
        else:
            print(f"\nError Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_gemini_chat()