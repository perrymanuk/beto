Filesystem Access for Python ADK
1. Goal

To integrate essential filesystem access capabilities (read, write, edit, copy, delete, list, get info, search) directly into the Python Agent Development Kit (ADK), allowing agents to interact with the local filesystem without requiring external processes or servers.

2. Motivation

Avoid the operational overhead, complexity, and potential inter-process communication challenges associated with managing a separate filesystem server process (like the Model Context Protocol server). Achieve tighter integration and potentially better performance for filesystem operations within the ADK's execution environment.

3. Reference/Inspiration

The Model Context Protocol (MCP) Filesystem Server (https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) provides a useful set of defined tools and features for filesystem interaction via a protocol. While we are not using the server itself, the tool definitions (read_file, write_file, edit_file, etc.) and the pragmatic implementation approach for edit_file serve as valuable references.

4. Proposed Approach

Implement the filesystem interaction logic directly within the Python ADK codebase using Python's standard libraries (os, shutil, built-in file I/O, difflib). This functionality will be exposed to agents either as native ADK functions or, preferably, as a set of internal "filesystem" tools managed by the ADK's existing tool execution mechanism.

5. Functional Requirements (Supported Operations / Tools)

The ADK should provide the following capabilities to agents via a defined interface (e.g., adk.tools.filesystem.read_file):

read_file(path: str) -> str: Reads the entire content of a specified file, returning it as a string (assuming text files, handle encoding, likely UTF-8).
write_file(path: str, content: str, overwrite: bool = False): Writes content to a specified file. Should handle creating new files and optionally overwriting existing ones.
edit_file(path: str, edits: List[Dict[str, str]], dry_run: bool = False) -> str: Edits a file by applying a list of changes. Each edit is specified as a dictionary {"oldText": "...", "newText": "..."}. The dry_run parameter allows previewing changes as a diff without applying them. Returns a git-style diff string.
copy(source_path: str, destination_path: str): Copies a file or directory from a source path to a destination path. Should handle both files and directories (recursively).
delete(path: str): Deletes a file or directory at the specified path. Should handle both files and non-empty directories (recursively).
list_directory(path: str) -> List[str]: Lists the names of files and directories within a specified directory. Could optionally include type indicators ([FILE], [DIR]).
get_info(path: str) -> Dict: Retrieves metadata about a file or directory, such as size, creation time, modified time, and type.
(Consider) search(path: str, pattern: str, exclude_patterns: List[str] = None) -> List[str]: Recursively searches for files or directories within a path matching a pattern, with optional exclusions.
6. Technical Implementation Details (in Python)

Language & Libraries: Python, using os, shutil, io, and difflib (or a similar diffing library).
Core Security Layer (Mandatory):
Allowed Directories Configuration: The ADK must be configured with a list of absolute base paths that agents are permitted to access.
Path Validation Function: A critical internal function must validate every path provided by an agent before any filesystem operation is attempted. This function must:
Resolve relative paths and symlinks (os.path.abspath(), os.path.realpath()).
Verify that the resolved, canonical path is safely within one of the configured allowed base paths.
Raise a PermissionError or similar exception if the path is not within an allowed directory.
Principle of Least Privilege: The ADK process should run with the minimum possible operating system permissions.
Operation Implementations:
Map each functional requirement to the appropriate Python standard library calls.
Wrap each library call with the path validation logic.
Implement robust try...except blocks to catch filesystem-specific errors and provide informative errors to the agent.
edit_file Implementation (apply_file_edits function):
Read the original file content.
Normalize line endings (\r\n to \n).
Iterate through the provided edits ({"oldText": "...", "newText": "..."}).
For each edit:
Normalize line endings for oldText and newText.
Attempt an exact string replacement of the first occurrence of normalized_oldText.
If an exact match is not found, fall back to a line-by-line comparison (splitting content and oldText by \n). Iterate through file lines, checking if a sequence of lines matches the oldText lines when compared whitespace-insensitively (line.strip()).
If a line-based match is found, apply the replacement. Implement heuristics to preserve the original indentation of the first matched line and potentially apply relative indentation to subsequent new lines.
If no match is found (exact or line-based), raise an error for that specific edit.
After attempting all edits, use a Python diffing library (difflib.unified_diff) to generate a diff string between the original content and the modified content.
If dry_run is False, write the modified content back to the file (consider atomic writes).
Return the generated diff string.
Concurrency: If multiple agents can modify the same files concurrently, implement file locking mechanisms (e.g., using fcntl or msvcrt).
Error Reporting: Standardize the format of errors returned to the agent.
7. Advantages

Avoids the need to deploy and manage a separate filesystem server process.
Potentially lower latency for filesystem operations.
Simplified deployment model for the ADK itself.
Full control over the implementation and security layer.
The edit_file approach using oldText/newText and returning diffs is token-efficient for LLM interactions and leverages a proven pattern.
8. Disadvantages / Challenges

Significant Development Effort: Implementing all operations, especially the robust edit_file logic (even with a pragmatic approach) and the critical security layer, is complex.
Security Risk: Incorrect implementation of path validation is a major security vulnerability, even within a sandbox.
Complexity within ADK: Adds substantial logic and dependencies into the ADK's core.
Concurrency Management: Implementing reliable file locking adds complexity.
