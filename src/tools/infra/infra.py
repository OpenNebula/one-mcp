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

"""Infrastructure tools for OpenNebula MCP Server."""

from typing import Optional
import xml.etree.ElementTree as ET
from logging import getLogger
from src.tools.utils.base import execute_one_command
from src.static import HOST_STATES_DESCRIPTION, VM_IMAGES_STATES_DESCRIPTION

logger = getLogger("opennebula_mcp.tools.infra")


def register_tools(mcp):
    @mcp.tool(
        name="list_clusters",
        description="List all OpenNebula clusters accessible to the current user.",
    )
    def list_clusters() -> str:
        """List all OpenNebula clusters accessible to the current user.
        Returns:
            str: XML string conforming to Cluster Pool XSD Schema
        """
        logger.debug("Listing OpenNebula clusters")
        return execute_one_command(["onecluster", "list", "--xml"])

    @mcp.tool(
        name="list_hosts",
        description=f"""
            List compute hosts, optionally filtered by cluster ID. 
            {HOST_STATES_DESCRIPTION}
            """,
    )
    def list_hosts(cluster_id: Optional[str] = None) -> str:
        """List compute hosts, optionally filtered by cluster.
        Args:
            cluster_id: Optional[str]: Filter hosts by cluster ID
        Returns:
            str: XML string conforming to Host Pool XSD Schema
        """
        if cluster_id:
            logger.debug(f"Listing hosts for cluster {cluster_id}")
        else:
            logger.debug("Listing all hosts")

        result = execute_one_command(["onehost", "list", "--xml"])

        # If cluster_id is provided, filter the results
        if cluster_id and cluster_id.isdigit():
            logger.debug(f"Filtering hosts by cluster ID: {cluster_id}")
            try:
                root = ET.fromstring(result)
                # Filter hosts by cluster
                filtered_hosts = [
                    host
                    for host in root.findall("HOST")
                    if host.find("CLUSTER_ID").text == str(cluster_id)
                ]

                if not filtered_hosts:
                    logger.debug(f"No hosts found in cluster {cluster_id}")
                    return f"<error><message>No hosts found in cluster {cluster_id}</message></error>"

                logger.debug(
                    f"Found {len(filtered_hosts)} hosts in cluster {cluster_id}"
                )
                # Create new XML with filtered hosts
                new_root = ET.Element("HOST_POOL")
                for host in filtered_hosts:
                    new_root.append(host)
                return ET.tostring(new_root, encoding="unicode")

            except ET.ParseError as e:
                logger.error(f"Failed to parse host list XML: {str(e)}")
                return "<error><message>Failed to parse host list XML</message></error>"

        return result

    @mcp.tool(
        name="list_datastores",
        description="List available storage datastores and their types. Possible STATE values are 0 (READY) and 1 (DISABLE) only.",
    )
    def list_datastores() -> str:
        """List available storage datastores and their types.
        Returns:
            str: XML string conforming to Datastore Pool XSD Schema
        """
        logger.debug("Listing OpenNebula datastores")
        return execute_one_command(["onedatastore", "list", "--xml"])

    @mcp.tool(
        name="list_networks",
        description="List virtual networks available for VM connectivity.",
    )
    def list_networks() -> str:
        """List virtual networks available for VM connectivity.
        Returns:
            str: XML string conforming to VNet Pool XSD Schema
        """
        logger.debug("Listing OpenNebula networks")
        return execute_one_command(["onevnet", "list", "--xml"])

    @mcp.tool(
        name="list_images",
        description=f"""List virtual machine images available for VM creation.
        {VM_IMAGES_STATES_DESCRIPTION}
        """,
    )
    def list_images() -> str:
        """List virtual machine images available for VM creation.
        Returns:
            str: XML string conforming to Image Pool XSD Schema
        """
        logger.debug("Listing OpenNebula images")
        return execute_one_command(["oneimage", "list", "--xml"])
