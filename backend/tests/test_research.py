import httpx
import asyncio
import json

async def test_research_pipeline():
    url = "http://127.0.0.1:8000/api/v1/research/query"
    session_id = "test_user_123"
    
    print("\n--- TURN 1: Initial Research ---")
    payload1 = {
        "patient_name": "John Doe",
        "disease": "Parkinson's Disease",
        "query": "What are the latest treatments?",
        "session_id": session_id
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Sending request: {payload1['query']}...")
        resp1 = await client.post(url, json=payload1)
        
        if resp1.status_code == 200:
            data = resp1.json()
            print("\nASSISTANT RESPONSE:")
            print(data["data"]["answer"])
            print(f"\nSources Found: {len(data['data']['sources'])}")
        else:
            print(f"Error Turn 1: {resp1.status_code} - {resp1.text}")
            return

    print("\n--- TURN 2: Follow-up Insight ---")
    payload2 = {
        "patient_name": "John Doe",
        "disease": "Parkinson's Disease",
        "query": "Are there any side effects for these?",
        "session_id": session_id
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        print(f"Sending follow-up: {payload2['query']}...")
        resp2 = await client.post(url, json=payload2)
        
        if resp2.status_code == 200:
            data = resp2.json()
            print("\nASSISTANT RESPONSE (Context-Aware):")
            print(data["data"]["answer"])
        else:
            print(f"Error Turn 2: {resp2.status_code} - {resp2.text}")

if __name__ == "__main__":
    print("Pre-requisites for this test:")
    print("1. LM Studio is running on port 1234 with a model loaded.")
    print("2. MongoDB is running (Local or Atlas URL in .env).")
    print("3. FastAPI server is running (uvicorn app.main:app --reload).")
    
    # Check if uvicorn is running or wait for user
    input("\nPress Enter if your server is running to start the test...")
    asyncio.run(test_research_pipeline())
