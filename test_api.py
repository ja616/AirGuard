import asyncio
import httpx
import websockets
import json

API_URL = "http://127.0.0.1:8000/api/v1/investigations"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws/investigations/{}/stream"

async def main():
    print("1. Creating Investigation (POST /investigations)...")
    async with httpx.AsyncClient() as client:
        req_body = {"dag_id": "etl_nightly", "user_query": "Why did it fail?"}
        response = await client.post(f"{API_URL}/", json=req_body)
        investigation = response.json()
        print(f"Investigation created! ID: {investigation['id']}")
        print(f"Initial State: {investigation['state']} | Progress: {investigation['progress']}%")

        inv_id = investigation["id"]

    print(f"\n2. Connecting to WebSocket stream for Investigation {inv_id}...")
    ws_uri = WS_URL.format(inv_id)
    
    try:
        async with websockets.connect(ws_uri) as websocket:
            print("WebSocket connected. Listening for structured events...")
            while True:
                try:
                    message = await websocket.recv()
                    event = json.loads(message)
                    print(f"  -> [{event['timestamp']}] state={event['new_state']} | progress={event['progress']}%")
                except websockets.ConnectionClosed:
                    print("WebSocket closed.")
                    break
    except Exception as e:
         print(f"WebSocket Error: {e}")

    print("\n3. Verifying Final State via REST (GET /investigations/{id})...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/{inv_id}")
        investigation = response.json()
        print(f"Final State: {investigation['state']} | Progress: {investigation['progress']}%")

if __name__ == "__main__":
    asyncio.run(main())
