# OpenAI client integration for chatbot functionality
import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def chat_with_openai(messages, system_prompt=None):
    """
    Generate a chat response using OpenAI's API.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        system_prompt: Optional system prompt to prepend
        
    Returns:
        Generated response content
    """
    try:
        # Prepare messages with optional system prompt
        chat_messages = []
        if system_prompt:
            chat_messages.append({"role": "system", "content": system_prompt})
        chat_messages.extend(messages)
        
        response = openai.chat.completions.create(
            model="gpt-5",  # the newest OpenAI model is "gpt-5"
            messages=chat_messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"Failed to generate chat response: {e}")

def upload_file_to_openai(file_path, purpose="assistants"):
    """
    Upload a file to OpenAI for use in chat conversations.
    
    Args:
        file_path: Path to the file to upload
        purpose: Purpose of the file upload (default: "assistants")
        
    Returns:
        OpenAI file ID
    """
    try:
        with open(file_path, "rb") as file:
            response = openai.files.create(
                file=file,
                purpose=purpose
            )
        return response.id
    except Exception as e:
        raise Exception(f"Failed to upload file to OpenAI: {e}")

def get_file_from_openai(file_id):
    """
    Retrieve file information from OpenAI.
    
    Args:
        file_id: OpenAI file ID
        
    Returns:
        File information
    """
    try:
        response = openai.files.retrieve(file_id)
        return response
    except Exception as e:
        raise Exception(f"Failed to retrieve file from OpenAI: {e}")

def delete_file_from_openai(file_id):
    """
    Delete a file from OpenAI.
    
    Args:
        file_id: OpenAI file ID to delete
        
    Returns:
        Deletion confirmation
    """
    try:
        response = openai.files.delete(file_id)
        return response
    except Exception as e:
        raise Exception(f"Failed to delete file from OpenAI: {e}")