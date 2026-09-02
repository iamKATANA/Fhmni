class ConversationMemory:

    def __init__(self, max_messages=12):
        self.messages = []
        self.max_messages = max_messages

    def add_user(self, message):
        self.messages.append({
            "role": "user",
            "content": message
        })
        self._limit()

    def add_assistant(self, message):
        self.messages.append({
            "role": "assistant",
            "content": message
        })
        self._limit()

    def get(self):
        return self.messages.copy()

    def clear(self):
        self.messages.clear()

    def _limit(self):
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]