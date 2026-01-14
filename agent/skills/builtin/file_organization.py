"""File organization skill that organizes and cleans up directories."""
from typing import Dict, Any, List
from ..base import Skill
from ...tools.registry import ToolRegistry


class FileOrganizationSkill(Skill):
    """Skill for organizing files and directories."""

    def __init__(self):
        super().__init__(
                name="file_organization",
                description="Organizes files by type, removes duplicates, cleans up directories",
                version="1.0.0",
                trigger_patterns=[
                        "organize files", "clean up files", "sort files",
                        "organize directory", "tidy up", "file organization"
                ],
                required_tools=["list_dir", "file_read", "file_write"],
                constraints={
                        "max_files_to_process": 100,
                        "safe_extensions": [".txt", ".md", ".log", ".tmp"]
                }
        )
        self.tool_registry = None

    def execute(self, task, context: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Execute file organization on task."""
        goal = task.goal.lower()

        # Extract directory path from task goal
        import re
        dir_match = re.search(r'(?:organize|clean|sort)\s+(?:files\s+in\s+)?(.+)', goal)
        target_dir = dir_match.group(1).strip() if dir_match else "."

        # List directory contents
        list_tool = self.tool_registry.get("list_dir")
        if not list_tool:
                return {"success": False, "error": "List directory tool not available"}

        list_result = list_tool.execute(path=target_dir)

        if list_result.get("error"):
                return {
                        "success": False,
                        "error": f"Failed to list directory: {list_result['error']}"
                }

        files = list_result.get("output", "").strip().split('\n')
        if not files or files == ['']:
                return {
                        "success": True,
                        "message": f"Directory {target_dir} is already organized (empty)",
                        "files_processed": 0
                }

        # Limit processing for safety
        if len(files) > self.constraints["max_files_to_process"]:
                return {
                        "success": False,
                        "error": f"Too many files ({len(files)}), max {self.constraints['max_files_to_process']}"
                }

        # Analyze file types
        file_types = self._analyze_files(files)

        # Generate organization plan
        plan = self._create_organization_plan(file_types, target_dir)

        # Execute organization
        results = self._execute_organization(plan)

        return {
                "success": True,
                "directory": target_dir,
                "files_analyzed": len(files),
                "file_types": file_types,
                "organization_plan": plan,
                "actions_taken": results
        }

    def _analyze_files(self, files: List[str]) -> Dict[str, List[str]]:
        """Analyze files by type."""
        file_types = {
                "python": [],
                "javascript": [],
                "documents": [],
                "images": [],
                "logs": [],
                "temp": [],
                "other": []
        }

        for file in files:
                if file.startswith('.') or '/' in file:
                        continue  # Skip hidden files and subdirs for now

                if file.endswith(('.py', '.pyc')):
                        file_types["python"].append(file)
                elif file.endswith(('.js', '.ts', '.jsx', '.tsx')):
                        file_types["javascript"].append(file)
                elif file.endswith(('.txt', '.md', '.doc', '.pdf')):
                        file_types["documents"].append(file)
                elif file.endswith(('.jpg', '.png', '.gif', '.svg')):
                        file_types["images"].append(file)
                elif file.endswith(('.log',)):
                        file_types["logs"].append(file)
                elif any(file.endswith(ext) for ext in ['.tmp', '.bak', '.swp']):
                        file_types["temp"].append(file)
                else:
                        file_types["other"].append(file)

        return file_types

    def _create_organization_plan(self, file_types: Dict[str, List[str]], base_dir: str) -> Dict[str, Any]:
        """Create organization plan."""
        plan = {
                "create_dirs": [],
                "move_files": [],
                "delete_files": [],
                "summary": {}
        }

        # Create directory structure
        dirs_to_create = ["documents", "images", "logs", "temp"]
        plan["create_dirs"] = [f"{base_dir}/{d}" for d in dirs_to_create]

        # Plan file moves
        for category, files in file_types.items():
                if category in ["documents", "images", "logs", "temp"]:
                        for file in files:
                                plan["move_files"].append({
                                        "from": f"{base_dir}/{file}",
                                        "to": f"{base_dir}/{category}/{file}"
                                })

        # Plan deletion of temp files
        for file in file_types.get("temp", []):
                if any(file.endswith(ext) for ext in self.constraints["safe_extensions"]):
                        plan["delete_files"].append(f"{base_dir}/{file}")

        # Summary
        plan["summary"] = {
                "total_files": sum(len(files) for files in file_types.values()),
                "dirs_to_create": len(plan["create_dirs"]),
                "files_to_move": len(plan["move_files"]),
                "files_to_delete": len(plan["delete_files"])
        }

        return plan

    def _execute_organization(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute organization plan."""
        results = []

        # Create directories (using shell tool for mkdir)
        shell_tool = self.tool_registry.get("shell")
        if shell_tool:
                for dir_path in plan["create_dirs"]:
                        result = shell_tool.execute(command=f"mkdir -p '{dir_path}'")
                        results.append({
                                "action": "create_dir",
                                "path": dir_path,
                                "success": "error" not in result,
                                "details": result
                        })

        # Move files (using shell tool for mv)
        if shell_tool:
                for move in plan["move_files"]:
                        result = shell_tool.execute(command=f"mv '{move['from']}' '{move['to']}'")
                        results.append({
                                "action": "move_file",
                                "from": move["from"],
                                "to": move["to"],
                                "success": "error" not in result,
                                "details": result
                        })

        # Delete files (using shell tool for rm)
        if shell_tool:
                for file_path in plan["delete_files"]:
                        result = shell_tool.execute(command=f"rm '{file_path}'")
                        results.append({
                                "action": "delete_file",
                                "path": file_path,
                                "success": "error" not in result,
                                "details": result
                        })

        return results
