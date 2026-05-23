import requests

def test_generate_instrumental():
    url = "http://localhost:8001/generate_song"
    
    # Request payload
    payload = {
        "prompt": "kabyle music for wedings style mohamed allaoua",
        "instrumental": True,  # Now defaults to True, but we can explicitly pass it
        "duration_s": 45,
        "bpm": 130,
        "auto_play": True 
    }
    
    print(f"Sending request to {url}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print("Success! Response:")
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        print(f"Filename: {data.get('filename')}")
        print(f"Saved to: {data.get('path')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if e.response is not None:
            print(f"Error details: {e.response.text}")

if __name__ == "__main__":
    test_generate_instrumental()
