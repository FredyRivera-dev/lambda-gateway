import docker
from pathlib import Path
from typing import Dict, Optional
import time

class BuildandRunLambda:
    def __init__(self, project_path: str | None = None):
        self.client = docker.from_env()
        self.project_path = Path(project_path) if project_path is not None else None
        self._invoke_only = project_path is None
        # This is used to verify that there is a .dockerignore
        # If there isn't one, we create it so that the builds aren't so heavy
        if self.project_path is not None:
            self._ensure_dockerignore()
    
    @classmethod
    def for_invoke(cls):
        return cls(project_path=None)

    def build(self, app_name: str,
                    framework: str,
                    env_vars: dict | None = None):

        if self._invoke_only or self.project_path is None:
            raise RuntimeError("This instance does not have a 'project_path'. Use the constructor with project_path to 'build'.")

        env_vars = env_vars or {}

        
        base_path = f"/app/{app_name}"
        env_vars['BASE_PATH'] = base_path

        self.create_dockerfile(framework)

        dockerfile = self._get_dockerfile(framework)

        image, logs = self.client.images.build(
            path=str(self.project_path),
            dockerfile=dockerfile,
            tag=f"{app_name}:latest",
            buildargs=env_vars,  
            rm=True,  
            pull=True 
        )

        try:
            for log in logs:
                if isinstance(log, dict) and 'stream' in log:
                    print(log['stream'].strip())
                else:
                    print(str(log))
        except Exception:
            pass

        return image

    def invoke_function(self, app_name: str,
                        framework: str,
                        port: int,
                        env_vars: Optional[Dict] = None):
        
        env = self._get_runtime_env(framework, env_vars or {})
        env['PORT'] = str(port)
        env['HOSTNAME'] = '0.0.0.0'

        # We do NOT pass BASE_PATH in runtime - only in build
        # The container serves from "/" internally

        if framework in ['vite', 'react']:
            internal_port = 80
        else:
            internal_port = port

        container = self.client.containers.run(
            image=f"{app_name}:latest",
            detach=True,
            remove=False,
            ports={f'{internal_port}/tcp': port},
            # Limited resources
            mem_limit="128m",
            nano_cpus=500000000,  # 0.5 CPU
            environment=env,
            labels={
                "type": "serverless",
                "invocation": str(time.time())
            }
        )

        time.sleep(5)
        container.reload()
        logs = container.logs(tail=50).decode()

        print(f"\n{'='*50}")
        print(f"State: {container.status}")
        print(f"Port: {port}")
        print(f"Logs:\n{logs}")
        print(f"{'='*50}\n")

        return container

    def stop_and_collect(self, container, timeout: int = 10, remove_after: bool = True):
        try:
            if container.status == 'running':
                container.stop(timeout=timeout)
            result = container.wait(timeout=timeout)
            logs = container.logs(stdout=True, stderr=True)
            exit_code = result.get('StatusCode', None) if isinstance(result, dict) else None
            if remove_after:
                try:
                    container.remove()
                except Exception:
                    pass
            return {
                "exit_code": exit_code,
                "logs": logs.decode() if isinstance(logs, bytes) else str(logs)
            }
        except Exception as e:
            try:
                container.remove(force=True)
            except Exception:
                pass
            return {"error": str(e)}

    def _get_dockerfile(self, framework: str) -> str:
        dockerfiles = {
            "nextjs": "Dockerfile.nextjs",
            "vite": "Dockerfile.vite",
            "react": "Dockerfile.vite"
        }
        return dockerfiles.get(framework, "Dockerfile")

    def _get_runtime_env(self, framework: str, env_vars: dict) -> dict:
        if framework == "nextjs":
            return {
                k: v for k, v in env_vars.items()
                if not k.startswith("NEXT_PUBLIC_")
            }
        return {}

    def create_dockerfile(self, framework: str):
        if self.project_path is None:
            raise RuntimeError("You need project_path to create Dockerfiles")
    
        dockerfile_path = self.project_path / self._get_dockerfile(framework)
    
        if dockerfile_path.exists():
            print(f"{dockerfile_path.name} already exists")
            return
    
        content = self._get_dockerfile_content(framework)
        dockerfile_path.write_text(content)

        if framework in ["vite", "react"]:
            self._create_nginx_conf()

    def gen_dockerignore(self):
        file = """
node_modules
.next
.git
.env*.local
npm-debug.log*
README.md
.dockerignore
Dockerfile 
        """
        return file

    def _ensure_dockerignore(self):
        if self.project_path is None:
            return

        dockerignore_path = self.project_path / ".dockerignore"
        
        if not dockerignore_path.exists():
            dockerignore_content = self.gen_dockerignore()
            dockerignore_path.write_text(dockerignore_content)

    def _get_dockerfile_content(self, framework: str) -> str:
        if framework == "nextjs":
            # DOCKERFILE
            return """FROM node:24-alpine3.21 AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production

FROM node:24-alpine3.21 AS builder
WORKDIR /app

ARG BASE_PATH
ENV BASE_PATH=${BASE_PATH}

COPY package.json package-lock.json* ./
RUN npm ci
COPY . .

RUN npm run build

FROM node:24-alpine3.21 AS runner
WORKDIR /app

ARG BASE_PATH
ENV BASE_PATH=${BASE_PATH}
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/next.config.* ./
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER nextjs
EXPOSE 3000
CMD ["npm", "start"]"""
    
        elif framework in ["vite", "react"]:
            return """FROM node:24-alpine3.21 AS builder
WORKDIR /app

ARG BASE_PATH
ENV BASE_PATH=${BASE_PATH}

COPY package.json package-lock.json* ./

RUN echo "Package.json scripts:" && cat package.json | grep -A 5 "scripts" || echo "No scripts found"

RUN npm ci

COPY . .

RUN echo "Running build..." && \\
    echo "BASE_PATH set to: $BASE_PATH" && \\
    npm run build && \\
    echo "Build completed" && \\
    echo "Checking dist/:" && \\
    ls -la dist/ || (echo "ERROR: dist/ directory not found" && exit 1)

FROM nginx:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]"""
    
        return ""

    def _create_nginx_conf(self):
        if self.project_path is None:
            return
        
        nginx_conf_path = self.project_path / "nginx.conf"
        
        if nginx_conf_path.exists():
            print(f"nginx.conf ya existe")
            return
        
        nginx_content = r"""server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Cache for static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}"""
        
        nginx_conf_path.write_text(nginx_content)