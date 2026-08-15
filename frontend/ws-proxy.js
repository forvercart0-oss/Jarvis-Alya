import asyncio
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ws-proxy")

BACKEND_WS = "ws://127.0.0.1:8000/ws/jarvis"
PROXY_PORT = 5175


async def proxy_handler(client_ws):
    try:
        remote = getattr(client_ws, 'remote_address', 'unknown')
        logger.info("Frontend connected from %s", remote)
    except Exception:
        logger.info("Frontend connected")
    try:
        async with websockets.connect(BACKEND_WS) as backend_ws:
            logger.info("Connected to backend")

            async def forward_to_backend():
                try:
                    async for message in client_ws:
                        await backend_ws.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as exc:
                    logger.error("Error forwarding to backend: %s", exc)
                finally:
                    await backend_ws.close()

            async def forward_to_client():
                try:
                    async for message in backend_ws:
                        await client_ws.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as exc:
                    logger.error("Error forwarding to client: %s", exc)
                finally:
                    await client_ws.close()

            await asyncio.gather(forward_to_backend(), forward_to_client())
    except Exception as exc:
        logger.error("Proxy error: %s", exc)
    finally:
        logger.info("Frontend disconnected")


async def main():
    logger.info("WebSocket proxy starting on port %d -> %s", PROXY_PORT, BACKEND_WS)
    async with websockets.serve(proxy_handler, "127.0.0.1", PROXY_PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
