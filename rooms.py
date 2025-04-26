import asyncio

rooms_lock = asyncio.Lock()

class ChatRoom:
    def __init__(self, name):
        self.name = name
        self.members = set()  # Each member is a tuple: (writer, username)

    def add(self, writer, username):
        self.members.add((writer, username))

    def discard(self, writer):
        self.members = {(w, u) for w, u in self.members if w != writer}

    def get_usernames(self):
        return [username for _, username in self.members]

    async def broadcast(self, message, sender=None):
        sender_peername = sender.get_extra_info('peername') if sender else None
        for writer, _ in self.members:
            if writer.get_extra_info('peername') == sender_peername:
                continue
            writer.write(message.encode())
            await writer.drain()

class RoomManager:
    def __init__(self):
        self.rooms = {}

    async def create_room(self, name):
        async with rooms_lock:
            if name in self.rooms:
                return False
            self.rooms[name] = ChatRoom(name)
            return True

    async def join_room(self, name, writer, username):
        async with rooms_lock:
            if name in self.rooms:
                self.rooms[name].add(writer, username)
                return True
            return False

    async def leave_room(self, name, writer):
        async with rooms_lock:
            if name in self.rooms:
                self.rooms[name].discard(writer)

    async def list_rooms(self):
        async with rooms_lock:
            return self.rooms
