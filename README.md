# Comfy MCP Server

[![smithery badge](https://smithery.ai/badge/@lalanikarim/comfy-mcp-server)](https://smithery.ai/server/@lalanikarim/comfy-mcp-server)

> MCP server for comprehensive ComfyUI workflow automation, management, and image generation.

## Overview

This server provides Claude Code (and other MCP clients) with full access to ComfyUI capabilities:

- **System monitoring**: Check server health, queue status, and history
- **Workflow execution**: Run saved workflows or execute custom workflow dicts
- **Workflow management**: Create, modify, save, and validate workflows
- **Node discovery**: List available nodes, models, and their parameters
- **Image generation**: Simple prompt-based generation or full workflow control

## Prerequisites

- [uv](https://docs.astral.sh/uv/) - Python package manager
- Running ComfyUI server (local or remote)
- Workflow files exported from ComfyUI (API format)

## Installation

```bash
# Install from source
git clone https://github.com/DanEscher98/comfy-mcp-server.git
cd comfy-mcp-server
uv sync
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COMFY_URL` | No | `http://localhost:8188` | ComfyUI server URL |
| `COMFY_URL_EXTERNAL` | No | Same as COMFY_URL | External URL for image retrieval |
| `COMFY_WORKFLOWS_DIR` | No | - | Directory containing workflow JSON files |
| `COMFY_WORKFLOW_JSON_FILE` | No | - | Default workflow file for `generate_image` |
| `PROMPT_NODE_ID` | No | - | Default prompt node ID for `generate_image` |
| `OUTPUT_NODE_ID` | No | - | Default output node ID |
| `OUTPUT_MODE` | No | `file` | Output mode: `file` (Image) or `url` (string URL) |
| `POLL_TIMEOUT` | No | `60` | Max seconds to wait for workflow (1-300) |
| `POLL_INTERVAL` | No | `1.0` | Seconds between status polls (0.1-10.0) |

### Example Configuration

```bash
export COMFY_URL=http://localhost:8188
export COMFY_WORKFLOWS_DIR=/path/to/workflows
export COMFY_WORKFLOW_JSON_FILE=/path/to/workflows/default.json
export PROMPT_NODE_ID=6
export OUTPUT_NODE_ID=9
export OUTPUT_MODE=file
```

### Claude Desktop Config

```json
{
  "mcpServers": {
    "ComfyUI": {
      "command": "uv",
      "args": ["--directory", "/path/to/comfy-mcp-server", "run", "comfy-mcp-server"],
      "env": {
        "COMFY_URL": "http://localhost:8188",
        "COMFY_WORKFLOWS_DIR": "/path/to/workflows",
        "COMFY_WORKFLOW_JSON_FILE": "/path/to/workflows/default.json",
        "PROMPT_NODE_ID": "6",
        "OUTPUT_NODE_ID": "9"
      }
    }
  }
}
```

## Available Tools

### System Tools

| Tool | Description |
|------|-------------|
| `get_system_stats()` | Get ComfyUI server health: version, memory, device info |
| `get_queue_status()` | Get current queue: running and pending jobs |
| `get_history(limit=10)` | Get recent generation history (1-100 entries) |
| `cancel_current(prompt_id=None)` | Interrupt current generation |
| `clear_queue(delete_ids=None)` | Clear queue or delete specific items |

### Discovery Tools

| Tool | Description |
|------|-------------|
| `list_nodes(filter=None)` | List available ComfyUI nodes (optional filter) |
| `get_node_info(node_name)` | Get detailed node info: inputs, outputs, parameters |
| `search_nodes(query)` | Search nodes by name, type, or category |
| `list_models(folder="checkpoints")` | List models in a folder |
| `list_model_folders()` | List available model folder types |
| `list_embeddings()` | List available embeddings |
| `list_extensions()` | List loaded extensions (custom node packs) |
| `refresh_nodes()` | Refresh cached node list from ComfyUI |

### Workflow Management Tools

| Tool | Description |
|------|-------------|
| `list_workflows()` | List available workflow files |
| `load_workflow(workflow_name)` | Load a workflow from file |
| `save_workflow(workflow, name)` | Save a workflow to file |
| `create_workflow()` | Create an empty workflow structure |
| `add_node(workflow, node_id, class_type, inputs)` | Add a node to a workflow |
| `remove_node(workflow, node_id)` | Remove a node from a workflow |
| `update_node_input(workflow, node_id, input_name, value)` | Update a node's input |
| `validate_workflow(workflow)` | Validate workflow structure and node types |
| `list_templates()` | List available workflow templates |
| `get_workflow_template(template_name)` | Get a pre-built workflow template |

### Execution Tools

| Tool | Description |
|------|-------------|
| `generate_image(prompt)` | Generate image using default workflow (simple interface) |
| `run_workflow(workflow_name, inputs=None, output_node_id=None)` | Execute a saved workflow file |
| `execute_workflow(workflow, output_node_id)` | Execute an arbitrary workflow dict |
| `submit_workflow(workflow)` | Submit workflow without waiting (returns prompt_id) |
| `get_prompt_status(prompt_id)` | Get status of a submitted prompt |
| `get_result_image(prompt_id, output_node_id)` | Get result image from completed prompt |

## Usage Examples

### Simple Image Generation

```python
# Using default workflow configuration
result = generate_image("a cyberpunk city at sunset")
```

### Run a Named Workflow

```python
# Execute saved workflow with custom inputs
result = run_workflow(
    "flux-dev.json",
    inputs={"6": {"text": "a forest landscape"}},
    output_node_id="9"
)
```

### Build and Execute Custom Workflow

```python
# 1. Create empty workflow
wf = create_workflow()

# 2. Add nodes
wf = add_node(wf, "1", "CheckpointLoaderSimple", {
    "ckpt_name": "flux-dev.safetensors"
})
wf = add_node(wf, "2", "CLIPTextEncode", {
    "text": "beautiful sunset over mountains",
    "clip": ["1", 1]  # Connect to checkpoint's CLIP output
})
wf = add_node(wf, "3", "KSampler", {
    "model": ["1", 0],
    "positive": ["2", 0],
    # ... other inputs
})

# 3. Execute
result = execute_workflow(wf, output_node_id="9")
```

### Async Workflow Submission

```python
# Submit without waiting
submission = submit_workflow(workflow)
prompt_id = submission["prompt_id"]

# Check status later
status = get_prompt_status(prompt_id)

# Get result when ready
if status["completed"]:
    image = get_result_image(prompt_id, "9")
```

### Discover Available Nodes

```python
# List all fal.ai nodes
nodes = list_nodes(filter="fal")

# Get details about a specific node
info = get_node_info("RemoteCheckpointLoader_fal")
```

### Using fal.ai Connector

The [ComfyUI-fal-Connector](https://github.com/badayvedat/ComfyUI-fal-Connector) enables cloud GPU inference via fal.ai.

```python
# 1. Verify fal.ai extension is loaded
extensions = list_extensions()
# Should include "ComfyUI-fal-Connector"

# 2. List available fal.ai nodes
fal_nodes = list_nodes(filter="fal")
# Returns: ["RemoteCheckpointLoader_fal", "StringInput_fal", "SaveImage_fal", ...]

# 3. Get node details
info = get_node_info("RemoteCheckpointLoader_fal")
# Shows available checkpoints: flux-dev, flux-schnell, sd3.5-large, etc.

# 4. Build a fal.ai workflow
wf = create_workflow()
wf = add_node(wf, "1", "RemoteCheckpointLoader_fal", {
    "ckpt_name": "flux-dev"
})
wf = add_node(wf, "2", "StringInput_fal", {
    "text": "a futuristic city at sunset, cyberpunk style"
})
wf = add_node(wf, "3", "CLIPTextEncode", {
    "text": ["2", 0],
    "clip": ["1", 1]
})
# ... add sampler, VAE decode, save image nodes

# 5. Execute on fal.ai cloud GPUs
result = execute_workflow(wf, output_node_id="9")
```

**Environment Setup:**
```bash
export FAL_KEY=your-fal-api-key
```

## Architecture

```
comfy_mcp_server/
├── __init__.py      # Entry point, FastMCP server
├── api.py           # HTTP helpers, ComfyUI API functions
├── models.py        # Pydantic models for type safety
├── settings.py      # Configuration with pydantic-settings
├── compat.py        # Version compatibility layer
└── tools/           # MCP tool implementations
    ├── system.py    # System monitoring tools
    ├── discovery.py # Node/model discovery
    ├── workflow.py  # Workflow management
    └── execution.py # Workflow execution
```

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run linting
uv run ruff check src/

# Run tests (requires running ComfyUI)
uv run pytest tests/

# Format code
uv run ruff format src/
```

## ComfyUI API Coverage

Target: **ComfyUI 0.3.x - 0.4.x**

| API Endpoint | Method | Description | Status |
|--------------|--------|-------------|--------|
| `/prompt` | POST | Submit workflow for execution | ✅ Implemented |
| `/queue` | GET | View running/pending jobs | ✅ Implemented |
| `/queue` | POST | Clear queue / delete items | ✅ Implemented |
| `/history` | GET | View generation history | ✅ Implemented |
| `/history/{id}` | GET | Get specific job result | ✅ Implemented |
| `/history` | POST | Delete history entries | ⚠️ Partial |
| `/interrupt` | POST | Stop current generation | ✅ Implemented |
| `/object_info` | GET | List all available nodes | ✅ Implemented |
| `/object_info/{node}` | GET | Get node parameters/inputs | ✅ Implemented |
| `/models` | GET | List model folders | ✅ Implemented |
| `/models/{folder}` | GET | List models in folder | ✅ Implemented |
| `/system_stats` | GET | Server health/resources | ✅ Implemented |
| `/view` | GET | Retrieve generated images | ✅ Implemented |
| `/embeddings` | GET | List available embeddings | ✅ Implemented |
| `/extensions` | GET | List loaded extensions | ✅ Implemented |
| `/upload/image` | POST | Upload image for workflows | ❌ Not implemented |
| `/upload/mask` | POST | Upload mask for inpainting | ❌ Not implemented |
| `/free` | POST | Free VRAM/memory | ❌ Not implemented |
| `/api/userdata/*` | * | User data management | ❌ Not implemented |

### Implementation Notes

- **Partial**: History deletion is not fully exposed as a tool
- **Not implemented**: Image/mask upload, memory management, and user data APIs are planned for future releases

## Compatibility

- **MCP Server Version**: 0.2.0
- **Minimum ComfyUI**: 0.3.0
- **Maximum Tested ComfyUI**: 0.4.x
- **Python**: 3.10+

The server includes a compatibility layer that handles API differences between ComfyUI versions and provides graceful degradation.

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Originally forked from [@lalanikarim/comfy-mcp-server](https://github.com/lalanikarim/comfy-mcp-server).
