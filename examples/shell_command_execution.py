#!/usr/bin/env python3
"""Example script demonstrating the shell command execution feature.

This script shows how to use the shell command execution tool in both
strict mode (default) and allow-all mode.

Usage:
    python -m examples.shell_command_execution
"""

import asyncio
import logging
from typing import Dict, Any

import google.generativeai as genai
from google.ai.generativelanguage import Part, FunctionResponse

from radbot.config.config_manager import ConfigManager
from radbot.tools.shell_tool import get_genai_shell_tool, handle_shell_function_call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run the shell command execution example."""
    # Load configuration
    config_manager = ConfigManager()
    api_key = config_manager.get("GOOGLE_API_KEY")
    model_name = config_manager.get("GEMINI_MODEL_NAME", "gemini-1.5-pro")

    # Configure the Gemini model
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model_name)

    # Get the shell tool in strict mode (default)
    # Use get_genai_shell_tool to get the GenAI SDK version of the tool
    shell_tool = get_genai_shell_tool(strict_mode=True)

    # Example prompt for listing files
    prompt = "List the files in the current directory."
    
    logger.info(f"Sending prompt: {prompt}")
    
    # Generate a response with the shell tool
    response = model.generate_content(
        prompt,
        tools=[shell_tool],
    )
    
    # Check if the response contains function calls
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "content") and candidate.content:
            content = candidate.content
            if hasattr(content, "parts"):
                for part in content.parts:
                    if hasattr(part, "function_call"):
                        function_call = part.function_call
                        logger.info(f"Function call detected: {function_call.name}")
                        
                        # Handle the function call
                        result = await handle_shell_function_call(
                            function_name=function_call.name,
                            arguments=function_call.args,
                            strict_mode=True,  # Use strict mode
                        )
                        
                        logger.info(f"Command result: {result}")
                        
                        # Send the result back to the model
                        function_response = Part(
                            function_response=FunctionResponse(
                                name=function_call.name,
                                response=result,
                            )
                        )
                        
                        # Get the final response from the model
                        final_response = model.generate_content(
                            [response, function_response],
                        )
                        
                        logger.info(f"Final response: {final_response.text}")
    
    # Example of using allow-all mode (SECURITY RISK)
    logger.info("\n--- Allow All Mode Example (SECURITY RISK) ---")
    
    # Get the shell tool in allow-all mode
    # Use get_genai_shell_tool to get the GenAI SDK version of the tool
    shell_tool_unrestricted = get_genai_shell_tool(strict_mode=False)
    
    # Example prompt for a command not in the allow-list
    prompt = "Check the disk space usage with df -h."
    
    logger.info(f"Sending prompt in allow-all mode: {prompt}")
    
    # Generate a response with the unrestricted shell tool
    response = model.generate_content(
        prompt,
        tools=[shell_tool_unrestricted],
    )
    
    # Process the response as before
    if hasattr(response, "candidates") and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, "content") and candidate.content:
            content = candidate.content
            if hasattr(content, "parts"):
                for part in content.parts:
                    if hasattr(part, "function_call"):
                        function_call = part.function_call
                        logger.info(f"Function call detected: {function_call.name}")
                        
                        # Handle the function call in allow-all mode
                        result = await handle_shell_function_call(
                            function_name=function_call.name,
                            arguments=function_call.args,
                            strict_mode=False,  # Use allow-all mode
                        )
                        
                        logger.info(f"Command result: {result}")
                        
                        # Send the result back to the model
                        function_response = Part(
                            function_response=FunctionResponse(
                                name=function_call.name,
                                response=result,
                            )
                        )
                        
                        # Get the final response from the model
                        final_response = model.generate_content(
                            [response, function_response],
                        )
                        
                        logger.info(f"Final response: {final_response.text}")


if __name__ == "__main__":
    asyncio.run(main())
