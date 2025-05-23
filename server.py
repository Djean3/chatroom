import asyncio
##
from rooms import RoomManager
from utils import trim_newline
from rich import print
print("[bold green]Server started successfully![/bold green]")

HOST = "127.0.0.1"
PORT = 8080
COLOR_YOU = "\033[92m"  # Light green for your own messages
COLOR_OTHER = "\033[94m"  # Light blue for others' messages
COLOR_RESET = "\033[0m"  # Reset to default terminal color

room_manager = RoomManager()

async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"[+] New connection from {addr}")

    writer.write(b"Enter your username:\n")
    await writer.drain()
    username = await reader.readline()
    username = trim_newline(username.decode())

    while True:
        menu = (
            "\n--- Chat Menu ---\n"
            "1. Create a new chat room\n"
            "2. Join an existing chat room\n"
            "3. List all chat rooms\n"
            "4. Exit\n"
            "Enter your choice: "
        )
        writer.write(menu.encode())
        await writer.drain()

        choice = await reader.readline()
        if not choice:
            break
        choice = trim_newline(choice.decode())

        if choice == "1":
            writer.write(b"Enter new room name:\n")
            await writer.drain()
            roomname = trim_newline((await reader.readline()).decode())
            if await room_manager.create_room(roomname):
                await join_chatroom(roomname, username, reader, writer)
            else:
                writer.write(b"Room already exists.\n")
                await writer.drain()

        elif choice == "2":
            rooms = await room_manager.list_rooms()

            if not rooms:
                writer.write(b"\nNo active chat rooms. Create one first.\n")
                await writer.drain()
                continue

            room_list = "\n".join(
                f"{room} ({len(rooms[room].members)} user(s))"
                for room in rooms
            )
            writer.write(f"\nAvailable rooms:\n{room_list}\n\n".encode())
            await writer.drain()

            writer.write(b"Enter room name to join: ")
            await writer.drain()

            data = await reader.readline()
            roomname = data.decode().strip()

            if roomname in rooms:
                await join_chatroom(roomname, username, reader, writer)
            else:
                writer.write(b"Room not found.\n")
                await writer.drain()

        elif choice == "3":
            rooms = await room_manager.list_rooms()

            if not rooms:
                writer.write(b"\nNo rooms yet.\n")
                await writer.drain()
            else:
                room_list = "\n".join(rooms.keys())
                writer.write(f"\nRooms:\n{room_list}\n".encode())
                await writer.drain()

        elif choice == "4":
            writer.write(b"Goodbye!\n")
            await writer.drain()
            break
        else:
            writer.write(b"Invalid choice.\n")
            await writer.drain()

    writer.close()
    await writer.wait_closed()
    print(f"[-] {addr} disconnected.")

async def join_chatroom(roomname, username, reader, writer):
    writer.write(f"\nJoined room [{roomname}]. Type 'exit' to leave.\n".encode())
    await writer.drain()
    room = room_manager.rooms[roomname]
    room.add(writer, username)

    try:
        while True:
            message = await reader.readline()
            if not message:
                break
            message = trim_newline(message.decode())
            if not message:
                continue  # Skip blank lines to avoid accidental echo
            if message.lower() == "exit":
                break
            if message.lower() == "/who":
                users = ", ".join(room.get_usernames())
                writer.write(f"\nUsers in this room: {users}\n\n".encode())
                await writer.drain()
                continue
            from datetime import datetime  # Make sure this is at the top if it's not already

            timestamp = datetime.now().strftime("%H:%M")
            you_msg = f"{COLOR_YOU}[{timestamp}] [YOU] {message}{COLOR_RESET}\n"
            others_msg = f"{COLOR_OTHER}[{timestamp}] [{username}] {message}{COLOR_RESET}\n"

            # Show the message back to the sender with [YOU]
            writer.write(you_msg.encode())
            await writer.drain()

            # Broadcast to everyone else
            await room.broadcast(others_msg, sender=writer)
    finally:
        room.discard((writer, username))
        writer.write(b"You have left the room.\n\n")
        await writer.drain()

async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    print(f"Server started on {HOST}:{PORT}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
