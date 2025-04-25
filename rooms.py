import asyncio

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
        for writer, _ in self.members:
            if writer is sender:
                continue
            writer.write(message.encode())
            await writer.drain()


class RoomManager:
    def __init__(self):
        self.rooms = {}

    def create_room(self, name):
        if name in self.rooms:
            return False
        self.rooms[name] = ChatRoom(name)
        return True

    def join_room(self, name, writer, username):
        if name in self.rooms:
            self.rooms[name].add(writer, username)
            return True
        return False

    def leave_room(self, name, writer):
        if name in self.rooms:
            self.rooms[name].discard(writer)

    def list_rooms(self):
        return self.rooms
