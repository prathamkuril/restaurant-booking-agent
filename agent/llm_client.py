"""
Ollama/Llama3 Integration Module.

Provides a wrapper for interacting with the Llama3 model via Ollama,
with streaming support and error handling.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Union, Optional, AsyncIterator
import logging

logger = logging.getLogger(__name__)


class LlamaClient:
    """Client for interacting with Llama3 via Ollama."""
    
    def __init__(self, model_name: str = "llama3", temperature: float = 0.7):
        """
        Initialize Llama3 client.
        
        Args:
            model_name: Name of the Ollama model to use
            temperature: Temperature for response generation (0-1)
        """
        self.model = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434"
        )
        logger.info(f"Initialized Llama3 client with model: {model_name}")
    
    async def ainvoke(
        self, 
        messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    ) -> str:
        """
        Invoke the model asynchronously.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Model response as string
        """
        try:
            response = await self.model.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking Llama3: {str(e)}")
            raise
    
    async def astream(
        self, 
        messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    ) -> AsyncIterator[str]:
        """
        Stream responses from the model.
        
        Args:
            messages: List of messages in the conversation
            
        Yields:
            Chunks of the model response
        """
        try:
            async for chunk in self.model.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming from Llama3: {str(e)}")
            raise
    
    def invoke(
        self, 
        messages: List[Union[SystemMessage, HumanMessage, AIMessage]]
    ) -> str:
        """
        Invoke the model synchronously.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            Model response as string
        """
        try:
            response = self.model.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error invoking Llama3: {str(e)}")
            raise