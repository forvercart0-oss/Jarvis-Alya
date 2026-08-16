from memory.manager import MEMORY_CATEGORIES, MemoryManager


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

    def get_memory_by_id(self, memory_id: str):
        return self.memory.get_memory_by_id(memory_id)

    def remember(self, content: str, category: str = "general"):
        return self.memory.remember(content, category=category)

    def forget(self, key: str):
        self.memory.forget(key)

    def delete_by_id(self, memory_id: str) -> bool:
        return self.memory.delete_memory_by_id(memory_id)

    def clear_all(self) -> int:
        return self.memory.clear_all_memories()

    def get_stats(self) -> dict:
        return self.memory.get_memory_stats()

    def categories(self):
        return list(MEMORY_CATEGORIES)

    def retrieve_relevant(self, query: str, limit: int = 5):
        return self.memory.retrieve_relevant(query, limit)
