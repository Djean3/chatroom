import asyncio
import sys
from utils import trim_newline

HOST = "127.0.0.1"
PORT = 8080

async def handle_recv(reader):
    try:
        while True:
            data = await reader.readline()
            if not data:
                print("\n[Disconnected from server]")
                sys.exit(0)
            print(data.decode(), end="")
    except Exception as e:
        print(f"\n[Error receiving data: {e}]")
        sys.exit(1)

import readline  

async def handle_send(writer):
    try:
        while True:
            msg = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not msg:
                break
            # Clear the local echoed line from the terminal
            sys.stdout.write("\033[F\033[K")  # move cursor up and clear line
            writer.write(msg.encode())
            await writer.drain()
    except Exception as e:
        print(f"\n[Error sending data: {e}]")
        sys.exit(1)

async def main():
    reader, writer = await asyncio.open_connection(HOST, PORT)
    print(f"[Connected to {HOST}:{PORT}]\n")

    recv_task = asyncio.create_task(handle_recv(reader))
    send_task = asyncio.create_task(handle_send(writer))

    done, pending = await asyncio.wait(
        [recv_task, send_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()

    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Client exited]")
