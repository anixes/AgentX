import os
import ast
import re
import json
from pathlib import Path

class LocalExtractor:
    """
    Extracts structural nodes (classes, functions) without using AI tokens.
    """
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.seen_ids = set()

    def add_node(self, node_id, label, type_):
        if node_id not in self.seen_ids:
            self.nodes.append({"id": node_id, "label": label, "type": type_})
            self.seen_ids.add(node_id)

    def extract_python(self, path):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'))
            module_name = path.stem
            self.add_node(module_name, module_name, "module")
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_id = f"{module_name}.{node.name}"
                    self.add_node(class_id, node.name, "class")
                    self.edges.append({"source": module_name, "target": class_id, "type": "contains"})
                elif isinstance(node, ast.FunctionDef):
                    func_id = f"{module_name}.{node.name}"
                    self.add_node(func_id, node.name, "function")
                    self.edges.append({"source": module_name, "target": func_id, "type": "contains"})
        except:
            pass

    def extract_ts(self, path):
        content = path.read_text(encoding='utf-8')
        module_name = path.stem
        self.add_node(module_name, module_name, "module")

        # Simplified Regex for TS structural elements
        classes = re.findall(r'class\s+(\w+)', content)
        for c in classes:
            class_id = f"{module_name}.{c}"
            self.add_node(class_id, c, "class")
            self.edges.append({"source": module_name, "target": class_id, "type": "contains"})

        funcs = re.findall(r'(?:export\s+)?const\s+(\w+)\s*:\s*ToolDefinition', content)
        for f in funcs:
            func_id = f"{module_name}.{f}"
            self.add_node(func_id, f, "tool")
            self.edges.append({"source": module_name, "target": func_id, "type": "contains"})

    def run(self):
        # 1. Scan Files
        for root, _, files in os.walk("."):
            if "node_modules" in root or ".git" in root or "graphify-out" in root:
                continue
            for f in files:
                path = Path(root) / f
                if path.suffix == ".py":
                    self.extract_python(path)
                elif path.suffix == ".ts":
                    self.extract_ts(path)

        # 2. Merge with existing semantic data if possible
        # For this demo, we just overwrite the local structure
        output = {
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": {"type": "local_ast_sync"}
        }
        
        out_dir = Path("graphify-out")
        out_dir.mkdir(exist_ok=True)
        (out_dir / "graph_local.json").write_text(json.dumps(output, indent=2))
        
        # 3. Simple HTML update (Optional/Simplified)
        # We'll just print status for now
        print(f"Mapped {len(self.nodes)} nodes and {len(self.edges)} edges.")

if __name__ == "__main__":
    LocalExtractor().run()
