"""Code review skill that analyzes code quality and provides suggestions."""
from typing import Dict, Any
from ..base import Skill
from ...model_router import ModelRouter
from ...tools.registry import ToolRegistry


class CodeReviewSkill(Skill):
    """Skill for reviewing code and providing improvement suggestions."""

    def __init__(self):
        super().__init__(
                name="code_review",
                description="Reviews code for quality, bugs, and improvements",
                version="1.0.0",
                trigger_patterns=[
                        "review code", "code review", "analyze code",
                        "check code", "improve code", "optimize code"
                ],
                required_tools=["file_read"],
                constraints={
                        "max_file_size": 100000,  # 100KB
                        "supported_extensions": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]
                }
        )
        self.model_router = None
        self.tool_registry = None

    def execute(self, task, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Execute code review on task."""
        # Extract file path from task goal
        goal = task.goal.lower()
        file_path = None

        # Simple pattern matching for file paths
        import re
        file_match = re.search(r'(?:review|analyze|check)\s+(.+\.\w+)', goal)
        if file_match:
                file_path = file_match.group(1).strip()

        if not file_path:
                return {
                        "success": False,
                        "error": "Could not identify file to review from task goal"
                }

        # Read file content
        file_tool = self.tool_registry.get("file_read")
        if not file_tool:
                return {"success": False, "error": "File read tool not available"}

        read_result = file_tool.execute(filepath=file_path)

        if read_result.get("error"):
                return {
                        "success": False,
                        "error": f"Failed to read file: {read_result['error']}"
                }

        code_content = read_result.get("output", "")

        # Check file size constraint
        if len(code_content) > self.constraints["max_file_size"]:
                return {
                        "success": False,
                        "error": f"File too large ({len(code_content)} bytes, max {self.constraints['max_file_size']})"
                }

        # Check file extension
        import os
        _, ext = os.path.splitext(file_path)
        if ext not in self.constraints["supported_extensions"]:
                return {
                        "success": False,
                        "error": f"Unsupported file type {ext}. Supported: {', '.join(self.constraints['supported_extensions'])}"
                }

        # Generate review using model
        prompt = f"""
Please review the following code file and provide detailed feedback:

File: {file_path}
Language: {ext}

Code:
{code_content}

Please provide:
1. Overall assessment
2. Code quality issues
3. Security concerns
4. Performance suggestions
5. Best practices recommendations
6. Specific improvement suggestions

Be thorough but constructive.
"""

        review_result = self.model_router.generate(prompt, context={"task": "code_review"})

        # Create subtask for implementing suggestions (optional)
        if "suggestion" in review_result.lower():
                subtask = self.add_subtask(f"Implement code review suggestions for {file_path}")
                subtask.description = "Apply the recommended improvements from code review"

        return {
                "success": True,
                "file_reviewed": file_path,
                "review": review_result,
                "code_length": len(code_content),
                "subtasks_created": len(self.get_subtasks())
        }
