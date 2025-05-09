# Claude Templates Command

The `/claude` command feature allows users to quickly send predefined prompts to Claude with the ability to fill in variables.

## Overview

This feature enables users to create templated prompts in the YAML config and access them with a slash command like `/claude:template-name` or `/claude template-name`. Variables in templates can be filled in by providing key-value pairs in the command arguments.

## Implementation Details

### Configuration

Add a `claude_templates` section to your `config.yaml` file:

```yaml
claude_templates:
  # Basic template without variables
  init: "You are my coding assistant. Help me brainstorm this project."
  
  # Template with variables
  pr-review: "I want you to review PR $PR_NUM for the repository $GH_REPO. Focus on code quality, security issues, and performance."
  
  # Template with multiple variables
  analyze: "Analyze the $LANGUAGE code in $REPO focusing on $ASPECT aspects."
```

### Usage

There are three ways to use the Claude command:

1. **Direct text**: `/claude what is the capital of France?` - Sends text directly to Claude
2. **Colon template syntax**: `/claude:template-name [args]` - Uses a specific template with optional arguments
3. **Space template syntax**: `/claude template-name [args]` - Alternative way to use templates

For templates with variables, provide key-value pairs:
```
/claude:pr-review PR_NUM="122" GH_REPO="https://github.com/org/repo"
```

The command will replace `$PR_NUM` with "122" and `$GH_REPO` with "https://github.com/org/repo" in the template.

### Example Use Cases

1. **Code Reviews**: 
   ```
   /claude:pr-review PR_NUM="122" GH_REPO="https://github.com/org/repo"
   ```

2. **Initial Coding Setup**:
   ```
   /claude:init
   ```

3. **Code Analysis**:
   ```
   /claude:analyze LANGUAGE="Python" REPO="backend-api" ASPECT="security"
   ```

4. **Direct Question**:
   ```
   /claude What's the difference between synchronous and asynchronous programming?
   ```

## Technical Implementation

The feature consists of:

1. A configuration schema addition for `claude_templates`
2. The `/claude` command in the web UI commands.js module
3. An API endpoint to expose templates from the config
4. Template variable processing logic

## API Endpoint

The `/api/claude-templates` endpoint returns all available templates from the configuration.

## Command Processing

The command handler:
1. Fetches templates from the API
2. Extracts the template name and arguments
3. Processes any key=value pairs to replace variables in the template
4. Sends the resulting message to the agent