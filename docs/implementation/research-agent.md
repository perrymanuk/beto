Implementation Plan: Technical Research Sub-Agent using Google Agent Development Kit (ADK)1. IntroductionThis document outlines a comprehensive plan for developing and integrating a specialized technical research sub-agent using Google's Agent Development Kit (ADK). The primary goal of this sub-agent is to assist with technical implementation research by interacting with various tools, including web scraping utilities, internal Retrieval-Augmented Generation (RAG) systems, and GitHub repositories. Furthermore, the agent is intended to facilitate "rubber ducky" design sessions, acting as a sounding board for technical architecture discussions.The sub-agent will be designed as a component within a larger multi-agent system, intended to be invoked by or receive tasks delegated from a primary coordinating agent. This plan details the necessary prerequisites, the phased development of the sub-agent, its integration with the main agent, and strategies for local testing. It provides context, code examples, and explanations suitable for a mid-level engineer to implement the feature.The Agent Development Kit (ADK) is selected as the framework for this implementation. ADK is an open-source, code-first Python toolkit designed by Google to simplify the development, evaluation, and deployment of sophisticated AI agents and multi-agent systems. It offers flexibility, modularity, and features specifically suited for building complex agentic workflows, including multi-agent hierarchies and rich tool integration. While optimized for the Google Cloud ecosystem, particularly Gemini models and Vertex AI deployment, ADK is designed to be model-agnostic and deployment-agnostic.2. Prerequisites and SetupBefore beginning the implementation, ensure the following prerequisites are met and the development environment is correctly configured. This setup provides the foundation for building and running ADK-based agents locally.
Google Cloud Project: A Google Cloud project is required. Ensure billing is enabled for the project, and the Vertex AI API is enabled. ADK is optimized for Google Cloud, and while it can run elsewhere, leveraging Vertex AI for models and potential deployment is common.
Credentials: Set up Application Default Credentials (ADC) for local development. This typically involves installing the Google Cloud CLI (gcloud) and running gcloud auth application-default login. ADK uses these credentials to access Google Cloud services like Vertex AI models. Unlike some Google AI services, Vertex AI relies on IAM for access control rather than API keys.
Python Environment: A Python version of 3.10 or higher is recommended. It is strongly advised to use a virtual environment to manage dependencies. Create and activate a virtual environment using tools like venv:
Bash# Create a virtual environment
python -m venv.venv
# Activate (example for macOS/Linux)
source.venv/bin/activate
# Or for Windows CMD:.venv\Scripts\activate.bat
# Or for Windows PowerShell:.venv\Scripts\Activate.ps1


Install ADK: Install the Agent Development Kit package using pip within the activated virtual environment:
Bashpip install google-adk

For access to the latest features or bug fixes not yet in a stable release, installation directly from the main GitHub branch is possible, though the stable release is generally recommended.
Project Structure: Create a dedicated directory for the research agent project. A typical structure includes an __init__.py file, an agent.py file for the agent logic, and potentially a .env file for environment variables (though ADC is preferred for credentials).
Bashmkdir research_agent_project
cd research_agent_project
touch __init__.py agent.py.env


3. Phase 1: Building the Research Sub-AgentThis phase focuses on creating the standalone ResearchAgent. This involves defining its core logic using ADK's LlmAgent, crafting its instructions, and integrating the necessary tools for web scraping, internal knowledge base querying, and GitHub interaction.3.1. Defining the Agent (LlmAgent)The core of the sub-agent will be an instance of ADK's LlmAgent class.1 This class leverages a Large Language Model (LLM) for reasoning, planning, and interacting with tools.
Purpose: The agent's primary functions are:

Technical Research: Answering specific technical questions by utilizing provided tools (web scraping, internal RAG, GitHub).
Design Rubber Ducky: Engaging in conversational design discussions, providing feedback, exploring alternatives, and potentially using tools ad-hoc during the conversation to look up relevant information.


Core Logic: The LlmAgent will process user requests (passed from the main agent), determine the necessary steps (which might involve planning or direct tool use), execute those steps using its available tools, and formulate a response.
3.2. Crafting the Agent InstructionThe instruction parameter provided to the LlmAgent is critical for defining its persona, capabilities, and behavior.1 A well-crafted instruction guides the LLM effectively.
Instruction Content: The instruction should clearly state the agent's dual roles and guide its interaction style. Example:
Pythonresearch_agent_instruction = """
You are a specialized AI assistant for technical research and design collaboration.
Your primary goal is to help engineers by:
1.  Researching technical implementations: Use the available tools (web_scraper, internal_knowledge_search, github_repository_search) to find information on specific technical topics, patterns, libraries, or internal standards when asked. Synthesize findings clearly. Always cite sources if possible (e.g., URL for web_scraper, document name for internal_knowledge_search).
2.  Acting as a rubber ducky for technical design: Engage in discussions about software architecture and design proposals. Analyze provided designs, ask clarifying questions, suggest alternatives, discuss trade-offs, and leverage your research tools to ground the discussion in facts or existing patterns. Be collaborative and objective.

When performing research, prioritize using the internal_knowledge_search tool for questions about internal systems or standards. Use github_repository_search for finding code examples or libraries. Use web_scraper for accessing specific public web pages or general public information.

When rubber ducking, actively listen, provide constructive feedback, and use your research tools proactively if needed to verify information or find relevant examples during the conversation.

Your task is typically defined by information passed in the session state, specifically the 'current_research_query' or 'design_context' keys. Access this state to understand the user's request.
"""


Key Elements:

Clearly defines the two main functions (research, rubber ducky).
Explicitly lists available tools and provides guidance on when to use each.
Sets expectations for output (synthesis, citations).
Guides the conversational style for rubber ducking (collaborative, objective, proactive tool use).
Specifies how the agent receives its task input (via session.state).


3.3. Integrating Existing Tools (FunctionTool)ADK allows integrating custom Python functions as tools using the FunctionTool class.1 This involves wrapping the existing functions provided by the user (for web scraping, RAG, GitHub) into FunctionTool objects.

Mechanism: Create a FunctionTool instance for each existing tool function. The func parameter takes the actual Python function, name provides an identifier, and description tells the LLM what the tool does and when to use it.1 The quality of the description is paramount for the LLM to select the correct tool.1


Code Examples (assuming user functions exist):

Web Scraper:
Pythonfrom google.adk.tools import FunctionTool

# Assume user has a function like this:
# def scrape_web(url: str) -> str:...

web_scraper_tool = FunctionTool(
    func=scrape_web, # The user's actual function
    name="web_scraper",
    description="Fetches and returns the textual content from a given public URL. Use this for accessing specific web pages mentioned or for general web research on public information."
    # Potentially add input/output schemas if needed for more complex tools
)


Internal RAG:
Pythonfrom google.adk.tools import FunctionTool

# Assume user has a function/method like this:
# def query_internal_rag(query: str) -> str:...

internal_rag_tool = FunctionTool(
    func=query_internal_rag, # The user's actual function/method
    name="internal_knowledge_search",
    description="Searches internal documentation and knowledge bases (RAG system) using a natural language query. Use this to find information specific to internal projects, standards, or past technical discussions."
)


It is important to recognize that the performance of this tool relies heavily on the underlying RAG system's quality. ADK facilitates calling the tool, but the relevance and accuracy of the results depend entirely on the data sources, chunking strategy, embedding models, and retrieval mechanisms used in the RAG implementation itself. If the RAG tool provides poor results, the research agent's output will suffer, irrespective of the ADK integration.


GitHub Tool: (Assuming a function to search repos)
Pythonfrom google.adk.tools import FunctionTool

# Assume user has a function like this:
# def search_github_repositories(search_query: str, org: str = None) -> list[str]:...
# Or: def get_github_file_content(repo_url: str, file_path: str) -> str:...

github_search_tool = FunctionTool(
    func=search_github_repositories, # User's function
    name="github_repository_search",
    description="Searches for relevant GitHub repositories based on a query, optionally within a specific organization. Use this to find example implementations, libraries, or open-source projects related to a technical topic."
)
# If a function like get_github_file_content exists, create a separate FunctionTool for it.





Tool Definition Summary: A clear mapping between the agent's tools, their purpose (as understood by the LLM), and the underlying implementation is essential.

Tool Name (in ADK)Purpose/Description (for LLM)Underlying Function/API Signatureweb_scraperFetches textual content from a public URL. Use for accessing specific pages or general public web research.scrape_web(url: str) -> strinternal_knowledge_searchSearches internal documentation and knowledge bases (RAG system) using a natural language query. Use for internal projects, standards, or past discussions.query_internal_rag(query: str) -> strgithub_repository_searchSearches GitHub repositories based on a query, optionally within a specific organization. Use for finding examples, libraries, or open-source projects.search_github_repositories(search_query: str, org: str = None) -> list[str](Add other tools here)(Describe purpose clearly for LLM)(Specify function signature)3.4. Attaching Tools to the AgentFinally, assemble the LlmAgent by providing the instruction, description, model, and the list of created FunctionTool instances to the tools parameter.Pythonfrom google.adk.agents import LlmAgent

# Assume tool objects (web_scraper_tool, etc.) are defined as above
# Assume research_agent_instruction is defined as above

research_agent = LlmAgent(
    name="technical_research_agent",
    model="gemini-1.5-pro-latest", # Or another suitable Gemini model like gemini-1.5-flash for speed/cost trade-off
    instruction=research_agent_instruction,
    description="A specialized sub-agent for conducting technical research (web, internal docs, GitHub) and facilitating technical design discussions (rubber ducking).",
    tools=
    # Consider adding output_key='research_summary' to automatically save the main response to state['research_summary'][1]
)
The "rubber ducky" functionality primarily stems from the agent's conversational abilities, guided by the instruction prompt. During these discussions, the agent might dynamically decide to use its research tools based on the conversation flow (e.g., "Let me check our internal docs for the standard pattern you mentioned."). This interaction is less deterministic than a direct research request and relies on the LLM's reasoning capabilities combined with the clarity of the tool descriptions.4. Phase 2: Connecting the Sub-Agent to the Main AgentWith the ResearchAgent defined, the next phase involves integrating it into the existing multi-agent system by establishing it as a sub-agent of the main coordinating agent. This requires defining the hierarchy and choosing a mechanism for the main agent to delegate tasks to the research sub-agent. This plan assumes the main agent is also implemented using ADK. Integrating agents built with different frameworks might require protocols like Agent2Agent (A2A) 2 or custom API layers, which adds significant complexity.4.1. Establishing the HierarchyADK supports multi-agent systems through hierarchical composition. A parent agent can have multiple sub_agents.

Code Example: Instantiate the ResearchAgent (defined in Phase 1) and include it in the sub_agents list when defining the MainAgent.
Pythonfrom google.adk.agents import LlmAgent # Or BaseAgent if main agent is custom

# Assuming research_agent is defined as in Phase 1

# Define the Main Agent (assuming it's also an LlmAgent)
main_agent = LlmAgent(
    name="main_coordinator_agent",
    model="gemini-1.5-pro-latest", # Or the main agent's preferred model
    instruction="You are the main coordinator agent. Handle user requests. If the user requires detailed technical research, needs to brainstorm a technical design, or asks to talk through an architecture, delegate the task to the 'technical_research_agent'.",
    description="Main coordinating agent that orchestrates tasks and delegates to specialized sub-agents.",
    sub_agents=[
        research_agent,
        #... include any other sub-agents the main agent manages
    ]
    #... other main agent configurations (e.g., its own tools)
)

This structure establishes research_agent as a child of main_agent within the ADK system.3

4.2. Choosing a Delegation MechanismThe main agent needs a way to "pass off" tasks to the research sub-agent, particularly for design planning as requested. ADK primarily offers two mechanisms for an LlmAgent parent to delegate to a sub-agent 3:

Option A: LLM-Driven Transfer (transfer_to_agent)

Mechanism: The parent agent's LLM, guided by its instruction and the description of the sub-agent, decides to hand over the conversational control to the sub-agent. It does this by generating a specific function call: transfer_to_agent(agent_name='technical_research_agent'). The ADK framework intercepts this call and shifts the execution focus to the specified sub-agent.3
Pros: Creates a more natural conversational handoff, aligning well with the "pass me off" requirement. Allows the sub-agent to manage the interaction fully during the research or design session.
Cons: Success depends heavily on the parent LLM's ability to correctly interpret instructions and generate the transfer call. Can be less predictable than explicit calls. Requires careful crafting of the parent's instructions and the sub-agent's description. The parent agent relinquishes direct control until the sub-agent completes or transfers back (if configured). Potential error point if the LLM fails to generate the transfer call when appropriate.
Configuration: Update the MainAgent's instruction (as shown in the example above) to explicitly guide it on when to transfer. Ensure the ResearchAgent's description accurately reflects its capabilities so the parent LLM can identify it as the correct target for delegation. Flags like disallow_transfer_to_parent or disallow_transfer_to_peers can control transfer scope if needed.1



Option B: Explicit Invocation (AgentTool)

Mechanism: The ResearchAgent instance is wrapped in an AgentTool. This tool is then added to the MainAgent's tools list. The parent LLM invokes the sub-agent by generating a function call for this tool, similar to how it would use any other tool.3
Pros: Provides a more predictable and controlled execution flow. The parent agent remains in control, invoking the sub-agent explicitly and receiving its results as tool output. Potentially simpler to implement and debug for request-response style interactions.
Cons: Feels less like a conversational "handoff" and more like a function execution. May be less suitable for the extended back-and-forth typical of rubber ducking sessions, as the entire sub-interaction would need to be managed within a single tool execution cycle or require repeated tool calls.
Configuration:
Pythonfrom google.adk.tools import AgentTool
from google.adk.agents import LlmAgent

# Assuming research_agent is defined

research_agent_tool = AgentTool(
    agent=research_agent,
    name="technical_research_and_design_tool",
    description="Use this tool to perform technical research (web, internal docs, GitHub) or to discuss and get feedback on a technical design proposal. Provide the research query or design details as input."
)

main_agent_with_tool = LlmAgent(
    name="main_coordinator_agent",
    model="gemini-1.5-pro-latest", # Or main agent's model
    instruction="You are the main coordinator agent. Handle user requests. Use the 'technical_research_and_design_tool' when the user requires technical research or wants to discuss a design.",
    description="Main coordinating agent using tools for delegation.",
    tools=[
        research_agent_tool,
        #... any other tools the main agent uses directly
    ]
    # The research_agent might still be listed in sub_agents for hierarchy/discovery,
    # but the primary delegation mechanism here is the AgentTool.
)





Recommendation: For the requirement of being "passed off" for design planning and rubber ducking, LLM-Driven Transfer (Option A) appears more suitable. It facilitates a more seamless transition of conversational control, which is beneficial for extended interactions like design discussions. However, this approach demands careful prompt engineering for the MainAgent's instructions to ensure reliable transfers. If initial attempts show unreliable transfers, or if the primary use case shifts towards more discrete research tasks, switching to the more robust Explicit Invocation (AgentTool, Option B) might be preferable. The choice involves a trade-off: Option A prioritizes conversational fluidity, while Option B prioritizes explicit control and predictability.3

4.3. Managing Context Transfer (session.state)Regardless of the delegation method, information (like the specific research topic or the design context) must be passed from the main agent to the sub-agent. ADK uses the session.state object, accessible via the InvocationContext or CallbackContext, for this purpose.3

Parent Agent (Setting Context): Before delegating (either instructing the LLM to transfer or calling the AgentTool), the parent agent's logic (or a preceding tool/callback) should write the necessary input data to session.state.
Python# Conceptual example within the parent agent's logic or a preceding step
# 'context' is an instance of InvocationContext or CallbackContext

user_request = "Let's discuss the architecture for the new notification service."
design_topic = "Architecture for new notification service"
context.state['current_research_query'] = None # Clear or set as needed
context.state['design_context'] = design_topic

# Now, trigger delegation (either via LLM instruction leading to transfer, or by calling the AgentTool)



Sub-Agent (Accessing Context): The ResearchAgent needs to be aware of these state keys. This is typically handled by including instructions in its prompt (as shown in Section 3.2) to look for input in session.state. The agent's internal logic or tools can then access it.
Python# Conceptual access within the ResearchAgent's execution flow
# 'context' is an instance of InvocationContext or CallbackContext

design_info = context.state.get('design_context')
research_query = context.state.get('current_research_query')

if design_info:
    # Initiate rubber ducking logic based on design_info
    pass
elif research_query:
    # Initiate research logic based on research_query
    pass



Sub-Agent (Returning Results): The sub-agent should write its results back to session.state so the parent agent can potentially access them later. If the ResearchAgent uses the output_key parameter (e.g., output_key='final_response'), its main textual response will be automatically saved to that key in the state.1
Python# Conceptual example within the ResearchAgent's logic before finishing
# 'context' is an instance of InvocationContext or CallbackContext

summary_of_discussion = "Discussed pros/cons of queue vs direct call. Recommended queue."
context.state['last_research_results'] = summary_of_discussion # Or research findings
# If output_key='final_response' is set on ResearchAgent, the agent's final message
# is also automatically stored in context.state['final_response']


While session.state provides a straightforward way to share data in this two-agent scenario, it's important to manage state keys carefully. In more complex systems, especially those involving parallel execution (ParallelAgent 3) or long histories, using unique or structured keys (e.g., agent-specific prefixes) is advisable to prevent accidental data overwrites or reliance on stale information.5. Phase 3: Local Testing and EvaluationOnce the ResearchAgent is built and connected to the MainAgent, thorough local testing is crucial before considering deployment. ADK provides tools for interactive testing and debugging, as well as systematic evaluation.5.1. Running the Agent LocallyInteract with the integrated multi-agent system locally to test the delegation logic, context passing, and tool usage.

Using Runner: The Runner class allows programmatic interaction via Python scripts.
Pythonfrom google.adk.runners import Runner

# Assuming main_agent is defined and configured with research_agent as sub-agent
# (using either transfer or AgentTool for delegation)
runner = Runner(agent=main_agent)

print("Starting interaction with main agent...")

# Example interaction likely triggering research sub-agent
user_input_1 = {"query": "Please research the best practices for asynchronous API design using our internal standards."}
print(f"\nUser: {user_input_1['query']}")
output_1 = runner.run(user_input_1)
print(f"Agent: {output_1}") # Output might be from main or sub-agent depending on delegation

# Example interaction likely triggering rubber ducking sub-agent
user_input_2 = {"query": "I'm thinking of using pattern X for service Y. Can we talk through the pros and cons?"}
print(f"\nUser: {user_input_2['query']}")
output_2 = runner.run(user_input_2)
print(f"Agent: {output_2}")

print("\nInteraction finished.")

This allows testing specific input scenarios and observing the output.


Using the Development UI: ADK includes a built-in web-based Development UI. This UI provides a chat interface for more natural conversational testing and offers capabilities to inspect agent events, state changes, and execution steps, which is invaluable for debugging multi-agent interactions. Launching the UI typically involves running a specific command provided by ADK against the agent definition file.

5.2. Basic Evaluation ConceptsWhile comprehensive evaluation is a larger effort, understanding ADK's basic evaluation features is important for future quality assurance.
Purpose: ADK's evaluation tools allow systematic assessment of agent performance against predefined test cases. This involves checking both the final response quality and the step-by-step execution path.
Evaluation Sets: Tests are defined in JSON files (e.g., my_tests.evalset.json) containing inputs and expected outputs or behaviors.
Running Evaluation: The adk eval command-line tool executes these tests against the agent.
Bashadk eval path/to/your/agent/definition path/to/your/evaluation_set.evalset.json


Testing Focus: For this initial implementation, focus on interactive testing using Runner and the Dev UI. This is better suited for debugging the integration aspects: Does the main agent correctly delegate? Is context passed correctly via session.state? Does the sub-agent receive the task and execute? Systematic evaluation using adk eval would be more appropriate later for rigorously testing the ResearchAgent's standalone ability to handle various research queries or use specific tools correctly.
6. Conclusion and Next StepsThis plan provides a structured approach to building a technical research sub-agent using Google's ADK and integrating it with a main agent. Key phases included defining the ResearchAgent with an LlmAgent, wrapping existing functionalities as FunctionTools, establishing the agent hierarchy using sub_agents, exploring delegation mechanisms (LLM-driven transfer vs. AgentTool), managing context via session.state, and outlining local testing procedures.Summary of Plan:
Setup: Configure Google Cloud, credentials, Python environment, and install ADK.
Build Sub-Agent: Define ResearchAgent (LlmAgent), craft its instruction, integrate tools (FunctionTool), and define tool descriptions carefully.
Connect Agents: Add ResearchAgent to MainAgent.sub_agents. Choose and configure a delegation mechanism (recommend LLM-transfer for conversational feel, AgentTool for control). Implement context passing using session.state.
Test Locally: Use Runner and the Dev UI for interactive testing and debugging of the integrated system.
Next Steps:
Implementation: Execute the steps outlined in this plan, paying close attention to instruction/description quality for LLM guidance and tool selection.
Thorough Testing: Conduct extensive interactive testing using various research queries and design discussion scenarios. Debug issues related to delegation, context passing, and tool execution. Consider creating a small set of basic evaluation cases (adk eval) for core research functionalities.
Deployment: Once the agent performs reliably locally, explore deployment options. ADK agents can be containerized and deployed on various platforms like Google Cloud Run or GKE. However, Vertex AI Agent Engine is specifically highlighted as a fully managed, scalable runtime optimized for ADK agents, offering features like built-in testing, release management, and reliability. Utilizing Agent Engine provides a streamlined path to production within the Google Cloud ecosystem, though it implies tighter integration with GCP services compared to self-managed options.
Advanced Orchestration: If workflows become more complex (e.g., requiring a fixed sequence of research steps followed by summarization), investigate ADK's dedicated Workflow Agents (SequentialAgent, ParallelAgent, LoopAgent) for more structured control flow.3
Observability: For production monitoring and deeper debugging, consider integrating observability tools. While specific integrations might vary, frameworks compatible with OpenTelemetry (used by some agent tools like OpenAI Agents SDK) could potentially be integrated for tracing agent behavior.
Remote Communication (Future): If the main agent and research sub-agent need to be deployed as independent services in the future, implementing the Agent2Agent (A2A) protocol 2 or a custom API/RPC layer between them would be necessary to maintain communication. A2A is positioned as an open standard to facilitate such interoperability.
By following this plan, a mid-level engineer should be able to successfully implement the technical research sub-agent feature, providing valuable research and design assistance capabilities within the existing agent system.
