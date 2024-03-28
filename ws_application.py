import asyncio
import signal

from autogen.io.websockets import IOWebsockets

from captn.captn_agents.application import on_connect


async def main():
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    with IOWebsockets.run_server_in_thread(
        on_connect=on_connect,
        host="0.0.0.0",  # nosec [B104]
        port=8080,
    ) as uri:
        print(f"Websocket server started at {uri}.", flush=True)
        await stop


if __name__ == "__main__":
    asyncio.run(main())
