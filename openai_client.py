# OpenAI client integration for chatbot functionality
import json
import os
import time
from openai import OpenAI

# the newest OpenAI model is "gpt-5" which was released August 7, 2025.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client with timeout configuration
openai = None
if OPENAI_API_KEY:
    openai = OpenAI(api_key=OPENAI_API_KEY, timeout=30.0)

def chat_with_openai(messages, system_prompt=None, model="gpt-5", max_retries=3):
    """
    Generate a chat response using OpenAI's API with retry logic.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        system_prompt: Optional system prompt to prepend
        model: Model to use (default: gpt-5)
        max_retries: Maximum number of retry attempts
        
    Returns:
        Generated response content
    """
    # Check if OpenAI is available
    if not openai:
        raise RuntimeError("OpenAI API key is not configured")
    
    # Prepare messages with optional system prompt
    chat_messages = []
    if system_prompt:
        chat_messages.append({"role": "system", "content": system_prompt})
    chat_messages.extend(messages)
    
    for attempt in range(max_retries):
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=chat_messages,
                max_tokens=1000,
                temperature=0.7,
                timeout=30.0
            )
            return response.choices[0].message.content
            
        except Exception as e:
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = (2 ** attempt) + 1
                time.sleep(wait_time)
                continue
            raise Exception(f"Failed to generate chat response after {max_retries} attempts: {e}")

def upload_file_to_openai(file_path, purpose="assistants"):
    """
    Upload a file to OpenAI for use in chat conversations.
    
    Args:
        file_path: Path to the file to upload
        purpose: Purpose of the file upload (default: "assistants")
        
    Returns:
        OpenAI file ID
    """
    # Check if OpenAI is available
    if not openai:
        raise RuntimeError("OpenAI API key is not configured")
        
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
    # Check if OpenAI is available
    if not openai:
        raise RuntimeError("OpenAI API key is not configured")
        
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
    # Check if OpenAI is available
    if not openai:
        raise RuntimeError("OpenAI API key is not configured")
        
    try:
        response = openai.files.delete(file_id)
        return response
    except Exception as e:
        raise Exception(f"Failed to delete file from OpenAI: {e}")