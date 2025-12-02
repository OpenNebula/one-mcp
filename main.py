# Copyright 2002-2025, OpenNebula Project, OpenNebula Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mcp.server.fastmcp import FastMCP
from src.static import MCP_SERVER_PROMPT
from src.tools import infra, templates, vm, oneflow, tenancy, market
from src.logging_config import setup_logging
import argparse
from logging import getLogger

mcp = FastMCP(name="opennebula-mcp-server", instructions=MCP_SERVER_PROMPT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="An OpenNebula Model Context Protocol (MCP) server for OpenNebula"
    )

    # To enable/disable write access to the VM, add or remove the --allow-write flag the mcp.json file.
    parser.add_argument(
        "--allow-write",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable write access mode (allow mutating operations)",
    )

    # Logging configuration arguments
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level (default: INFO, or LOG_LEVEL env var)",
    )

    parser.add_argument(
        "--log-file",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable file logging with automatic timestamped filename in ./log directory",
    )

    args = parser.parse_args()

    # Setup logging before any other operations
    setup_logging(level=args.log_level, enable_file_logging=args.log_file)

    # Get logger for this module
    logger = getLogger("opennebula_mcp.main")

    allow_write = True if args.allow_write else False

    # Register tool modules
    infra.register_tools(mcp, allow_write)
    vm.register_tools(mcp, allow_write)
    templates.register_tools(mcp, allow_write)
    oneflow.register_tools(mcp, allow_write)
    tenancy.register_tools(mcp, allow_write)
    market.register_tools(mcp, allow_write)

    logger.info(f"Starting MCP server - allow_write: {allow_write}")

    mcp.run()
