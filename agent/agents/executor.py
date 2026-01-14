"""Worker agent for executing tasks autonomously."""
from typing import Dict, Any, Optional
import re
from .base import BaseAgent
from ..task import Task, TaskStatus
from ..model_router import ModelRouter
from ..commands.registry import CommandRegistry
from ..profiles.base import AgentProfile
from ..skills.registry import SkillRegistry


class WorkerAgent(BaseAgent):
    """Worker agent that executes tasks with tool calling and skills."""

    def __init__(
                self,
                tool_registry,
                model_router: ModelRouter,
                skill_registry: Optional[SkillRegistry] = None,
                command_registry: Optional[CommandRegistry] = None,
                profile: Optional[AgentProfile] = None,
                # Security systems
                sandbox=None,
                syscall_filter=None
    ):
        super().__init__(tool_registry)
        self.model_router = model_router
        self.skill_registry = skill_registry or SkillRegistry()
        self.command_registry = command_registry or CommandRegistry()
        self.profile = profile
        self.max_tools_per_step = self.profile.max_tools_per_step if self.profile else 3
        self._status = "idle"

        # Security systems
        self.sandbox = sandbox
        self.syscall_filter = syscall_filter

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
        """Run task through decision-action loop with skill checking."""
        steps_completed = 0
        tool_calls_count = 0

        # Check for applicable skills first (if enabled in profile)
        if self.profile and self.profile.enable_skill_system:
                available_tools = set(tool.name for tool in self.tool_registry.list_tools())
                matching_skills = self.skill_registry.find_matching_skills(task.goal, available_tools)

                # Filter skills based on profile preferences
                if matching_skills and self.profile.prefer_skills_over_tools:
                        # Use the first matching skill
                        skill = matching_skills[0]
                        print(f"[WORKER] Using skill: {skill.name} (profile: {self.profile.name})")

                        # Set up skill dependencies
                        skill.tool_registry = self.tool_registry
                        skill.model_router = self.model_router

                        try:
                                skill_result = skill.execute(task)
                                task.add_step("skill_execution", result=f"Used skill: {skill.name}")

                                if skill_result.get("success", False):
                                        return {
                                                "success": True,
                                                "steps_completed": 1,
                                                "error": None,
                                                "skill_used": skill.name
                                        }
                                else:
                                        return {
                                                "success": False,
                                                "steps_completed": 1,
                                                "error": skill_result.get("error", "Skill execution failed")
                                        }
                        except Exception as e:
                                return {
                                        "success": False,
                                        "steps_completed": 1,
                                        "error": f"Skill execution error: {str(e)}"
                                }

        # Fall back to regular tool-based execution
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

                # Check for commands in model output
                command_result = self._check_and_execute_command(decision, task)
                if command_result:
                        # Command was executed, log it
                        task.add_step("command", result=command_result.output)

                        # Apply any state changes from command
                        if command_result.state_changes:
                                self._apply_command_state_changes(task, command_result.state_changes)

                        # Check if execution should be interrupted
                        if command_result.interrupt_execution:
                                return {
                                        "success": True,
                                        "steps_completed": steps_completed,
                                        "error": None,
                                        "interrupted_by_command": True
                                }

                        # Continue to next iteration
                        continue

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

    def _check_and_execute_command(self, text: str, task: Task):
        """Check for and execute commands in text."""
        # Build context for command execution
        context = {
                "task": task,
                "agent": self,
                "model_router": self.model_router,
                "tool_registry": self.tool_registry,
                "skill_registry": self.skill_registry,
                "timestamp": task.updated_at
        }

        # Try to execute command
        result = self.command_registry.execute_command(text, context)
        return result

    def _apply_command_state_changes(self, task: Task, state_changes: Dict[str, Any]):
        """Apply state changes from command execution."""
        if "switch_provider" in state_changes:
                # This would be handled by the model router
                # For now, just log the change
                task.add_step("state_change", result=f"Switched provider to: {state_changes['switch_provider']}")

        if "pause_execution" in state_changes:
                task.update_status(TaskStatus.PAUSED)

        if "resume_execution" in state_changes:
                task.update_status(TaskStatus.RUNNING)

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
        """Execute a tool with arguments, wrapped in security systems."""
        tool_name = tool_call.get("tool", "")
        arguments = tool_call.get("arguments", {})

        tool = self.tool_registry.get(tool_name)
        if not tool:
                return {
                        "output": "",
                        "error": f"Tool not found: {tool_name}"
                }

        # Apply security sandboxing if available
        if self.sandbox:
            try:
                # Wrap tool execution in sandbox
                result = self.sandbox.execute_secure(
                    lambda: tool.execute(**arguments)
                )
                return result
            except Exception as e:
                return {
                    "output": "",
                    "error": f"Security violation in {tool_name}: {str(e)}"
                }
        else:
            # Execute without sandbox
            return tool.execute(**arguments)

    def _is_complete(self, decision: str) -> bool:
        """Check if decision indicates task completion."""
        complete_markers = ["done", "complete", "finished", "success", "finished"]
        decision_lower = decision.lower()
        return any(marker in decision_lower for marker in complete_markers)

    def get_status(self) -> str:
        """Get current worker status."""
        return self._status
