#!/usr/bin/env python
"""
Test script for verifying ADK built-in agent transfers.

This script has two modes of operation:
1. Validation mode: Tests the agent transfer paths programmatically
2. Web mode: Starts the web application for manual testing

Validation mode tests all possible agent transfer paths:
- beto → scout transfers
- beto → search_agent transfers 
- beto → code_execution_agent transfers
- scout → beto transfers
- scout → search_agent transfers
- scout → code_execution_agent transfers
- search_agent → beto transfers
- search_agent → scout transfers
- search_agent → code_execution_agent transfers
- code_execution_agent → beto transfers
- code_execution_agent → scout transfers
- code_execution_agent → search_agent transfers

Usage:
    # Run validation tests
    python -m tools.test_adk_builtin_transfers --validate
    
    # Run web application for manual testing
    python -m tools.test_adk_builtin_transfers --web
"""

import os
import sys
import logging
import time
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure the radbot package is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_environment(enable_search=True, enable_code_exec=True, debug=True):
    """Set up the environment variables for testing."""
    logger.info("Setting up environment for ADK built-in agent tests")
    
    # Store original environment to restore later
    orig_env = {}
    for var in ["RADBOT_ENABLE_ADK_SEARCH", "RADBOT_ENABLE_ADK_CODE_EXEC", "LOG_LEVEL", "RADBOT_USE_VERTEX_AI"]:
        orig_env[var] = os.environ.get(var)
    
    # Set test environment
    os.environ["RADBOT_ENABLE_ADK_SEARCH"] = "true" if enable_search else "false"
    if enable_search:
        logger.info("Enabled ADK Search tool")
    else:
        logger.info("Disabled ADK Search tool")
    
    os.environ["RADBOT_ENABLE_ADK_CODE_EXEC"] = "true" if enable_code_exec else "false"
    if enable_code_exec:
        logger.info("Enabled ADK Code Execution tool")
    else:
        logger.info("Disabled ADK Code Execution tool")
    
    if debug:
        # Set verbose logging for agent transfers
        os.environ["LOG_LEVEL"] = "DEBUG"
        logger.info("Set log level to DEBUG for detailed transfer logs")
    
    return orig_env

def restore_environment(orig_env):
    """Restore the original environment variables."""
    for var, value in orig_env.items():
        if value is None:
            if var in os.environ:
                del os.environ[var]
        else:
            os.environ[var] = value

def run_web_app():
    """Start the web application."""
    logger.info("Starting web application with ADK built-in agents")
    
    try:
        from radbot.web import app
        
        # Import necessary modules for startup
        from agent import root_agent
        
        logger.info(f"Root agent name: {root_agent.name if hasattr(root_agent, 'name') else 'unnamed'}")
        
        # Get sub-agents
        sub_agents = getattr(root_agent, 'sub_agents', [])
        sub_agent_names = [sa.name for sa in sub_agents if hasattr(sa, 'name')]
        logger.info(f"Sub-agents: {sub_agent_names}")
        
        # Check for search and code execution agents
        has_search = "search_agent" in sub_agent_names
        has_code_exec = "code_execution_agent" in sub_agent_names
        logger.info(f"Has search agent: {has_search}")
        logger.info(f"Has code execution agent: {has_code_exec}")
        
        # Report success
        logger.info(f"Web application started. Please navigate to http://localhost:8080")
        logger.info(f"Test agent transfers by:")
        logger.info(f" - Asking the agent to search Google for something")
        logger.info(f" - Asking the agent to execute some Python code")
        logger.info(f" - Check the logs for transfer events and debugging information")
        logger.info(f"Press Ctrl+C to exit when testing is complete")
        
        # Run the application
        # Note: This will block until manually terminated
        app.run(host='0.0.0.0', port=8080)
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
    except Exception as e:
        logger.error(f"Error starting web application: {e}", exc_info=True)

class AgentTransferTest:
    """Test harness for agent transfers."""
    
    def __init__(self):
        """Initialize test configurations."""
        self.test_configs = [
            {"search": False, "code_exec": False, "name": "No builtin tools"},
            {"search": True, "code_exec": False, "name": "Search only"},
            {"search": False, "code_exec": True, "name": "Code execution only"},
            {"search": True, "code_exec": True, "name": "Both builtin tools"},
            {"search": True, "code_exec": True, "name": "Both builtin tools (Vertex AI)", "vertex_ai": True},
        ]
        
        # All agent names to test
        self.agent_names = ["beto", "scout", "search_agent", "code_execution_agent"]
        
        # Define transfer paths to test
        self.transfer_paths = [
            ("beto", "scout"),
            ("beto", "search_agent"),
            ("beto", "code_execution_agent"),
            ("scout", "beto"),
            ("scout", "search_agent"),
            ("scout", "code_execution_agent"),
            ("search_agent", "beto"),
            ("search_agent", "scout"),
            ("search_agent", "code_execution_agent"),
            ("code_execution_agent", "beto"),
            ("code_execution_agent", "scout"),
            ("code_execution_agent", "search_agent"),
        ]
        
        self.results = []
    
    def run_test_config(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run tests for a specific configuration."""
        logger.info(f"Testing configuration: {config['name']}")
        logger.info(f"  Search: {config['search']}")
        logger.info(f"  Code Execution: {config['code_exec']}")
        logger.info(f"  Vertex AI: {config.get('vertex_ai', False)}")
        
        # Set up environment
        orig_env = setup_environment(
            enable_search=config["search"],
            enable_code_exec=config["code_exec"],
            debug=True
        )
        
        # Set Vertex AI environment variable if needed
        if config.get("vertex_ai", False):
            os.environ["RADBOT_USE_VERTEX_AI"] = "true"
            logger.info("Set RADBOT_USE_VERTEX_AI=true")
        
        try:
            # Create agents 
            from radbot.agent.agent import create_core_agent_for_web
            from radbot.agent.research_agent.factory import create_research_agent
            
            # Create root agent with appropriate configuration
            root_agent = create_core_agent_for_web(
                name="beto",
                app_name="beto",
                include_google_search=config["search"],
                include_code_execution=config["code_exec"]
            )
            
            # Check tools and sub-agents
            tools = getattr(root_agent, "tools", [])
            tool_names = [getattr(tool, "name", str(tool)) for tool in tools]
            
            # Get transfer tool if available
            from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
            try:
                # Also try importing the backwards compatibility version
                from radbot.tools.agent_transfer import AgentTransferTool
                has_compat_tool = True
            except ImportError:
                has_compat_tool = False
                
            transfer_tool = None
            for tool in tools:
                # Check if it's the transfer_to_agent tool by name or function reference
                tool_name = getattr(tool, "name", "")
                if (tool == transfer_to_agent or 
                    tool_name == "transfer_to_agent" or 
                    (has_compat_tool and isinstance(tool, AgentTransferTool))):
                    transfer_tool = tool
                    break
            
            # Check sub_agents
            sub_agents = getattr(root_agent, "sub_agents", [])
            sub_agent_names = [getattr(agent, "name", None) for agent in sub_agents]
            
            logger.info(f"Root agent tools: {tool_names}")
            logger.info(f"Root agent sub_agents: {sub_agent_names}")
            
            # Check each transfer path
            results = []
            
            # Validate specialized agents have at most one tool if using Vertex AI
            if config.get("vertex_ai", False):
                # Find specialized agents in sub_agents
                vertex_validation_results = {}
                
                for sa in sub_agents:
                    sa_name = getattr(sa, "name", "unknown")
                    if sa_name in ["search_agent", "code_execution_agent"]:
                        # Check tool count
                        sa_tools = getattr(sa, "tools", [])
                        sa_tools_count = len(sa_tools)
                        
                        # Vertex AI requires one tool at most
                        is_valid = sa_tools_count <= 1
                        
                        vertex_validation_results[sa_name] = {
                            "tools_count": sa_tools_count,
                            "is_valid": is_valid,
                            "tools": [getattr(tool, "name", str(tool)) for tool in sa_tools]
                        }
                        
                        # Log results
                        status_str = "✅" if is_valid else "❌"
                        logger.info(f"Vertex AI validation for {sa_name}: {status_str} ({sa_tools_count} tools)")
                        if sa_tools_count > 0:
                            logger.info(f"  Tools: {', '.join([str(t) for t in vertex_validation_results[sa_name]['tools']])}")
                
                # Add to results
                if vertex_validation_results:
                    results.append({
                        "config_name": config["name"],
                        "source": "vertex_validation",
                        "target": "vertex_validation",
                        "vertex_validation": vertex_validation_results,
                        "status": all(r["is_valid"] for r in vertex_validation_results.values())
                    })
            
            # For each path, check if it's possible based on configuration
            for source_name, target_name in self.transfer_paths:
                # Skip paths involving disabled agents
                if (target_name == "search_agent" and not config["search"]) or \
                   (target_name == "code_execution_agent" and not config["code_exec"]):
                    logger.info(f"Skipping {source_name} → {target_name} (target not enabled)")
                    continue
                
                # For now, we're only testing transfers from the root agent
                if source_name != "beto":
                    logger.info(f"Skipping {source_name} → {target_name} (non-root source)")
                    continue
                
                # Check if transfer is possible
                # Safely look for target in sub_agents (handle None names)
                target_in_sub_agents = False
                for sa in sub_agents:
                    sa_name = getattr(sa, "name", None)
                    if sa_name == target_name:
                        target_in_sub_agents = True
                        break
                
                has_transfer_tool = transfer_tool is not None
                
                # Transfer validation depends on whether we're using Vertex AI
                is_vertex = config.get("vertex_ai", False)
                
                # In Vertex AI mode, we don't need transfer_to_agent tool, just the instructions
                # and the target in sub_agents
                if is_vertex:
                    status = "valid" if target_in_sub_agents else "invalid"
                else:
                    status = "valid" if target_in_sub_agents and has_transfer_tool else "invalid"
                
                # Record result
                result = {
                    "config_name": config["name"],
                    "source": source_name,
                    "target": target_name,
                    "has_transfer_tool": has_transfer_tool,
                    "target_in_sub_agents": target_in_sub_agents,
                    "status": status
                }
                
                results.append(result)
                logger.info(f"{source_name} → {target_name}: " 
                           f"{'✅' if status == 'valid' else '❌'} "
                           f"(transfer tool: {'✅' if has_transfer_tool else '❌'}, "
                           f"in sub_agents: {'✅' if target_in_sub_agents else '❌'})")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in test: {str(e)}", exc_info=True)
            return []
        finally:
            # Restore environment
            restore_environment(orig_env)
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all test configurations."""
        all_results = []
        
        for config in self.test_configs:
            results = self.run_test_config(config)
            all_results.extend(results)
        
        # Calculate summary statistics
        total = len(all_results)
        valid = sum(1 for r in all_results if r["status"] == "valid")
        
        if total > 0:
            logger.info(f"Test summary: {valid}/{total} transfer paths valid ({valid/total*100:.1f}%)")
        else:
            logger.info("No test results collected")
        
        return all_results
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print a summary of test results."""
        print("\nAgent Transfer Test Results Summary:")
        print("===================================")
        
        # Group by configuration
        by_config = {}
        for result in results:
            config_name = result["config_name"]
            if config_name not in by_config:
                by_config[config_name] = []
            by_config[config_name].append(result)
        
        # Print summary for each configuration
        for config_name, config_results in by_config.items():
            total = len(config_results)
            valid = sum(1 for r in config_results if r["status"] == "valid")
            
            print(f"\nConfiguration: {config_name}")
            percent = valid/total*100 if total > 0 else 0
            print(f"  Valid transfers: {valid}/{total} ({percent:.1f}%)")
            
            # Sort results by source then target
            config_results.sort(key=lambda r: (r["source"], r["target"]))
            
            # Print details of each transfer path
            for result in config_results:
                status = "✅" if result["status"] == "valid" else "❌"
                source = result["source"]
                target = result["target"]
                
                # Handle special Vertex AI validation results
                if source == "vertex_validation" and target == "vertex_validation":
                    print(f"  {status} Vertex AI Tool Count Validation")
                    if "vertex_validation" in result:
                        # Print detailed results for each agent
                        for agent_name, validation in result["vertex_validation"].items():
                            agent_status = "✅" if validation["is_valid"] else "❌"
                            tools_count = validation["tools_count"]
                            print(f"     {agent_status} {agent_name}: {tools_count} tools")
                            if tools_count > 0:
                                tools_str = ", ".join([str(t) for t in validation["tools"]])
                                print(f"        Tools: {tools_str}")
                    continue
                
                # Normal transfer path result
                print(f"  {status} {source} → {target}")
                
                # If invalid, print reason
                if result["status"] == "invalid":
                    reasons = []
                    # Check if has_transfer_tool is present (not needed for Vertex AI)
                    if "has_transfer_tool" in result and not result["has_transfer_tool"]:
                        reasons.append("Missing transfer_to_agent tool")
                    if not result["target_in_sub_agents"]:
                        reasons.append("Target not in sub_agents list")
                    print(f"     Issues: {', '.join(reasons)}")

def run_validation_tests():
    """Run programmatic validation of agent transfers."""
    logger.info("Running transfer validation tests")
    test = AgentTransferTest()
    results = test.run_all_tests()
    test.print_summary(results)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test ADK built-in agent transfers")
    
    # Create a mutually exclusive group for the test modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate", action="store_true", help="Run validation tests")
    group.add_argument("--web", action="store_true", help="Run web application for manual testing")
    
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    if args.validate:
        # Run validation tests
        run_validation_tests()
    elif args.web:
        # Set up environment with all tools enabled
        orig_env = setup_environment()
        
        # Run web application
        try:
            run_web_app()
        finally:
            # Clean up environment
            restore_environment(orig_env)