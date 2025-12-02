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
import tempfile
import os
from src.tools.utils.base import execute_one_command
from src.static import HOST_STATES_DESCRIPTION, VM_IMAGES_STATES_DESCRIPTION

logger = getLogger("opennebula_mcp.tools.infra")


def register_tools(mcp, allow_write=False):
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

    @mcp.tool(
        name="create_image",
        description="Create a new image in the datastore.",
    )
    def create_image(
        name: str,
        path: str,
        datastore_id: str,
        type: str = "OS",
        prefix: str = "vd",
        persistent: bool = False,
    ) -> str:
        """Create a new image.
        Args:
            name: Name of the new image
            path: Path to the image file
            datastore_id: ID of the datastore to place the image in
            type: Type of the image (OS, CDROM, DATABLOCK, KERNEL, RAMDISK, CONTEXT)
            prefix: Device prefix (vd, sd, hd, etc.)
            persistent: Whether the image is persistent
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not datastore_id.isdigit():
            return "<error><message>datastore_id must be a non-negative integer</message></error>"

        cmd = [
            "oneimage",
            "create",
            "--name",
            name,
            "--path",
            path,
            "--datastore",
            datastore_id,
            "--type",
            type,
            "--prefix",
            prefix,
        ]

        if persistent:
            cmd.append("--persistent")

        logger.debug(f"Creating image {name} in datastore {datastore_id}")
        output = execute_one_command(cmd)
        
        # oneimage create returns "ID: <id>" on success
        if output.startswith("ID:"):
            image_id = output.split(":")[1].strip()
            return f"<success><message>Image created successfully</message><image_id>{image_id}</image_id></success>"
        
        return output

    @mcp.tool(
        name="delete_image",
        description="Delete an image.",
    )
    def delete_image(image_id: str) -> str:
        """Delete an image.
        Args:
            image_id: ID of the image to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not image_id.isdigit():
            return "<error><message>image_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting image {image_id}")
        result = execute_one_command(["oneimage", "delete", image_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Image {image_id} deleted successfully</message><image_id>{image_id}</image_id></success>"

    @mcp.tool(
        name="update_image_type",
        description="Change the type of an image.",
    )
    def update_image_type(image_id: str, type: str) -> str:
        """Change the type of an image.
        Args:
            image_id: ID of the image
            type: New type (OS, CDROM, DATABLOCK, KERNEL, RAMDISK, CONTEXT)
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not image_id.isdigit():
            return "<error><message>image_id must be a non-negative integer</message></error>"

        logger.debug(f"Changing type of image {image_id} to {type}")
        result = execute_one_command(["oneimage", "chtype", image_id, type])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Image {image_id} type updated to {type}</message><image_id>{image_id}</image_id></success>"

    @mcp.tool(
        name="create_vnet",
        description="Create a new virtual network from a template string.",
    )
    def create_vnet(template_content: str) -> str:
        """Create a new virtual network.
        Args:
            template_content: Content of the network template
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        # Create a temporary file for the template
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                temp_file.write(template_content)
                temp_file_path = temp_file.name
        except Exception as e:
            logger.error(f"Failed to create temporary file: {str(e)}")
            return f"<error><message>Failed to create temporary file: {str(e)}</message></error>"

        try:
            logger.debug("Creating new virtual network from template")
            output = execute_one_command(["onevnet", "create", temp_file_path])
            
            # onevnet create returns "ID: <id>" on success
            if output.startswith("ID:"):
                vnet_id = output.split(":")[1].strip()
                return f"<success><message>Virtual network created successfully</message><vnet_id>{vnet_id}</vnet_id></success>"
            
            return output
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    @mcp.tool(
        name="delete_vnet",
        description="Delete a virtual network.",
    )
    def delete_vnet(vnet_id: str) -> str:
        """Delete a virtual network.
        Args:
            vnet_id: ID of the virtual network to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not vnet_id.isdigit():
            return "<error><message>vnet_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting virtual network {vnet_id}")
        result = execute_one_command(["onevnet", "delete", vnet_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Virtual network {vnet_id} deleted successfully</message><vnet_id>{vnet_id}</vnet_id></success>"

    @mcp.tool(
        name="reserve_vnet",
        description="Reserve addresses from a virtual network.",
    )
    def reserve_vnet(vnet_id: str, size: str, name: Optional[str] = None) -> str:
        """Reserve addresses from a virtual network.
        Args:
            vnet_id: ID of the virtual network
            size: Number of addresses to reserve
            name: Name of the new reservation (optional)
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not vnet_id.isdigit():
            return "<error><message>vnet_id must be a non-negative integer</message></error>"
        
        if not size.isdigit():
             return "<error><message>size must be a non-negative integer</message></error>"

        cmd = ["onevnet", "reserve", vnet_id, "--size", size]
        if name:
            cmd.extend(["--name", name])

        logger.debug(f"Reserving {size} addresses from vnet {vnet_id}")
        output = execute_one_command(cmd)
        
        # onevnet reserve returns "ID: <id>" on success (ID of the new reservation VNET)
        if output.startswith("ID:"):
            reservation_id = output.split(":")[1].strip()
            return f"<success><message>Network reservation created successfully</message><reservation_id>{reservation_id}</reservation_id></success>"
        
        return output

    @mcp.tool(
        name="enable_host",
        description="Enable a host.",
    )
    def enable_host(host_id: str) -> str:
        """Enable a host.
        Args:
            host_id: ID of the host to enable
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not host_id.isdigit():
            return "<error><message>host_id must be a non-negative integer</message></error>"

        logger.debug(f"Enabling host {host_id}")
        result = execute_one_command(["onehost", "enable", host_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Host {host_id} enabled successfully</message><host_id>{host_id}</host_id></success>"

    @mcp.tool(
        name="disable_host",
        description="Disable a host.",
    )
    def disable_host(host_id: str) -> str:
        """Disable a host.
        Args:
            host_id: ID of the host to disable
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not host_id.isdigit():
            return "<error><message>host_id must be a non-negative integer</message></error>"

        logger.debug(f"Disabling host {host_id}")
        result = execute_one_command(["onehost", "disable", host_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Host {host_id} disabled successfully</message><host_id>{host_id}</host_id></success>"

    @mcp.tool(
        name="host_monitoring",
        description="Show monitoring information for a host.",
    )
    def host_monitoring(host_id: str) -> str:
        """Show monitoring information for a host.
        Args:
            host_id: ID of the host
        Returns:
            str: XML string with host details
        """
        # Read-only operation, no allow_write check needed
        if not host_id.isdigit():
            return "<error><message>host_id must be a non-negative integer</message></error>"

        logger.debug(f"Getting monitoring info for host {host_id}")
        return execute_one_command(["onehost", "show", host_id, "--xml"])
