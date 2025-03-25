# Langchain, Langgraph, CrewAI here 

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

SONNET_3_7_MODEL = "claude-3-7-sonnet-20250219"

def get_client():
    client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    return client

def get_completion(claude_format):
    client = get_client()
    try:
        # Extract system and messages from the input dictionary
        system = claude_format["system"]
        messages = claude_format["messages"]
        
        completion = client.messages.create(
            model=SONNET_3_7_MODEL,
            system=system,  # Pass system as top-level parameter
            messages=messages,  # Pass the messages list
            max_tokens=1024,
        )
        # Extract text from response
        if completion.content and len(completion.content) > 0:
            return completion.content[0].text
        return "I couldn't generate a proper response."
    except Exception as e:
        return f"Error: {str(e)}"
    

if __name__ == "__main__":
    messages = [
        {"role": "user", "content": "Hello, Claude"}
    ]
    print('here')
    message =   get_completion(messages)
    print(message)