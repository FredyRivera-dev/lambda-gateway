import asyncio
import time
from typing import Dict
from fastapi import Request
import httpx

# Timeout setting (in seconds)
CONTAINER_IDLE_TIMEOUT = 15

async def cleanup_idle_containers(running_containers: Dict[str, dict]):
    # Background task that cleans up inactive containers
    while True:
        await asyncio.sleep(5)
        now = time.time()
        
        to_remove = []
        for app_name, info in running_containers.items():
            idle_time = now - info['last_access']
            if idle_time > CONTAINER_IDLE_TIMEOUT:
                to_remove.append(app_name)
        
        for app_name in to_remove:
            info = running_containers.pop(app_name, None)
            if info and info.get('container'):
                try:
                    container = info['container']
                    container.stop(timeout=3)
                    container.remove()
                    print(f"Container '{app_name}' stopped due to inactivity ({idle_time:.1f}s)")
                except Exception as e:
                    print(f"Error cleaning container '{app_name}': {e}")

def get_app_url(app_name: str, request: Request) -> str:
    base_url = str(request.base_url).rstrip('/')
    return f"{base_url}/app/{app_name}"

async def wait_for_service(url: str, timeout: float = 10.0, interval: float = 0.2):
    deadline = asyncio.get_event_loop().time() + timeout
    async with httpx.AsyncClient() as client:
        while True:
            try:
                r = await client.get(url, timeout=1.0)
                return True
            except (httpx.RequestError, httpx.ConnectError, httpx.ReadTimeout):
                if asyncio.get_event_loop().time() > deadline:
                    return False
                await asyncio.sleep(interval)

def filter_request_headers(headers: dict) -> dict:
    hop_by_hop = {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailers", "transfer-encoding", "upgrade", "host"
    }
    return {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}

_next_port = 3500

def get_next_available_port() -> int:
    global _next_port
    port = _next_port
    _next_port += 1
    return port