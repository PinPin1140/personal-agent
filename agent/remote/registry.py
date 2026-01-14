"""Registry for remote agent nodes."""
from typing import Dict, Any, Optional
from .node import RemoteNode


class NodeRegistry:
    """Manage registered remote nodes."""

    def __init__(self, nodes_path: str = "data/nodes.json"):
        self.nodes_path = Path(nodes_path)
        self.nodes_path.parent.mkdir(parents=True, exist_ok=True)
        self._nodes: Dict[str, RemoteNode] = {}
        self._load()

    def _load(self):
        """Load nodes from disk."""
        if self.nodes_path.exists():
                try:
                        with open(self.nodes_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                for node_id, node_data in data.get("nodes", {}).items():
                                        self._nodes[node_id] = RemoteNode.from_dict(node_data)
                except (json.JSONDecodeError, IOError):
                        self._nodes = {}

    def _save(self):
        """Atomically save nodes to disk."""
        temp_path = self.nodes_path.with_suffix(".tmp")
        try:
                with open(temp_path, "w", encoding="utf-8") as f:
                        data = {
                                "nodes": {
                                        node_id: node.to_dict()
                                        for node_id, node in self._nodes.items()
                                }
                        }
                        json.dump(data, f, indent=2)
                temp_path.replace(self.nodes_path)
        except (IOError, OSError):
                if temp_path.exists():
                        temp_path.unlink()
                raise

    def register(self, node: RemoteNode):
        """Register a new remote node."""
        self._nodes[node.node_id] = node
        self._save()
        return True

    def unregister(self, node_id: str) -> bool:
        """Unregister a remote node."""
        if node_id in self._nodes:
                del self._nodes[node_id]
                self._save()
                return True
        return False

    def get_node(self, node_id: str) -> Optional[RemoteNode]:
        """Get node by ID."""
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[RemoteNode]:
        """List all registered nodes."""
        return list(self._nodes.values())

    def find_available(self, capabilities: list[str] = None) -> Optional[RemoteNode]:
        """Find available node matching capabilities."""
        for node in self._nodes.values():
                if node._status == "online":
                        if not capabilities or all(cap in node.capabilities):
                                return node
        return None

    def update_node_status(self, node_id: str, status: str):
        """Update node status."""
        node = self.get_node(node_id)
        if node:
                node.update_status(status)
                self._save()
                return True
        return False
