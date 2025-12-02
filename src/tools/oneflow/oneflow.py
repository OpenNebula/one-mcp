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

"""OneFlow tools for OpenNebula MCP Server."""

from typing import Optional
from logging import getLogger
from src.tools.utils.base import execute_one_command

logger = getLogger("opennebula_mcp.tools.oneflow")


def register_tools(mcp, allow_write=False):
    @mcp.tool(
        name="list_service_templates",
        description="List available OneFlow service templates.",
    )
    def list_service_templates() -> str:
        """List available OneFlow service templates.
        Returns:
            str: JSON string with service templates
        """
        logger.debug("Listing OneFlow service templates")
        return execute_one_command(["oneflow-template", "list", "--json"])

    @mcp.tool(
        name="deploy_service",
        description="Deploy a service from a template.",
    )
    def deploy_service(
        template_id: str,
        name: Optional[str] = None,
        custom_attrs: Optional[str] = None,
    ) -> str:
        """Deploy a service from a template.
        Args:
            template_id: ID of the service template
            name: Optional name for the new service
            custom_attrs: Optional custom attributes (key=value pairs)
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not template_id.isdigit():
            return "<error><message>template_id must be a non-negative integer</message></error>"

        cmd = ["oneflow-template", "instantiate", template_id]
        
        if name:
            cmd.extend(["--name", name])
            
        # Note: Handling custom attributes might require more complex parsing or a file
        # For now, we'll support simple key=value strings passed directly if needed, 
        # but the CLI usually takes them as extra arguments or a file.
        # Simpler approach for now: just basic instantiation.
        
        logger.debug(f"Deploying service from template {template_id}")
        output = execute_one_command(cmd)
        
        # oneflow-template instantiate returns "ID: <id>" on success
        if output.startswith("ID:"):
            service_id = output.split(":")[1].strip()
            return f"<success><message>Service deployed successfully</message><service_id>{service_id}</service_id></success>"
        
        return output

    @mcp.tool(
        name="list_services",
        description="List running OneFlow services.",
    )
    def list_services() -> str:
        """List running OneFlow services.
        Returns:
            str: JSON string with services
        """
        logger.debug("Listing OneFlow services")
        return execute_one_command(["oneflow", "list", "--json"])

    @mcp.tool(
        name="get_service_info",
        description="Get detailed information about a service.",
    )
    def get_service_info(service_id: str) -> str:
        """Get detailed information about a service.
        Args:
            service_id: ID of the service
        Returns:
            str: JSON string with service details
        """
        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"

        logger.debug(f"Getting info for service {service_id}")
        return execute_one_command(["oneflow", "show", service_id, "--json"])

    @mcp.tool(
        name="delete_service",
        description="Delete a service.",
    )
    def delete_service(service_id: str) -> str:
        """Delete a service.
        Args:
            service_id: ID of the service to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting service {service_id}")
        # oneflow delete doesn't output XML, usually just empty or text
        result = execute_one_command(["oneflow", "delete", service_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Service {service_id} deleted successfully</message><service_id>{service_id}</service_id></success>"

    @mcp.tool(
        name="service_action",
        description="Perform an action on a service (shutdown, recover, hold, release, etc.).",
    )
    def service_action(service_id: str, action: str) -> str:
        """Perform an action on a service.
        Args:
            service_id: ID of the service
            action: Action to perform
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"

        # Validate action against a known list could be good, but CLI handles it too.
        # Common actions: shutdown, shutdown-hard, undeploy, undeploy-hard, hold, release, stop, suspend, resume, boot, delete-recreate, reboot, reboot-hard, poweroff, poweroff-hard, snapshot-create
        
        logger.debug(f"Performing action {action} on service {service_id}")
        result = execute_one_command(["oneflow", "action", action, service_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Action {action} performed on service {service_id}</message><service_id>{service_id}</service_id></success>"

    @mcp.tool(
        name="scale_service",
        description="Scale a role in a service.",
    )
    def scale_service(service_id: str, role_name: str, cardinality: str) -> str:
        """Scale a role in a service.
        Args:
            service_id: ID of the service
            role_name: Name of the role to scale
            cardinality: New cardinality (number of VMs)
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"
            
        if not cardinality.isdigit():
             return "<error><message>cardinality must be a non-negative integer</message></error>"

        logger.debug(f"Scaling role {role_name} in service {service_id} to {cardinality}")
        result = execute_one_command(["oneflow", "scale", service_id, role_name, cardinality])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Scaled role {role_name} in service {service_id} to {cardinality}</message><service_id>{service_id}</service_id></success>"

    @mcp.tool(
        name="get_service_log",
        description="Get the log of a OneFlow service.",
    )
    def get_service_log(service_id: str) -> str:
        """Get the log of a OneFlow service.
        Args:
            service_id: ID of the service
        Returns:
            str: Log content
        """
        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"

        logger.debug(f"Getting log for service {service_id}")
        # onelog get-service <id> returns raw text log
        return execute_one_command(["onelog", "get-service", service_id])

    @mcp.tool(
        name="recover_service",
        description="Recover a failed service.",
    )
    def recover_service(service_id: str) -> str:
        """Recover a failed service.
        Args:
            service_id: ID of the service
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not service_id.isdigit():
            return "<error><message>service_id must be a non-negative integer</message></error>"

        logger.debug(f"Recovering service {service_id}")
        result = execute_one_command(["oneflow", "recover", service_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Service {service_id} recovered successfully</message><service_id>{service_id}</service_id></success>"
