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

"""Tenancy tools for OpenNebula MCP Server (Users, Groups, ACLs)."""

from typing import Optional
from logging import getLogger
import tempfile
import os
from src.tools.utils.base import execute_one_command

logger = getLogger("opennebula_mcp.tools.tenancy")


def register_tools(mcp, allow_write=False):
    
    # --- User Tools ---
    
    @mcp.tool(
        name="list_users",
        description="List all users.",
    )
    def list_users() -> str:
        """List all users.
        Returns:
            str: XML string with users
        """
        logger.debug("Listing users")
        return execute_one_command(["oneuser", "list", "--xml"])

    @mcp.tool(
        name="create_user",
        description="Create a new user.",
    )
    def create_user(
        name: str,
        password: str,
        auth_driver: Optional[str] = None,
    ) -> str:
        """Create a new user.
        Args:
            name: Username
            password: Password
            auth_driver: Authentication driver (optional, e.g., 'core', 'public', 'ldap')
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        cmd = ["oneuser", "create", name, password]
        if auth_driver:
            cmd.extend(["--driver", auth_driver])
            
        logger.debug(f"Creating user {name}")
        output = execute_one_command(cmd)
        
        # oneuser create returns "ID: <id>" on success
        if output.startswith("ID:"):
            user_id = output.split(":")[1].strip()
            return f"<success><message>User created successfully</message><user_id>{user_id}</user_id></success>"
        
        return output

    @mcp.tool(
        name="update_user_quota",
        description="Update user quotas.",
    )
    def update_user_quota(user_id: str, quota_template: str) -> str:
        """Update user quotas.
        Args:
            user_id: ID of the user
            quota_template: Quota definition in OpenNebula template format
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not user_id.isdigit():
            return "<error><message>user_id must be a non-negative integer</message></error>"

        logger.debug(f"Updating quotas for user {user_id}")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write(quota_template)
            tmp_path = tmp.name

        try:
            result = execute_one_command(["oneuser", "quota", user_id, tmp_path])
            if "Error" in result:
                 return f"<error><message>{result}</message></error>"
            return f"<success><message>Quotas updated for user {user_id}</message><user_id>{user_id}</user_id></success>"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @mcp.tool(
        name="delete_user",
        description="Delete a user.",
    )
    def delete_user(user_id: str) -> str:
        """Delete a user.
        Args:
            user_id: ID of the user to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not user_id.isdigit():
            return "<error><message>user_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting user {user_id}")
        result = execute_one_command(["oneuser", "delete", user_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>User {user_id} deleted successfully</message><user_id>{user_id}</user_id></success>"

    # --- Group Tools ---

    @mcp.tool(
        name="list_groups",
        description="List all groups.",
    )
    def list_groups() -> str:
        """List all groups.
        Returns:
            str: XML string with groups
        """
        logger.debug("Listing groups")
        return execute_one_command(["onegroup", "list", "--xml"])

    @mcp.tool(
        name="create_group",
        description="Create a new group.",
    )
    def create_group(name: str) -> str:
        """Create a new group.
        Args:
            name: Group name
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        logger.debug(f"Creating group {name}")
        output = execute_one_command(["onegroup", "create", name])
        
        # onegroup create returns "ID: <id>" on success
        if output.startswith("ID:"):
            group_id = output.split(":")[1].strip()
            return f"<success><message>Group created successfully</message><group_id>{group_id}</group_id></success>"
        
        return output

    @mcp.tool(
        name="add_user_to_group",
        description="Add a user to a group.",
    )
    def add_user_to_group(group_id: str, user_id: str, admin: bool = False) -> str:
        """Add a user to a group.
        Args:
            group_id: ID of the group
            user_id: ID of the user
            admin: If True, add as group admin
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not group_id.isdigit():
            return "<error><message>group_id must be a non-negative integer</message></error>"
        if not user_id.isdigit():
            return "<error><message>user_id must be a non-negative integer</message></error>"

        action = "add_admin" if admin else "add_user"
        logger.debug(f"Adding user {user_id} to group {group_id} (admin={admin})")
        
        result = execute_one_command(["onegroup", action, group_id, user_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>User {user_id} added to group {group_id}</message><group_id>{group_id}</group_id></success>"

    @mcp.tool(
        name="delete_group",
        description="Delete a group.",
    )
    def delete_group(group_id: str) -> str:
        """Delete a group.
        Args:
            group_id: ID of the group to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not group_id.isdigit():
            return "<error><message>group_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting group {group_id}")
        result = execute_one_command(["onegroup", "delete", group_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>Group {group_id} deleted successfully</message><group_id>{group_id}</group_id></success>"

    # --- ACL Tools ---

    @mcp.tool(
        name="list_acls",
        description="List all ACLs.",
    )
    def list_acls() -> str:
        """List all ACLs.
        Returns:
            str: XML string with ACLs
        """
        logger.debug("Listing ACLs")
        return execute_one_command(["oneacl", "list", "--xml"])

    @mcp.tool(
        name="create_acl",
        description="Create a new ACL rule.",
    )
    def create_acl(user: str, resources: str, rights: str) -> str:
        """Create a new ACL rule.
        Args:
            user: User component (e.g., '#<id>', '@<id>', '*')
            resources: Resources component (e.g., 'VM+NET/#<id>')
            rights: Rights component (e.g., 'USE+MANAGE')
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        # Construct the rule string
        rule = f"{user} {resources} {rights}"
        
        logger.debug(f"Creating ACL rule: {rule}")
        output = execute_one_command(["oneacl", "create", rule])
        
        # oneacl create returns "ID: <id>" on success
        if output.startswith("ID:"):
            acl_id = output.split(":")[1].strip()
            return f"<success><message>ACL created successfully</message><acl_id>{acl_id}</acl_id></success>"
        
        return output

    @mcp.tool(
        name="delete_acl",
        description="Delete an ACL rule.",
    )
    def delete_acl(acl_id: str) -> str:
        """Delete an ACL rule.
        Args:
            acl_id: ID of the ACL rule to delete
        Returns:
            str: XML string with success message or error
        """
        if not allow_write:
            return "<error><message>Write operations are disabled</message></error>"

        if not acl_id.isdigit():
            return "<error><message>acl_id must be a non-negative integer</message></error>"

        logger.debug(f"Deleting ACL {acl_id}")
        result = execute_one_command(["oneacl", "delete", acl_id])
        
        if "Error" in result:
             return f"<error><message>{result}</message></error>"

        return f"<success><message>ACL {acl_id} deleted successfully</message><acl_id>{acl_id}</acl_id></success>"
