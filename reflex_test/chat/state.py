import reflex as rx
from typing import List, Optional

from reflex_test.model import ChatSession, ChatSessionMessageModel
from . import ai

class ChatMessage(rx.Base):
    message: str
    is_bot: bool = False

class ChatState(rx.State):
    chat_session: Optional[ChatSession] = None
    not_found: Optional[bool] = None
    did_submit: bool = False
    messages: List[ChatMessage] = []
    
    @rx.var
    def user_did_submit(self) -> bool:
        return self.did_submit
    
    @rx.var
    def session_id(self) -> str:
        return self.router.page.params.get('session_id')
    
    def get_session_id(self) -> int:
        try:
            my_session_id = int(self.router.page.params.get('session_id', '-1'))
        except:
            my_session_id = None
        return my_session_id
    
    def create_new_chat_session(self):
        with rx.session() as db_session:
            obj = ChatSession()
            db_session.add(obj) # prepare to save
            db_session.commit() # actually save
            db_session.refresh(obj)
            self.chat_session = obj
            return obj

    def clear_ui(self):
        self.chat_session = None
        self.not_found = None
        self.did_submit = False
        self.messages = []

    def create_new_and_redirect(self):
        self.clear_ui()
        new_chat_session = self.create_new_chat_session()
        return rx.redirect(f"/chat/{new_chat_session.id}")

    def clear_and_start_new(self):
        self.clear_ui()
        self.create_new_chat_session()
        yield

    def get_session_from_db(self, session_id=None):
        if session_id is None:
            session_id = self.get_session_id()
        # ChatSession.id == session_id
        with rx.session() as db_session:
            sql_statement = sqlmodel.select(
                ChatSession
            ).where(
                ChatSession.id == session_id
            )
            result = db_session.exec(sql_statement).one_or_none()
            if result is None:
                self.not_found = True
            else:
                self.not_found = False
            self.chat_session = result
            messages = result.messages
            for msg_obj in messages:
                msg_txt = msg_obj.content
                is_bot = False if msg_obj.role == "user" else True
                self.append_message_to_ui(msg_txt, is_bot=is_bot)
            
    
    def on_detail_load(self):
        session_id = self.get_session_id()
        reload_detail = False
        if not self.chat_session:
            reload_detail = True
        else:
            """has a session"""
            if self.chat_session.id != session_id:
                reload_detail = True

        if reload_detail:
            self.clear_ui()
            if isinstance(session_id, int):
                self.get_session_from_db(session_id=session_id)

    
    def on_load(self):
        print('run on load')
        if self.chat_session is None: 
            with rx.session() as db_session:
               self.create_new_chat_session()
    
    def insert_message_db(self, content: str, role: str):
        print('insert message db')
        if self.chat_session is None: 
            return
        if not isinstance(self.chat_session, ChatSession):
            return
        with rx.session() as db_session:
            data = {
                "session_id": self.chat_session.id,
                "content": content,
                "role": role
            }
            obj = ChatSessionMessageModel(**data)
            db_session.add(obj)
            db_session.commit()
            print(obj.id)
            self.chat_session = obj
      
    def append_message_to_ui(self, message: str, is_bot: bool):
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
        
    async def handle_submit(self, form_data:dict):
        print('here is our form data', form_data)
        user_message = form_data.get('message')
        if user_message:
            self.did_submit = True
            self.append_message_to_ui(user_message, is_bot=False)
            self.insert_message_db(user_message, role='user')
            yield
            claude_messages = self.get_claude_response(user_message)
            bot_response = ai.get_completion(claude_messages)
            self.did_submit = False
            self.append_message_to_ui(bot_response, is_bot=True)
            print('bot response', bot_response)
            self.insert_message_db(bot_response, role='system')
            yield
        