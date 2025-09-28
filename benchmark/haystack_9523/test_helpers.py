def doc_to_string(documents) -> str:
    return "documents processed"

class MockChatGenerator:
    def run(self, messages, tools=None, **kwargs):
        from haystack.dataclasses import ChatMessage
        return {"replies": [ChatMessage.from_assistant("Mocked final answer.")]}