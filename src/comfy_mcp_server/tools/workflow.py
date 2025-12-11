"""Workflow management and creation tools.

Impact: High (core functionality for automation)
Complexity: Medium (file operations, template management)
"""

import json
from pathlib import Path

from mcp.server.fastmcp import Context
from pydantic import Field

from ..models import ErrorResponse
from ..settings import settings

# === Workflow Templates ===
TEMPLATES = {
    "empty": {},
    "fal-flux-dev": {
        "1": {
            "class_type": "RemoteCheckpointLoader_fal",
            "inputs": {"ckpt_name": "fal-ai/flux/dev"},
        },
        "2": {"class_type": "StringInput_fal", "inputs": {"text": "A beautiful landscape"}},
        "3": {"class_type": "IntegerInput_fal", "inputs": {"value": 1024}},
        "4": {"class_type": "IntegerInput_fal", "inputs": {"value": 1024}},
        "5": {"class_type": "IntegerInput_fal", "inputs": {"value": 28}},
        "6": {"class_type": "FloatInput_fal", "inputs": {"value": 3.5}},
        "7": {
            "class_type": "SaveImage_fal",
            "inputs": {"filename_prefix": "flux_output", "images": ["1", 0]},
        },
    },
    "fal-flux-schnell": {
        "1": {
            "class_type": "RemoteCheckpointLoader_fal",
            "inputs": {"ckpt_name": "fal-ai/flux/schnell"},
        },
        "2": {"class_type": "StringInput_fal", "inputs": {"text": "A beautiful landscape"}},
        "3": {
            "class_type": "SaveImage_fal",
            "inputs": {"filename_prefix": "flux_schnell", "images": ["1", 0]},
        },
    },
}


def register_workflow_tools(mcp):
    """Register workflow management tools."""

    @mcp.tool()
    def list_workflows(ctx: Context = None) -> list:
        """List available workflow files.

        Returns list of workflow JSON files in the configured workflows directory.
        Use run_workflow() to execute a saved workflow.
        """
        if not settings.workflows_dir:
            return ["Error: COMFY_WORKFLOWS_DIR not configured"]

        if ctx:
            ctx.info(f"Listing workflows in: {settings.workflows_dir}")

        path = Path(settings.workflows_dir)
        if not path.exists():
            return []
        return sorted([f.name for f in path.glob("*.json")])

    @mcp.tool()
    def load_workflow(
        workflow_name: str = Field(description="Workflow filename"),
        ctx: Context = None,
    ) -> dict:
        """Load a workflow file for inspection or modification.

        Args:
            workflow_name: Workflow filename (e.g., 'my-workflow.json')

        Returns the workflow dict that can be modified and executed.
        """
        if not settings.workflows_dir:
            return ErrorResponse.not_configured("COMFY_WORKFLOWS_DIR").model_dump()

        wf_path = Path(settings.workflows_dir) / workflow_name
        if not wf_path.exists():
            return ErrorResponse.not_found(
                f"Workflow '{workflow_name}'",
                suggestion="Use list_workflows() to see available workflows",
            ).model_dump()

        if ctx:
            ctx.info(f"Loading workflow: {workflow_name}")

        with open(wf_path) as f:
            return json.load(f)

    @mcp.tool()
    def save_workflow(
        workflow: dict = Field(description="Workflow to save"),
        name: str = Field(description="Filename (without .json)"),
        ctx: Context = None,
    ) -> str:
        """Save a workflow to the workflows directory.

        Args:
            workflow: Workflow dict to save
            name: Filename (with or without .json extension)

        Returns path to saved file or error message.
        """
        if not settings.workflows_dir:
            return "Error: COMFY_WORKFLOWS_DIR not configured"

        if not name.endswith(".json"):
            name = f"{name}.json"

        path = Path(settings.workflows_dir) / name

        if ctx:
            ctx.info(f"Saving to: {path}")

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(workflow, f, indent=2)
            return f"Saved: {path}"
        except Exception as e:
            return f"Error: {e}"

    @mcp.tool()
    def create_workflow(ctx: Context = None) -> dict:
        """Create an empty workflow structure.

        Returns an empty dict that you can populate with add_node().
        """
        if ctx:
            ctx.info("Creating new workflow")
        return {}

    @mcp.tool()
    def add_node(
        workflow: dict = Field(description="Workflow dict to modify"),
        node_id: str = Field(description="Unique node ID (e.g., '1', 'prompt')"),
        node_type: str = Field(description="Node class name"),
        inputs: dict = Field(description="Node inputs"),
        ctx: Context = None,
    ) -> dict:
        """Add a node to a workflow.

        Args:
            workflow: Existing workflow dict
            node_id: Unique identifier for this node
            node_type: Node class name (use list_nodes() to find)
            inputs: Input values. For connections use ["source_node_id", output_index].

        Examples:
            # Simple value input
            add_node(wf, "1", "StringInput_fal", {"text": "a cat"})

            # Connection to another node
            add_node(wf, "2", "CLIPTextEncode", {
                "text": "prompt",
                "clip": ["1", 0]  # Connect to node "1" output 0
            })

        Returns the modified workflow dict.
        """
        if ctx:
            ctx.info(f"Adding node {node_id}: {node_type}")

        workflow[node_id] = {"class_type": node_type, "inputs": inputs}
        return workflow

    @mcp.tool()
    def remove_node(
        workflow: dict = Field(description="Workflow dict to modify"),
        node_id: str = Field(description="Node ID to remove"),
        ctx: Context = None,
    ) -> dict:
        """Remove a node from a workflow.

        Args:
            workflow: Workflow dict to modify
            node_id: ID of node to remove

        Warning: This doesn't update connections from other nodes.
        """
        if ctx:
            ctx.info(f"Removing node: {node_id}")

        if node_id in workflow:
            del workflow[node_id]
        return workflow

    @mcp.tool()
    def update_node_input(
        workflow: dict = Field(description="Workflow dict to modify"),
        node_id: str = Field(description="Node ID to update"),
        input_name: str = Field(description="Input name to update"),
        value: str = Field(description="New value (or JSON for complex values)"),
        ctx: Context = None,
    ) -> dict:
        """Update a specific input on a node.

        Args:
            workflow: Workflow dict to modify
            node_id: Node ID to update
            input_name: Name of the input to update
            value: New value (use JSON string for lists/dicts)

        Returns the modified workflow dict.
        """
        if ctx:
            ctx.info(f"Updating {node_id}.{input_name}")

        if node_id not in workflow:
            return workflow

        # Try to parse as JSON for complex values
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            parsed_value = value

        workflow[node_id]["inputs"][input_name] = parsed_value
        return workflow

    @mcp.tool()
    def get_workflow_template(
        template_name: str = Field(
            description="Template: 'fal-flux-dev', 'fal-flux-schnell', 'empty'"
        ),
        ctx: Context = None,
    ) -> dict:
        """Get a pre-built workflow template.

        Args:
            template_name: One of:
                - 'empty': Empty workflow
                - 'fal-flux-dev': Flux Dev via fal.ai (higher quality)
                - 'fal-flux-schnell': Flux Schnell via fal.ai (faster)

        Returns a workflow dict that can be modified and executed.
        """
        if ctx:
            ctx.info(f"Loading template: {template_name}")

        if template_name not in TEMPLATES:
            return ErrorResponse.not_found(
                f"Template '{template_name}'",
                suggestion=f"Available: {list(TEMPLATES.keys())}",
            ).model_dump()

        # Return a copy to avoid modifying the original
        return json.loads(json.dumps(TEMPLATES[template_name]))

    @mcp.tool()
    def list_templates(ctx: Context = None) -> list:
        """List available workflow templates.

        Returns list of template names for get_workflow_template().
        """
        if ctx:
            ctx.info("Listing templates")
        return list(TEMPLATES.keys())

    @mcp.tool()
    def validate_workflow(
        workflow: dict = Field(description="Workflow to validate"),
        ctx: Context = None,
    ) -> dict:
        """Validate a workflow structure.

        Args:
            workflow: Workflow dict to validate

        Returns validation result with any issues found.
        """
        if ctx:
            ctx.info("Validating workflow")

        issues = []
        node_ids = set(workflow.keys())

        for node_id, node in workflow.items():
            # Check required fields
            if "class_type" not in node:
                issues.append(f"Node {node_id}: missing class_type")
            if "inputs" not in node:
                issues.append(f"Node {node_id}: missing inputs")

            # Check connections reference valid nodes
            if "inputs" in node:
                for input_name, value in node["inputs"].items():
                    if isinstance(value, list) and len(value) == 2:
                        ref_node = str(value[0])
                        if ref_node not in node_ids:
                            issues.append(
                                f"Node {node_id}.{input_name}: "
                                f"references non-existent node {ref_node}"
                            )

        return {
            "valid": len(issues) == 0,
            "node_count": len(workflow),
            "issues": issues,
        }
