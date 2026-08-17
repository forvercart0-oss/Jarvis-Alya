"""Reverse proxy configuration for JARVIS Phase 28."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("jarvis.devops.reverse_proxy")


class ReverseProxyManager:
    def detect(self) -> str:
        import shutil
        for proxy in ["nginx", "caddy", "traefik"]:
            if shutil.which(proxy):
                return proxy
        return "none"

    def generate_nginx_config(self, services: list[dict[str, Any]]) -> str:
        lines = ["events { worker_connections 1024; }", "http {"]
        for svc in services:
            lines.append(f"  upstream {svc['name']} {{")
            lines.append(f"    server {svc.get('host', 'localhost')}:{svc.get('port', 8000)};")
            lines.append("  }")
        for svc in services:
            domain = svc.get("domain", f"{svc['name']}.local")
            lines.append("  server {")
            lines.append("    listen 80;")
            lines.append(f"    server_name {domain};")
            lines.append("    location / {")
            lines.append(f"      proxy_pass http://{svc['name']};")
            lines.append("      proxy_set_header Host $host;")
            lines.append("    }")
            lines.append("  }")
        lines.append("}")
        return "\n".join(lines)

    def generate_caddyfile(self, services: list[dict[str, Any]]) -> str:
        lines = []
        for svc in services:
            domain = svc.get("domain", f"{svc['name']}.local")
            target = f"{svc.get('host', 'localhost')}:{svc.get('port', 8000)}"
            lines.append(f"{domain} {{\n  reverse_proxy {target}\n}}")
        return "\n".join(lines)


reverse_proxy_manager = ReverseProxyManager()
