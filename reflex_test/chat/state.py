import reflex as rx
from typing import List

from reflex_test.model import Chat
from . import ai

class ChatMessage(rx.Base):
    message: str
    is_bot: bool = False

class ChatState(rx.State):
    did_submit: bool = False
    messages: List[ChatMessage] = []
    
    @rx.var
    def user_did_submit(self) -> bool:
        return self.did_submit
    
    def on_load(self):
        with rx.session() as session:
            results = session.exec(
                Chat.select()
            ).all()
            print(results)
    
    def append_message(self, message: str, is_bot: bool):
        self.messages.append(ChatMessage(message=message, is_bot=is_bot))
        
    def get_claude_response(self, message: str) -> dict:
        """
        Format messages for Claude API with the correct structure.
        Returns the system prompt and messages separately.
        """
        # System prompt goes as a separate parameter
        system_message = "You are a helpful assistant that can answer questions and help with tasks. Respond in markdown"
        
        # Format the conversation history for Claude
        formatted_messages = []
        for chat_message in self.messages:
            role = 'user'
            if chat_message.is_bot:
                role = 'assistant'  # Bot messages are "assistant", not "system"
            formatted_messages.append({
                "role": role,
                "content": chat_message.message,  # "content", not "message"
            })
        
        return {
            "system": system_message,
            "messages": formatted_messages
        }
        
    async def handle_submit(self, form_data: dict):
        user_message = form_data.get("message")
        if user_message:
            self.did_submit = True
            self.append_message(user_message, False)
            yield
            
            try:
                # Get formatted message structure for Claude
                claude_format = self.get_claude_response(user_message)
                # Pass the entire structure to get_completion
                bot_message = ai.get_completion(claude_format)
                self.did_submit = False
                self.append_message(bot_message, True)
            except Exception as e:
                self.did_submit = False
                self.append_message(f"Sorry, I couldn't process your request: {str(e)}", True)
            
            yield
        
    