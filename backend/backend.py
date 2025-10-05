from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from buildlambda import BuildandRunLambda
from pydantic import BaseModel, Field
from typing import Dict
import asyncio
import httpx
import time
from utils import cleanup_idle_containers, get_app_url, wait_for_service, filter_request_headers, get_next_available_port

deployed_apps: Dict[str, dict] = {}
app_locks: Dict[str, asyncio.Lock] = {}
running_containers: Dict[str, dict] = {}  # {app_name: {container, last_access}}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # At the global level we instantiate a "BuildandRunLambda" 
    # that is seen to be in charge of the invocations
    app.state.run = BuildandRunLambda()
    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_idle_containers(running_containers))
    yield
    # We clean all containers when closing
    cleanup_task.cancel()
    for app_name, info in running_containers.items():
        try:
            if info.get('container'):
                info['container'].stop()
                info['container'].remove()
        except:
            pass

app = FastAPI(lifespan=lifespan)

# Minimum payload for the build API
class JSONBuild(BaseModel):
    project_path: str
    app_name: str
    framework: str
    env_vars: dict
    port: int | None = Field(default=None)

# API for making the builds
@app.post("/build/lambda")
async def build_lambda(q: JSONBuild):
    build = BuildandRunLambda(q.project_path)
    try:
        build.build(app_name=q.app_name,
                    framework=q.framework,
                    env_vars=q.env_vars)

        if q.port is None:
            port = get_next_available_port()
        else:
            port = q.port

        deployed_apps[q.app_name] = {
            "framework": q.framework,
            "port": port,
            "env_vars": q.env_vars
        }

        app_locks.setdefault(q.app_name, asyncio.Lock())

        return {"success": True}

    except Exception as e:
        print(f"Error: {e}")
        return {
            "success": False,
            "error": str(e),
        }

# We get the apps we have built
@app.get("/apps")
async def get_apps(request: Request):
    results = []

    for name, info in deployed_apps.items():
        port = info.get("port")
        framework = info.get("framework")
        env_vars = info.get("env_vars", {})
        is_running = name in running_containers
        
        try:
            url = get_app_url(name, request)
        except Exception:
            url = f"{str(request.base_url).rstrip('/')}/app/{name}"

        results.append({
                "app_name": name,
                "url": url,
                "port": port,
                "framework": framework,
                "env_vars": env_vars,
                "status": "running" if is_running else "stopped"
            })

    return {"apps": results}

@app.get("/app/{app_name}")
async def redirect_app_root(app_name: str):
    return Response(
        status_code=307,
        headers={"Location": f"/app/{app_name}/"}
    )

@app.api_route("/app/{app_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_app(app_name: str, path: str, request: Request):

    if app_name not in deployed_apps:
        raise HTTPException(404, f"App '{app_name}' not found")

    app_info = deployed_apps[app_name]
    target_port = app_info['port']
    framework = app_info['framework']

    # For static frameworks (Vite/React), Nginx serves from "/"
    # For Next.js, the Node server can handle basePath
    if framework in ["vite", "react"]:
        # Remove the /app/{app_name} prefix for static applications
        target_url = f"http://localhost:{target_port}/{path}"
    else:
        # Next.js and other dynamic frameworks receive the full path
        target_url = f"http://localhost:{target_port}/app/{app_name}/{path}"
    
    if request.url.query:
        target_url += f"?{request.url.query}"

    lock = app_locks.setdefault(app_name, asyncio.Lock())
    
    # Check if a container is already running
    container_info = running_containers.get(app_name)
    
    if container_info is None:
        async with lock:
            # Double verification for security
            container_info = running_containers.get(app_name)
            if container_info is None:
                try:
                    print(f"Starting container for '{app_name}'...")
                    container = await asyncio.to_thread(
                        app.state.run.invoke_function,
                        app_name,
                        app_info['framework'],
                        target_port,
                        app_info.get('env_vars', {})
                    )
                    
                    running_containers[app_name] = {
                        'container': container,
                        'last_access': time.time()
                    }
                    container_info = running_containers[app_name]
                    
                    # Wait for the service to be ready
                    # For static frameworks, check from "/"
                    # For Next.js, check from "/app/{app_name}/"
                    if framework in ["vite", "react"]:
                        health_check_url = f"http://localhost:{target_port}/"
                    else:
                        health_check_url = f"http://localhost:{target_port}/app/{app_name}/"
                    
                    ready = await wait_for_service(health_check_url, timeout=15.0, interval=0.2)
                    
                    if not ready:
                        try:
                            info = await asyncio.to_thread(app.state.run.stop_and_collect, container, 3, True)
                            running_containers.pop(app_name, None)
                        except Exception:
                            info = {"error": "The container could not be stopped after a timeout"}
                        raise HTTPException(status_code=503, detail=f"The service on '{app_name}' did not respond in a timely manner. Info: {info}")
                    
                except Exception as e:
                    running_containers.pop(app_name, None)
                    raise HTTPException(status_code=500, detail=f"Error starting container: {e}")
    
    # Update last access timestamp
    container_info['last_access'] = time.time()

    # Make the proxy request
    try:
        body = await request.body()
        headers = filter_request_headers(dict(request.headers))
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0
            )

            response_headers = {k: v for k, v in resp.headers.items() if k.lower() not in ("content-encoding", "transfer-encoding", "connection")}

        return Response(content=resp.content, status_code=resp.status_code, headers=response_headers, media_type=resp.headers.get("content-type"))

    except httpx.ConnectError:
        # If it fails, clean the container
        running_containers.pop(app_name, None)
        raise HTTPException(503, f"Could not connect to '{app_name}'")
    except httpx.TimeoutException:
        raise HTTPException(504, f"Timeout connecting with '{app_name}'")
    except Exception as e:
        raise HTTPException(500, f"Proxy error: {str(e)}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/{filename:path}")
async def catch_static_files(filename: str, request: Request):
    static_extensions = (
        '.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico', 
        '.webp', '.woff', '.woff2', '.ttf', '.eot'
    )
    
    if not filename.lower().endswith(static_extensions):
        raise HTTPException(404, "Not found")
    
    if not deployed_apps:
        raise HTTPException(404, f"File '{filename}' not found")
    
    referer = request.headers.get('referer', '')
    target_app = None
    
    for app_name in deployed_apps.keys():
        if f"/app/{app_name}" in referer:
            target_app = app_name
            break
    
    if not target_app:
        target_app = list(deployed_apps.keys())[0]
    
    redirect_url = f"/app/{target_app}/{filename}"
    return Response(
        status_code=307,
        headers={"Location": redirect_url}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5500)