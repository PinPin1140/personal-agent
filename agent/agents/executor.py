"""Worker agent for executing tasks autonomously."""
from typing import Dict, Any, Optional
import re
from .base import BaseAgent
from ..task import Task, TaskStatus
from ..model_router import ModelRouter


class WorkerAgent(BaseAgent):
    """Worker agent that executes tasks with tool calling."""

    def __init__(self, tool_registry, model_router: ModelRouter):
        super().__init__(tool_registry)
        self.model_router = model_router
        self.max_tools_per_step = 3
        self._status = "idle"

    def execute(self, task: Task) -> Dict[str, Any]:
        """Execute task autonomously with tool calls."""
        self._status = "running"

        try:
                result = self._run_task_loop(task)
                self._status = "idle"
                return {
                        "success": result.get("success", False),
                        "steps_completed": result.get("steps_completed", 0),
                        "error": result.get("error")
                }
        except Exception as e:
                self._status = "error"
                return {
                        "success": False,
                        "steps_completed": 0,
                        "error": str(e)
                }

    def _run_task_loop(self, task: Task, max_steps: int = 10) -> Dict[str, Any]:
        """Run task through decision-action loop."""
        steps_completed = 0
        tool_calls_count = 0

        while steps_completed < max_steps:
                steps_completed += 1
                tool_calls_count = 0

                # Build context for model
                context = {
                        "task_id": task.id,
                        "goal": task.goal,
                        "status": task.status.value,
                        "steps": task.steps[-3:],
                        "available_tools": [tool.to_schema() for tool in self.tool_registry.list_tools()]
                }

                # Get decision from model
                decision = self.model_router.generate(
                        prompt=f"Task goal: {task.goal}\nCurrent step: {steps_completed}",
                        context=context
                )

                # Add decision step
                task.add_step("decision", result=decision)

                # Check for completion
                if self._is_complete(decision):
                        return {
                                "success": True,
                                "steps_completed": steps_completed,
                                "error": None
                        }

                # Check for tool calls
                tool_calls = self._detect_tool_calls(decision)

                if not tool_calls:
                        # No tools, add generic action
                        task.add_step("action", result=decision[:200])
                        continue

                # Execute tools
                for tool_call in tool_calls[:self.max_tools_per_step]:
                        tool_calls_count += 1
                        result = self._execute_tool(tool_call)
                        task.add_step("action", result=result.get("output", ""), error=result.get("error"))

                        if result.get("error"):
                                return {
                                        "success": False,
                                        "steps_completed": steps_completed,
                                        "error": f"Tool failed: {result['error']}"
                                }

                # Mark complete if max steps reached
                if steps_completed >= max_steps:
                        return {
                                "success": True,
                                "steps_completed": steps_completed,
                                "error": None
                        }

        return {
                "success": False,
                "steps_completed": steps_completed,
                "error": "Max steps exceeded"
        }

    def _detect_tool_calls(self, text: str) -> list[Dict[str, Any]]:
        """Detect tool calls in model output."""
        # Simple pattern matching: tool_name(arg1=value1, arg2=value2)
        pattern = r'(\w+)\(([^)]+)\)'
        matches = re.findall(pattern, text)

        tool_calls = []
        for tool_name, args_str in matches:
                # Parse arguments
                args = {}
                for arg_pair in args_str.split(','):
                        if '=' in arg_pair:
                                key, value = arg_pair.split('=', 1)
                                args[key.strip()] = value.strip().strip('"')

                tool_calls.append({
                        "tool": tool_name,
                        "arguments": args
                })

        return tool_calls

    def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with arguments."""
        tool_name = tool_call.get("tool", "")
        arguments = tool_call.get("arguments", {})

        tool = self.tool_registry.get(tool_name)
        if not tool:
                return {
                        "output": "",
                        "error": f"Tool not found: {tool_name}"
                }

        return tool.execute(**arguments)

    def _is_complete(self, decision: str) -> bool:
        """Check if decision indicates task completion."""
        complete_markers = ["done", "complete", "finished", "success", "finished"]
        decision_lower = decision.lower()
        return any(marker in decision_lower for marker in complete_markers)

    def get_status(self) -> str:
        """Get current worker status."""
        return self._status
