"""Main entry point for the Pivot.AI MCP Server (Dynamic SOPs & Resources)."""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, List
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.resources import FileResource

from pivot_mcp.tools.ingestion import ingest_jobs
from pivot_mcp.tools.scoring import score_job, list_matches

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pivot-ai-mcp")

# Initialize FastMCP server
mcp = FastMCP("Pivot.AI Core")

# --- Explicit Tool Registration (Programmatic) ---

tools_to_register = [
    ingest_jobs,
    score_job,
    list_matches
]

for t in tools_to_register:
    mcp.add_tool(t)
    logger.info(f"Registered Tool: {t.__name__}")

# --- Configuration Paths ---
ROOT = Path.home() / ".pivot-ai"
RESOURCE_ROOT = ROOT / "resources"
SOP_ROOT = ROOT / "sops"

for p in [RESOURCE_ROOT, SOP_ROOT]:
    p.mkdir(parents=True, exist_ok=True)

# --- Dynamic MCP Resources ---

def register_filesystem_resources():
    """Register all files in ~/.pivot-ai/resources as static resources."""
    for file in RESOURCE_ROOT.glob("*"):
        if file.suffix in [".md", ".txt"]:
            try:
                uri = f"pivot://user/{file.name}"
                mcp.add_resource(FileResource(
                    uri=uri,
                    name=file.stem.capitalize(),
                    description=f"Personal context from {file.name}",
                    path=file
                ))
                logger.info(f"Registered Resource: {uri}")
            except Exception as e:
                logger.error(f"Failed to register resource {file.name}: {e}")

# --- Dynamic MCP SOPs ---

def parse_sop(file_path: Path):
    """Extract instructions and variables from a Markdown file."""
    content = file_path.read_text()
    title_match = re.search(r"^#\s+(.*)", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem.capitalize()
    variables = sorted(list(set(re.findall(r"\{\{([a-zA-Z0-9_-]+)\}\}", content))))
    return {
        "name": file_path.stem.lower().replace(" ", "-"),
        "title": title,
        "content": content,
        "variables": variables
    }

def register_filesystem_sops():
    """Register all Markdown files in ~/.pivot-ai/sops as prompts (SOPs)."""
    for file in SOP_ROOT.glob("*.md"):
        sop = parse_sop(file)
        
        # Closure-safe handler
        # Note: We use the decorator as a function call
        def make_handler(instructions):
            async def handler(arguments: dict = None) -> str:
                final = instructions
                if arguments:
                    for k, v in arguments.items():
                        final = final.replace(f"{{{{{k}}}}}", str(v))
                return final
            return handler

        # Correct FastMCP decorator usage for programmatic registration
        mcp.prompt(name=sop["name"], description=f"SOP: {sop['title']}")(make_handler(sop["content"]))
        logger.info(f"Registered SOP: {sop['name']}")

# Run registry loops
register_filesystem_resources()
register_filesystem_sops()

# --- Helper Skills ---

@mcp.resource("pivot://user/{filename}")
async def get_dynamic_resource(filename: str) -> str:
    """Read any user context file (Template mode)"""
    path = RESOURCE_ROOT / Path(filename).name
    return path.read_text() if path.exists() else "File not found."

@mcp.tool()
async def health_check() -> str:
    """Check if the MCP server is alive."""
    return "✅ Pivot.AI Core MCP is Online."

async def async_main():
    """Asynchronous entry point."""
    logger.info("🚀 Starting Pivot.AI Core (Unified Registry Mode)...")
    await mcp.run_stdio_async()

def main():
    """Synchronous entry point."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
