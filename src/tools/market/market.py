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

"""Marketplace tools for OpenNebula MCP Server."""

from typing import Optional
from logging import getLogger
import xml.etree.ElementTree as ET
from src.tools.utils.base import execute_one_command

logger = getLogger("opennebula_mcp.tools.market")


def register_tools(mcp, allow_write=False):
    @mcp.tool(
        name="list_markets",
        description="List available marketplaces.",
    )
    def list_markets() -> str:
        """List available marketplaces.
        Returns:
            str: XML string with marketplaces
        """
        logger.debug("Listing marketplaces")
        return execute_one_command(["onemarket", "list", "--xml"])

    @mcp.tool(
        name="search_market_apps",
        description="""List or search for appliances in the marketplace by name, description, or tags (case-insensitive).
        
        **IMPORTANT**: Use this tool when the user requests to "list all marketplace apps" or "show marketplace apps". 
        The `list_markets` tool lists marketplaces (repositories), NOT the apps within them. This tool lists the actual 
        marketplace applications/appliances.
        
        If no filter_str is provided, returns ALL marketplace apps. If filter_str is provided, performs a case-insensitive 
        search in NAME, DESCRIPTION, and TAGS fields.""",
    )
    def search_market_apps(filter_str: Optional[str] = None) -> str:
        """Search for appliances in the marketplace.
        Args:
            filter_str: Optional string to filter results. Performs case-insensitive search in NAME, DESCRIPTION, and TAGS fields.
                       If not provided, returns all marketplace apps.
        Returns:
            str: XML string with marketplace apps matching the filter
        """
        logger.debug(f"Searching marketplace apps with filter: {filter_str}")
        
        # Get full XML output (filter doesn't work with --xml, so we filter client-side)
        cmd = ["onemarketapp", "list", "--xml"]
        result = execute_one_command(cmd)
        
        # If no filter is provided, return all apps
        if not filter_str:
            return result
        
        # Parse XML and filter by name, description, or tags (case-insensitive)
        try:
            root = ET.fromstring(result)
            filter_lower = filter_str.lower()
            
            # Find all MARKETPLACEAPP elements
            filtered_apps = []
            for app in root.findall(".//MARKETPLACEAPP"):
                # Check if filter matches name, description, or tags (case-insensitive)
                name_elem = app.find("NAME")
                desc_elem = app.find("DESCRIPTION")
                tags_elem = app.find("TAGS")
                
                matches = False
                if name_elem is not None and name_elem.text and filter_lower in name_elem.text.lower():
                    matches = True
                elif desc_elem is not None and desc_elem.text and filter_lower in desc_elem.text.lower():
                    matches = True
                elif tags_elem is not None and tags_elem.text and filter_lower in tags_elem.text.lower():
                    matches = True
                
                if matches:
                    filtered_apps.append(app)
            
            # If no matches found, return empty result
            if not filtered_apps:
                return "<MARKETPLACEAPP_POOL></MARKETPLACEAPP_POOL>"
            
            # Create new XML with filtered apps
            new_root = ET.Element("MARKETPLACEAPP_POOL")
            for app in filtered_apps:
                new_root.append(app)
            
            return ET.tostring(new_root, encoding="unicode")
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse marketplace apps XML: {e}")
            # If parsing fails, return the original result
            return result

    @mcp.tool(
        name="import_market_app",
        description="Import an appliance from the marketplace to a datastore.",
    )
    def import_market_app(
        app_id: str,
        datastore_id: str,
        name: Optional[str] = None,
    ) -> str:
        """Import an appliance from the marketplace.
        Args:
            app_id: ID of the marketplace appliance
            datastore_id: ID of the datastore to import into
            name: Optional name for the new image
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not app_id.isdigit():
            return "<error><message>app_id must be a non-negative integer</message></error>"
        if not datastore_id.isdigit():
            return "<error><message>datastore_id must be a non-negative integer</message></error>"

        cmd = ["onemarketapp", "export", app_id, name if name else "", "--datastore", datastore_id]
        # Note: 'export' syntax is: onemarketapp export <app_id> <name> --datastore <ds_id>
        # If name is empty, it uses the app name. We need to handle the empty name case carefully.
        # If name is None, we shouldn't pass an empty string as a positional arg if it confuses the parser,
        # but looking at CLI help: `onemarketapp export <app_id> [name] [options]`
        
        final_cmd = ["onemarketapp", "export", app_id]
        if name:
            final_cmd.append(name)
        
        final_cmd.extend(["--datastore", datastore_id])

        logger.debug(f"Importing market app {app_id} to datastore {datastore_id}")
        output = execute_one_command(final_cmd)
        
        # onemarketapp export returns "IMAGE ID: <id>" or similar on success
        if "ID:" in output:
             # Extract ID if possible, or just return success
             return f"<success><message>Appliance imported successfully</message><output>{output}</output></success>"
        
        return output
