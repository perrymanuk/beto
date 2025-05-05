# Design Document: Ripgrep Tool Implementation

## 1. Goal

Implement a new tool for the Radbot agent that leverages the `ripgrep` command-line utility to perform fast and efficient searches of the filesystem. This tool will allow the agent to search for specific patterns within files, optionally filtering by file type, excluding directories, and controlling the amount of context surrounding matches.

## 2. Reference Implementation

The design is heavily inspired by the `ripgrep_search` tool found in `ra_aid/tools/ripgrep.py`. This existing implementation provides a robust blueprint for mapping `ripgrep` command options to function arguments, constructing the command, and handling its output.

## 3. Integration with Radbot's Shell Execution

The `ripgrep` tool will utilize Radbot's existing secure shell command execution mechanism provided by the `execute_shell_command` function in `radbot.tools.shell.shell_command.py`. This ensures command execution adheres to Radbot's security policies, including command allow-listing and safe argument handling.

## 4. Tool Definition

A new Python file, likely named `ripgrep_tool.py`, will be created within the `radbot/tools/shell/` directory. This file will contain the tool function and its ADK schema definition.

The tool function, let's call it `ripgrep_search`, will mirror the parameters of the reference implementation to provide flexibility in controlling the `ripgrep` execution:

```python
def ripgrep_search(
    pattern: str,
    *,
    before_context_lines: Optional[int] = None,
    after_context_lines: Optional[int] = None,
    file_type: Optional[str] = None,
    case_sensitive: bool = True,
    include_hidden: bool = False,
    follow_links: bool = False,
    exclude_dirs: Optional[List[str]] = None,
    include_paths: Optional[List[str]] = None,
    fixed_string: bool = False,
) -> Dict[str, Union[str, int, bool]]:
    # ... implementation details ...
    pass
```

An ADK tool schema will be defined to describe this function's name, description, and parameters, allowing the ADK framework to expose it to the language model.

## 5. Command Construction

Inside the `ripgrep_search` tool function, a list of strings representing the `rg` command and its arguments will be dynamically constructed based on the input parameters. This involves:

*   Starting with `["rg"]`.
*   Adding options like `"-B", str(before_context_lines)` if `before_context_lines` is provided.
*   Mapping `file_type` (e.g., "py") to `rg`'s `-t` flag format (e.g., `"-t", "python"`), potentially using a predefined map similar to the reference implementation.
*   Adding flags like `"-i"`, `--hidden`, `--follow`, `-F` based on boolean parameters.
*   Adding exclusion globs (`"--glob", f"!{dir}"`) for default and specified `exclude_dirs`.
*   Appending the search `pattern`.
*   Appending `include_paths` if provided.

## 6. Execution

The constructed command list will be passed to `radbot.tools.shell.shell_command.execute_shell_command`:

```python
result = execute_shell_command(command="rg", arguments=cmd_args, strict_mode=True)
```

**Crucially**, the string `"rg"` must be added to the `ALLOWED_COMMANDS` set in `/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/shell/shell_command.py` to permit its execution in strict mode.

## 7. Output Handling

The `execute_shell_command` function returns a dictionary containing `stdout`, `stderr`, `return_code`, and `error`. The `ripgrep_search` tool function will process this result:

*   Determine success based on `return_code == 0`.
*   Combine or structure the `stdout` and `stderr` for the tool's output.
*   Return a dictionary to the agent including the output, return code, and a boolean indicating success, similar to the reference implementation.
*   Consider truncating the output using a utility function (like `truncate_output` in the reference) before returning it to the agent to conserve token usage, while potentially logging the full output internally.

## 8. File Location

The primary implementation file will be located at:
`/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/shell/ripgrep_tool.py`

Updates to `radbot/tools/shell/shell_command.py` are required to add `rg` to `ALLOWED_COMMANDS`. The tool will also need to be registered, likely in `radbot/tools/__init__.py`.

## 9. Dependencies

This tool depends on the `ripgrep` binary being installed and available in the system's PATH where the Radbot agent is running.
