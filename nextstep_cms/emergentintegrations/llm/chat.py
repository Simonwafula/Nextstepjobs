import openai

class UserMessage:
    def __init__(self, text: str):
        self.text = text

class LlmChat:
    def __init__(self, api_key: str, session_id: str = None, system_message: str = None):
        openai.api_key = api_key
        self.messages = []
        if system_message:
            self.messages.append({"role": "system", "content": system_message})
        self.session_id = session_id

    def with_model(self, provider: str, model: str):
        self.model = model
        return self

    async def send_message(self, message: UserMessage):
        self.messages.append({"role": "user", "content": message.text})
        response = await openai.ChatCompletion.acreate(
            model=self.model,
            messages=self.messages
        )
        return response["choices"][0]["message"]["content"]
