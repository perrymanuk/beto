# ADK 0.4.0 API Changes

This document outlines key API changes between ADK 0.3.0 and ADK 0.4.0 that impact our codebase. Understanding these changes is crucial for maintaining compatibility and properly handling events in the web interface.

## Event Structure Changes

### Model Response Events

In ADK 0.4.0, the structure of model response events has changed significantly:

#### ADK 0.3.0 (Old):
```python
event.content.text  # Direct text content
event.is_final_response()  # Method to check if response is final
```

#### ADK 0.4.0 (New):
```python
event.message.content  # Can be a string or an object with parts
event.message.content.parts[0].text  # Text content in parts
event.message.end_turn  # Boolean property indicating if this is the final response
event.is_final_response  # Can be a property instead of a method in some event types
```

### Function Tool Events

The structure of function tool events has also changed:

#### ADK 0.3.0 (Old):
```python
event.tool_name  # Name of the tool
event.input  # Input arguments
event.output  # Return value
```

#### ADK 0.4.0 (New):
```python
event.function_call.name  # Name of the function
event.function_call.args  # Arguments as an object
event.tool_calls[0].name  # Alternative structure
event.tool_calls[0].args  # Arguments in alternative structure

# Function responses:
event.function_response.name  # Name of the function
event.function_response.response  # Return value
event.tool_results[0].name  # Alternative structure
event.tool_results[0].output  # Output in alternative structure
```

## FunctionTool Parameter Changes

FunctionTool parameter handling has changed in ADK 0.4.0:

#### ADK 0.3.0 (Old):
```python
from google.adk.tools import FunctionTool

# Parameters could be a simple dict
tool = FunctionTool(
    name="my_tool",
    description="A tool that does something",
    parameters={
        "param1": "string",
        "param2": "integer"
    },
    fn=my_function
)
```

#### ADK 0.4.0 (New):
```python
from google.adk.tools import FunctionTool

# Parameters must use JSON Schema format
tool = FunctionTool(
    name="my_tool",
    description="A tool that does something",
    parameters={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1"]
    },
    fn=my_function
)
```

## Content Structure Changes

The structure of Content objects has also changed:

#### ADK 0.3.0 (Old):
```python
from google.adk.type import Content

content = Content(text="Hello, world!")
```

#### ADK 0.4.0 (New):
```python
from google.genai.types import Content, Part

content = Content(
    parts=[Part(text="Hello, world!")],
    role="user"  # Role is now required
)
```

## Event Detection and Processing

To properly handle events in ADK 0.4.0, our code needs to:

1. Check for both callable methods and properties (e.g., `is_final_response` can be either)
2. Look for the new message structure first (e.g., `event.message.content`)
3. Handle multiple content formats (string, object with text, object with parts)
4. Check `message.end_turn` as an alternative to `is_final_response`

## Common Issues and Fixes

### Issue 1: Final Response Detection

The method for detecting final responses has changed.

**Fix**: Check both property and method forms:
```python
is_final = False
if hasattr(event, 'is_final_response'):
    if callable(getattr(event, 'is_final_response')):
        is_final = event.is_final_response()
    else:
        is_final = event.is_final_response
elif hasattr(event, 'message') and hasattr(event.message, 'end_turn'):
    is_final = event.message.end_turn
```

### Issue 2: Content Extraction

Extracting content from events works differently.

**Fix**: Handle multiple content structures:
```python
text = ""
# Check for message.content (ADK 0.4.0 primary structure)
if hasattr(event, 'message') and hasattr(event.message, 'content'):
    if isinstance(event.message.content, str):
        text = event.message.content
    elif hasattr(event.message.content, 'text'):
        text = event.message.content.text
    elif hasattr(event.message.content, 'parts'):
        for part in event.message.content.parts:
            if hasattr(part, 'text'):
                text += part.text

# Fallback to direct content
if not text and hasattr(event, 'content'):
    # Similar checks for event.content
```

### Issue 3: Tool Parameters

Tool parameters must now use JSON Schema.

**Fix**: Update all tool definitions:
```python
# Convert simple parameter definitions to JSON Schema
parameters = {
    "type": "object",
    "properties": {
        # Convert each parameter to a property
        "name": {"type": "string"},
        "count": {"type": "integer"},
    },
    "required": ["name"]  # List required parameters
}
```

## Troubleshooting

When experiencing issues with event handling:

1. Add detailed logging to see event structures: 
   ```python
   logger.info(f"Event attributes: {dir(event)}")
   ```

2. Log event types to understand what you're receiving:
   ```python
   logger.info(f"Event types: {[type(e).__name__ for e in events]}")
   ```

3. Check for the availability of both old and new structures:
   ```python
   if hasattr(event, 'message'):
       logger.info(f"message.content type: {type(event.message.content)}")
   if hasattr(event, 'content'):
       logger.info(f"content type: {type(event.content)}")
   ```

## Resources

- [Official ADK 0.4.0 Migration Guide](https://google.github.io/adk-docs/migration-guide)
- [ADK 0.4.0 Release Notes](https://github.com/google/adk-python/releases)