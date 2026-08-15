DEFAULT_MAX_CONTEXT_CHARS = 10000


class ConversationManager:
    def __init__(self, memory):
        self.memory = memory

    def ensure_conversation(self, conv_id) -> str:
        return self.memory.ensure_conversation(conv_id)

    def add_message(self, conv_id: str, role: str, content: str) -> str:
        return self.memory.add_message(conv_id, role, content)

    def build_messages(self, conv_id: str, user_message: str, max_messages: int = 100, max_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> list[dict]:
        return self.memory.build_messages(conv_id, user_message, max_messages, max_chars)

    def build_messages_with_system(self, conv_id: str, user_message: str, system_prompt: str, max_messages: int = 100, max_chars: int = DEFAULT_MAX_CONTEXT_CHARS) -> list[dict]:
        history = self.memory.get_messages(conv_id, limit=max_messages)
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        total_chars = len(system_prompt) + len(user_message)
        messages.append({"role": "user", "content": user_message})
        for msg in reversed(history):
            if len(messages) >= max_messages + 2:
                break
            content = msg["content"]
            if total_chars + len(content) > max_chars:
                continue
            total_chars += len(content)
            messages.insert(1, {"role": msg["role"], "content": content})
        return messages

    def get_history(self, conv_id: str) -> list[dict]:
        return self.memory.get_history(conv_id)

    def clear_history(self, conv_id: str):
        self.memory.clear_history(conv_id)

    def reset_conversation(self) -> str:
        return self.memory.reset_conversation()
