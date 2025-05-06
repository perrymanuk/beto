# Play: Frontend Event and Tooling Fixes

**Goal:** Improve the RadBot web frontend to correctly display agent messages, structured tool call/result events, and provide access to the list of available tools.

**Problem:**
1.  Agent messages (`model_response` events) are received via WebSocket but not displayed in the main chat feed because the frontend expects them with a different message type (`type: 'message'`).
2.  Structured tool call/result events (`tool_call` events with `function_call`/`function_response` details) are received but not fully parsed and displayed with their specific inputs/outputs in the events panel details.
3.  The frontend has no mechanism to fetch and display the list of available tools.

**Solution:**
1.  **Backend Change:** Add a new FastAPI endpoint (`/api/tools`) in the `radbot` backend to expose the `root_agent`'s tool list.
2.  **Frontend Change (Event Handling):** Modify `app.js` to correctly route `model_response` events to the chat display and enhance event processing to include information necessary for detailed display of tool events.
3.  **Frontend Change (Event Rendering):** Update `app.js`'s event rendering logic (`renderEvents` and `showDetailPanel`) to properly display structured information from tool and message events.
4.  **Frontend Change (Tool List):** (Planned for a follow-up) Add frontend logic to fetch data from the new `/api/tools` endpoint and display it.

**Implementation Plan:**

**Step 1: Create Play Document (`frontend-event-fix.md`)**
*   This document is being created now with the current plan.

**Step 2: Implement Backend Tool Endpoint**
*   **File:** `/Users/perry.manuk/git/perrymanuk/radbot/radbot/web/app.py`
*   **Change:**
    *   Add a function `get_available_tools()` that imports and accesses the `root_agent` to get its `tools` list.
    *   Add a new FastAPI GET endpoint `/api/tools` that calls `get_available_tools()` and returns a JSON representation of the tools. This will involve serializing the tool objects, which might require extracting relevant attributes like `name`, `description`, and `input_schema`.

**Step 3: Implement Frontend Event Handling Fixes**
*   **File:** `/Users/perry.manuk/git/perrymanuk/radbot/radbot/web/static/js/app.js`
*   **Change (in `handleEvents` function):**
    *   Iterate through the received `newEvents`.
    *   If an event's `type` or `category` is 'model_response' and it has a `text` field, call `window.chatModule.addMessage('assistant', event.text)` to display it in the main chat.
    *   Add custom temporary properties (e.g., `_displayType`, `_displayText`, `_detailsContent`) to each event object based on its `type`, `category`, and presence of fields like `tool_name`, `input`, `output`, and `text`. These properties will be used by the rendering functions.
    *   Ensure agent transfer logic continues to function and calls `updateStatusBar()`.
    *   Sort the `events` array by timestamp (newest first) after adding new events.

**Step 4: Implement Frontend Event Rendering Fixes**
*   **File:** `/Users/perry.manuk/git/perrymanuk/radbot/radbot/web/static/js/app.js`
*   **Change (in `renderEvents` function):**
    *   Modify the code that creates event list items to use the `_displayType` and `_displayText` properties for the event title and summary displayed in the list.
*   **Change (in `showDetailPanel` function):**
    *   Within the `if (type === 'event')` block, update the detail rendering logic.
    *   Use the `_displayType` and `_displayText` for the title and summary in the detail panel.
    *   Add conditional rendering based on `item.type` or `item.category` and `item.details.event_type`.
    *   If it's a tool call/result, display `item.tool_name` and format `item.input` or `item.output` using `JSON.stringify` within `<pre>` tags for readability.
    *   If it's a model response, display `item.text` using `marked.parse`.
    *   Use `item._detailsContent` as a fallback for displaying general details if specific fields aren't found.

**Step 5: Frontend Tool List Display (Follow-up)**
*   After the endpoint is added and event handling is fixed, implement fetching from `/api/tools` and displaying the list in the frontend.

**Verification:**
*   After applying changes, run the RadBot web interface.
*   Verify that agent responses appear correctly in the main chat feed.
*   Verify that tool call and tool result events are listed in the Events panel with informative summaries.
*   Verify that clicking on a tool event in the Events panel shows a detail panel with structured `input` or `output` information.
*   Verify that the agent status bar correctly updates on agent transfers.
*   (Once implemented) Verify that the tool list is fetched and displayed.

---
