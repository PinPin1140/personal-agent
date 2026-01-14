"""Skill registry for loading, managing, and discovering skills."""
import os
import importlib
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from .base import Skill


class SkillRegistry:
    """Registry for managing available skills."""

    def __init__(self, skills_dir: str = "agent/skills/builtin"):
        self.skills_dir = Path(skills_dir)
        self._skills: Dict[str, Skill] = {}
        self._load_builtin_skills()

    def _load_builtin_skills(self):
        """Load built-in skills from the builtin directory."""
        if not self.skills_dir.exists():
                return

        # Import all Python files in builtin directory
        for skill_file in self.skills_dir.glob("*.py"):
                if skill_file.name.startswith("_"):
                        continue

                try:
                        module_name = f"agent.skills.builtin.{skill_file.stem}"
                        module = importlib.import_module(module_name)

                        # Look for skill classes (classes that inherit from Skill)
                        for attr_name in dir(module):
                                attr = getattr(module, attr_name)
                                if (isinstance(attr, type) and
                                        issubclass(attr, Skill) and
                                        attr != Skill):
                                        # Create instance
                                        skill_instance = attr()
                                        self.register(skill_instance)

                except (ImportError, AttributeError) as e:
                        print(f"Failed to load skill from {skill_file}: {e}")

    def register(self, skill: Skill):
        """Register a skill instance."""
        self._skills[skill.name] = skill

    def unregister(self, skill_name: str) -> bool:
        """Unregister a skill by name."""
        if skill_name in self._skills:
                del self._skills[skill_name]
                return True
        return False

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> List[Skill]:
        """List all registered skills."""
        return list(self._skills.values())

    def find_matching_skills(self, task_goal: str, available_tools: Set[str]) -> List[Skill]:
        """Find skills that can handle a task and have required tools available."""
        matching_skills = []

        for skill in self._skills.values():
                if skill.can_handle_task(type('Task', (), {'goal': task_goal, 'description': ''})()):
                        if skill.validate_requirements(available_tools):
                                matching_skills.append(skill)

        return matching_skills

    def get_skill_names(self) -> List[str]:
        """Get list of all skill names."""
        return list(self._skills.keys())

    def get_skills_by_tool(self, tool_name: str) -> List[Skill]:
        """Get skills that require a specific tool."""
        return [skill for skill in self._skills.values()
                        if tool_name in skill.get_required_tools()]

    def get_skills_by_trigger(self, trigger_pattern: str) -> List[Skill]:
        """Get skills that match a trigger pattern."""
        matching = []
        for skill in self._skills.values():
                for pattern in skill.trigger_patterns:
                        if trigger_pattern.lower() in pattern.lower():
                                matching.append(skill)
                                break
        return matching

    def reload_skills(self):
        """Reload all skills (useful for development)."""
        self._skills = {}
        self._load_builtin_skills()

    def validate_skill_requirements(self, skill_name: str, available_tools: Set[str]) -> Dict[str, Any]:
        """Validate if a skill's requirements are met."""
        skill = self.get_skill(skill_name)
        if not skill:
                return {"valid": False, "reason": "Skill not found"}

        if not skill.validate_requirements(available_tools):
                missing = set(skill.get_required_tools()) - available_tools
                return {
                        "valid": False,
                        "reason": f"Missing tools: {', '.join(missing)}"
                }

        return {"valid": True, "reason": "All requirements met"}
