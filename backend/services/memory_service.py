from memory.manager import MemoryManager


class MemoryService:
    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def get_conversations(self, limit: int = 50):
        return self.memory.get_conversations(limit)

    def get_messages(self, conv_id: str, limit: int = 100):
        return self.memory.get_messages(conv_id, limit)

    def delete_conversation(self, conv_id: str):
        self.memory.delete_conversation(conv_id)

    def get_all_memories(self):
        return self.memory.get_all_memories()

    def remember(self, content: str, category: str = "general"):
        return self.memory.store.remember(content, category=category)

    def forget(self, key: str):
        self.memory.forget(key)
