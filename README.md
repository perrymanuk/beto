# Radbot: Peronal AI Agent
(Beto)

An AI agent designed with a unique '90s SoCal influence. Beto blends practical functionality with a laid-back, knowledgeable persona. It can manage smart home devices via Home Assistant, access external information using various tools, and retain context from past interactions. While capable and efficient, it occasionally reflects a nostalgic appreciation for '90s tech and culture, adding a distinct character to interactions.

<p align="center">
  <img src="img/radbot.png" alt="RadBot">
</p>

### General Info

*   **`get_current_time`**: Fetches the current time for a specified city, or defaults to UTC if you don't name one. Simple, right?
*   **`get_weather`**: Grabs the weather report for any city you ask about. Don't leave home without knowing the conditions, man.
*   **`web_search`**: Performs a general web search. Handy for quick lookups.

### Home Assistant Control

*   **`search_ha_entities`**: Helps me figure out which specific light, switch, or device you're talking about in your Home Assistant setup. Gotta find the right one first.
*   **`list_ha_entities`**: Shows me all the connected gadgets and sensors in your Home Assistant. Like flipping through a catalog of your smart home.
*   **`get_ha_entity_state`**: Checks the current status or readings from a specific Home Assistant device. Is the light on? What's the temperature?
*   **`turn_on_ha_entity`**: Instructs a Home Assistant device to turn itself ON.
*   **`turn_off_ha_entity`**: Tells a Home Assistant device to power OFF.
*   **`toggle_ha_entity`**: Flips the current state of a device. If it's off, it goes on; if it's on, it goes off.

### File System Interaction

*   **`list_files`**: Lists the files and folders inside a specified path. See what's cruisin' in a directory.
*   **`read_file`**: Reads and returns the content of a file. Like opening a text file on your computer.
*   **`get_file_info`**: Gets details about a file or directory, like its size or type.
*   **`write_file`**: Writes new content to a file, or appends to an existing one.
*   **`copy_file`**: Duplicates files or directories from one spot to another.
*   **`move_file`**: Moves files or directories, which can also be used to rename them.
*   **`delete_file`**: Removes files or directories permanently. Handle with care!
*   **`edit_file_func`**: Modifies a file by applying a list of text replacements. Like using `sed` but safer.

### Web & Search Tools

(Crawl4AI tools are for ingesting and querying specific web content into a knowledge base)

*   **`crawl4ai_ingest_and_read`**: Fetches content from a web page, lets me read it immediately, and also saves it in a knowledge base for later.
*   **`crawl4ai_ingest_url`**: Fetches content from one or more URLs and stores it in the knowledge base. Good for building up info without cluttering the conversation.
*   **`crawl4ai_query`**: Searches through the web content previously saved in the knowledge base using your search terms.
*   **`crawl4ai_two_step`**: Reads a main page, finds links on it, and then fetches the content from those linked pages too. A deep dive.
*   **`call_search_agent`**: Uses a specialized agent (powered by Tavily) for web search. Good for more focused queries.

### Task Management (Todos)

*   **`add_task`**: Adds a new task item to a specified project list. Helps keep track of things to do.
*   **`complete_task`**: Marks a task as finished. Check!
*   **`remove_task`**: Deletes a task from the list entirely. Poof, it's gone.
*   **`list_projects`**: Shows all the different project lists you've created.
*   **`list_project_tasks`**: Lists all the tasks specifically for one project.
*   **`list_all_tasks`**: Gathers and lists all tasks from all projects. Tasks are sorted with "In Progress" at the top, followed by "Backlog" and "Done".
*   **`update_task`**: Modifies an existing task (description, status, project, etc.).
*   **`update_project`**: Renames an existing project.

### Calendar Management (Google Calendar)

*   **`list_calendar_events_wrapper`**: Shows upcoming events from your Google Calendar. Peep the schedule, man.
*   **`create_calendar_event_wrapper`**: Adds a new event to your Google Calendar. Lock in that surf session or meeting.
*   **`update_calendar_event_wrapper`**: Changes details of an existing calendar event. Like editing the time or description.
*   **`delete_calendar_event_wrapper`**: Removes an event from your Google Calendar. Zap that unwanted meeting!
*   **`check_calendar_availability_wrapper`**: Checks free/busy times on calendars. Find out when you can totally chill or gotta jam.

### Memory & Recall

*   **`search_past_conversations`**: Searches back through our previous chats to find relevant info. Helps me remember context.
*   **`store_important_information`**: Allows me to save specific facts or preferences you tell me for future reference.

### Web Interface (UI)

The RadBot web interface features an i3-inspired tiling layout, allowing you to manage multiple panels side-by-side.

*   **Tiling Panels:**
    *   **Chat:** The main conversation area.
    *   **Sessions:** View and manage your chat history sessions.
    *   **Tasks:** View and filter your todo tasks.
    *   **Events:** View and filter the internal agent events (tool calls, transfers, etc.).
*   **Input Commands:**
    *   Prefix messages with `/` to execute built-in commands (e.g., `/tasks`, `/help`, `/clear`).
    *   Prefix messages with `#` followed by a space (`# `) to save the text directly to your memory for future recall.

### Input Prefixes & Commands

*   **`/`**: Use the slash prefix for built-in commands (e.g., `/tasks`, `/help`, `/clear`). Type `/` in the input for suggestions.
*   **`# `**: Use the hash prefix followed by a space (`# `) to save the text directly to your memory.
*   **`/claude`**: Send text directly to Claude or use templated prompts defined in `config.yaml`. Examples:
    - Direct: `/claude What's the capital of France?`
    - Template: `/claude:pr-review PR_NUM="123" GH_REPO="https://github.com/org/repo"` (fills in variables in the template)

### Specialized Agents Architecture

RadBot features a multi-agent architecture with specialized agents that have focused toolsets, reducing token usage and improving performance:

*   **`call_search_agent`**: (See Web & Search Tools) - Specialized for web search tasks
*   **`call_code_execution_agent`**: Executes Python code securely. Like having a mini-IDE built-in.
*   **`call_scout_agent`**: Researches technical topics using various sources (web, docs, code repos). Your personal research assistant.
*   **`call_axel_agent`**: Implements code and technical solutions based on specifications from Scout. Features a dynamic worker system that can distribute implementation tasks across specialized "thing" agents for parallel execution of code implementation, documentation, and testing.

### System Operations (Requires Caution)

*   **`execute_shell_command`**: **(Advanced - Use with Extreme Caution)** This tool can execute arbitrary shell commands. It bypasses normal safety checks and should only be used if you fully understand the security implications.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/perrymanuk/radbot.git
   cd radbot
   ```

2. Set up your environment:
   ```
   make setup
   ```

3. Configure the application:
   ```
   cp config.yaml.example config.yaml
   # Edit config.yaml with your API keys, model settings, and tool configurations
   ```
   RadBot uses `config.yaml` for most settings, including API keys, model preferences, and tool enablement.

## Usage

Run the web interface (with MCP filesystem support):
```
# Optional: Set the root directory for filesystem access
export MCP_FS_ROOT_DIR=/path/to/accessible/directory

# Run the web interface
make run-web
```

## Development

- Run tests: `make test`
- Run unit tests only: `make test-unit`
- Run integration tests only: `make test-integration`
- Run a specific test: `pytest tests/path/to/test_file.py::TestClass::test_method`
- Format code: `make format`
- Lint code: `make lint`

## Project Structure

- `/radbot/agent`: Core agent logic and definitions
- `/radbot/tools`: Tool implementations (time, weather, etc.)
- `/radbot/memory`: Memory system with Qdrant integration
- `/radbot/cli`: Command-line interfaces and runners
- `/docs/implementation`: Implementation documentation
- `/tests`: Unit and integration tests

## Documentation

See the `docs/implementation` directory for detailed documentation on each feature.

## License

MIT
