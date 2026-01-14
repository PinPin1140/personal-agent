"""Debug skill that diagnoses errors and provides troubleshooting assistance."""
from typing import Dict, Any
from ..base import Skill
from ...tools.registry import ToolRegistry
from ...model_router import ModelRouter


class DebugSkill(Skill):
    """Skill for debugging errors and diagnosing issues."""

    def __init__(self):
        super().__init__(
                name="debug",
                description="Diagnoses errors, analyzes logs, and provides troubleshooting",
                version="1.0.0",
                trigger_patterns=[
                        "debug", "diagnose error", "troubleshoot", "fix error",
                        "analyze logs", "check logs", "find bug", "debug issue"
                ],
                required_tools=["shell", "file_read", "list_dir"],
                constraints={
                        "max_log_files": 5,
                        "log_file_patterns": ["*.log", "*.err", "*.out"]
                }
        )
        self.tool_registry = None
        self.model_router = None

    def execute(self, task, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Execute debugging analysis on task."""
        goal = task.goal.lower()

        # Determine what to debug
        error_message = None
        log_files = []
        system_info = {}

        # Check for error messages in goal
        import re
        error_match = re.search(r'(?:debug|fix|diagnose)\s+(.+)', goal)
        if error_match:
                error_message = error_match.group(1).strip()

        # Look for log files in current directory
        list_tool = self.tool_registry.get("list_dir")
        if list_tool:
                list_result = list_tool.execute(path=".")
                if not list_result.get("error"):
                        files = list_result.get("output", "").strip().split('\n')
                        for file in files:
                                if any(file.endswith(pattern[1:]) for pattern in self.constraints["log_file_patterns"]):
                                        log_files.append(file)

        # Limit log files
        log_files = log_files[:self.constraints["max_log_files"]]

        # Read log files
        log_contents = {}
        file_tool = self.tool_registry.get("file_read")
        if file_tool:
                for log_file in log_files:
                        read_result = file_tool.execute(filepath=log_file)
                        if not read_result.get("error"):
                                log_contents[log_file] = read_result.get("output", "")[:5000]  # Limit content

        # Get system information
        shell_tool = self.tool_registry.get("shell")
        if shell_tool:
                # Get basic system info (safe commands only)
                safe_commands = [
                        "uname -a",
                        "df -h",
                        "free -h",
                        "ps aux | head -10"
                ]

                for cmd in safe_commands:
                        result = shell_tool.execute(command=cmd)
                        if not result.get("error"):
                                system_info[cmd] = result.get("output", "")

        # Analyze with model
        analysis_prompt = f"""
You are a debugging expert. Analyze the following debugging scenario:

Task: {task.goal}

{f"Error Description: {error_message}" if error_message else ""}

Log Files Found: {', '.join(log_files) if log_files else "None"}

System Information:
{chr(10).join(f"{cmd}: {info}" for cmd, info in system_info.items())}

Log Contents:
{chr(10).join(f"=== {file} ==={chr(10)}{content[:2000]}..." for file, content in log_contents.items())}

Please provide:
1. Root cause analysis
2. Step-by-step troubleshooting steps
3. Potential solutions
4. Prevention recommendations
5. Commands to run for further diagnosis

Be specific and actionable.
"""

        analysis = self.model_router.generate(analysis_prompt, context={"task": "debug"})

        # Create subtasks for fixes if analysis suggests them
        if "solution" in analysis.lower() or "fix" in analysis.lower():
                subtask = self.add_subtask(f"Apply debug fixes for: {task.goal[:50]}")
                subtask.description = "Implement the debugging solutions identified"

        return {
                "success": True,
                "analysis": analysis,
                "error_detected": error_message,
                "log_files_analyzed": len(log_files),
                "system_info_collected": len(system_info),
                "subtasks_created": len(self.get_subtasks())
        }
