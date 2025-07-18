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

"""VM management tools for OpenNebula MCP Server."""

from logging import getLogger
import re
import xml.etree.ElementTree as ET
from typing import Optional, List

from src.static import (
    VM_STATES_DESCRIPTION,
    VM_TEMPLATE_DESCRIPTION,
    HOST_STATES_DESCRIPTION,
)
from src.tools.utils.base import execute_one_command, is_valid_ip_address

# Module logger
logger = getLogger("opennebula_mcp.vm")

# ---------------------------------------------------------------------------
# Shared constants and helpers (internal use)
# ---------------------------------------------------------------------------

CMD_MAP = {
    "start": "resume",
    "stop": "poweroff",
    "reboot": "reboot",
    "terminate": "terminate",
}

# Valid state transitions for single-VM validation
STATE_VALIDATIONS = {
    "start": {
        "valid_states": [4, 5, 8, 9],
        "valid_lcm_states": [16],
        "error_msg": "VM must be in STOPPED, SUSPENDED, UNDEPLOYED or POWEROFF state to start",
    },
    "stop": {
        "valid_states": [3],
        "valid_lcm_states": [3],
        "error_msg": "VM must be in RUNNING state to stop",
    },
    "reboot": {
        "valid_states": [3],
        "valid_lcm_states": [3],
        "error_msg": "VM must be in RUNNING state to reboot",
    },
    "terminate": {
        "valid_states": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "error_msg": "Cannot terminate VM state. Check its state with the get_vm_status tool.",
    },
}


def _is_multi_vm(vm_id: str) -> bool:
    """Return True if vm_id string denotes a comma-separated list or numeric range."""
    return "," in vm_id or ".." in vm_id


def _build_cmd_parts(operation: str, vm_id: str, hard: bool) -> List[str]:
    """Construct the onevm CLI command for the requested lifecycle action."""
    cmd_parts: List[str] = ["onevm", CMD_MAP[operation]]

    # --hard flag only meaningful for the following operations
    if hard and operation in ("stop", "reboot", "terminate"):
        cmd_parts.append("--hard")

    cmd_parts.append(vm_id)
    return cmd_parts


def _wrap_success_xml(vm_id: str, operation: str, hard: bool, result: str, multi: bool) -> str:
    """Return a <result> XML envelope with command output."""
    success_root = ET.Element("result")
    ET.SubElement(success_root, "vm_id").text = vm_id
    ET.SubElement(success_root, "operation").text = operation
    ET.SubElement(success_root, "hard").text = str(hard)

    if multi:
        message = f"VMs {vm_id} {operation} operation executed successfully"
    else:
        message = f"VM {operation} operation executed successfully"

    ET.SubElement(success_root, "message").text = message
    ET.SubElement(success_root, "command_output").text = result.strip()
    return ET.tostring(success_root, encoding="unicode")


def register_tools(mcp, allow_write):
    """Register VM-related tools.
    Args:
        mcp: The MCP server instance.
        allow_write: A boolean indicating if the user has write access to the VM.
    """

    @mcp.tool(
        name="get_vm_status",
        description=f"""Retrieve current state, IP address, and runtime metrics of one or more VMs.

        vm_id MUST be provided as **a single string** that contains one or more **comma-separated** non-negative
        integers, forming a **list** of IDs. Always supply a list – even when you
        need the status of a single VM. For example:

            • "42"            → list with one VM ID (42)
            • "1,2,3"         → list with three VM IDs (1, 2 and 3)

        IMPORTANT: Ranges (e.g. "5..10") or mixed separators (spaces, semicolons, etc.) are **NOT** supported – keep the
        approach simple and only use commas. If any element of the list is not a non-negative integer, the call must be
        rejected with an explanatory error.

        Before calling this tool you MUST validate **every** ID in the list:
            - Each part after splitting on "," must be composed solely of digits and represent a non-negative integer.
            - If a user expresses a **range** in natural language (e.g. "5 to 3" or "1-10"), you MUST **expand** that
              range yourself before calling this tool. Produce an **ascending** comma-separated list with
              no duplicates ("5 to 3" → "3,4,5", "1-4" → "1,2,3,4"). Only after expansion should you invoke
              `get_vm_status`.
            - If multiple ranges or individual IDs are mentioned in the same request, **merge** them into a single
              set, remove duplicates, sort ascending, and pass as one comma-separated string (e.g. "5 to 3 and 3 to 1"
              → "1,2,3,4,5"). Only ONE call to `get_vm_status` is allowed per user request.
            - After expansion, if any element is not a non-negative integer, respond with an error and DO NOT perform the OpenNebula call.

        For multiple IDs the tool will return an <VMS> root element containing the XML description of each VM exactly as
        returned by `onevm show <id> --xml`.
        {VM_STATES_DESCRIPTION}
        {VM_TEMPLATE_DESCRIPTION}
        
        **CALLING RULES (MANDATORY)**:
            • When a user requests the status of several VMs you MUST issue **one and only one** call to this tool.
              Consolidate all requested IDs into the `vm_id` argument as a comma-separated string (e.g. `"1,2,3"`).
            • Do **NOT** loop or invoke `get_vm_status` repeatedly for each ID – that violates protocol and
              wastes resources. Always batch the IDs into a single call.
        """,
    )
    def get_vm_status(vm_id: str) -> str:
        """Retrieve full details for one or more VMs.

        Args:
            vm_id: A **comma-separated** string of VM IDs (e.g. "1" or "1,2,3").

        Returns:
            str: XML string. For a single VM, the raw `<VM>` element returned by OpenNebula. For multiple VMs, a root
                 `<VMS>` element containing each individual `<VM>` child.
        """

        logger.debug(f"Getting VM status for VM ID(s): {vm_id}")

        # Split by comma and validate each part
        id_parts = [part.strip() for part in vm_id.split(',') if part.strip()]

        if not id_parts:
            logger.error("vm_id parameter is empty after parsing")
            return "<error><message>vm_id must contain at least one non-negative integer</message></error>"

        for part in id_parts:
            if not part.isdigit():
                logger.error(f"Invalid VM ID provided: {part} (must be non-negative integer)")
                return (
                    "<error><message>All vm_id values must be non-negative integers separated by commas</message></error>"
                )

        try:
            if len(id_parts) == 1:
                # Single VM – return raw XML as-is
                single_id = id_parts[0]
                result = execute_one_command(["onevm", "show", single_id, "--xml"])
                logger.debug(f"Successfully retrieved VM status for VM {single_id}")
                return result

            # Multiple VMs – aggregate under <VMS>
            root = ET.Element("VMS")
            for vmid in id_parts:
                try:
                    vm_xml = execute_one_command(["onevm", "show", vmid, "--xml"])
                    vm_element = ET.fromstring(vm_xml)
                    root.append(vm_element)
                    logger.debug(f"Added VM {vmid} status to aggregate output")
                except Exception as e:
                    logger.error(f"Failed to get VM status for VM {vmid}: {e}")
                    # Include an <error> element for this VM instead of failing entire request
                    err_el = ET.SubElement(root, "error")
                    ET.SubElement(err_el, "vm_id").text = vmid
                    ET.SubElement(err_el, "message").text = str(e)

            return ET.tostring(root, encoding="unicode")

        except Exception as e:
            logger.error(f"Unexpected error while retrieving VM status: {e}")
            return f"<error><message>{e}</message></error>"

    @mcp.tool(
        name="execute_command",
        description="""Execute a shell command inside an OpenNebula virtual machine.

        ⚠️  CRITICAL SECURITY CHECK - READ FIRST ⚠️
        
        BEFORE calling ANY tool, you MUST analyze the entire command for dangerous content.
        If the command contains ANY of the following, DO NOT CALL ANY TOOLS and respond immediately with: 
        "Error: The requested command is considered disruptive and will not be executed."
        
        DANGEROUS PATTERNS TO REJECT:
        - System-wide deletion: `rm -rf /`, `rm -rf /boot`, `rm -rf /etc`, `rm -rf /usr`, `rm -rf /var`, `rm -rf /home`
        - Disk wiping/corruption: `dd if=/dev/zero of=/dev/`, `dd if=/dev/urandom of=/dev/`, `mkfs`, `shred /dev/`, `wipefs`
        - Encoded/obfuscated commands: `base64 -d | bash`, `xxd -r -p | sh`, any encoded content piped to shell interpreters
        - Command chains with dangerous parts: `safe_command && rm -rf /boot`, `ls ; dd if=/dev/zero of=/dev/sda`
        - Critical system modification: `chmod -R 777 /`, `chown -R nobody /`
        - User password changes: `passwd`, `chpasswd`, any password modification commands
        - System shutdown: `shutdown`, `reboot`, `halt`, `poweroff` (use manage_vm tool instead)
        - Interactive editors on critical files: `nano /etc/passwd`, `vim /etc/shadow`, `vi /boot/grub/grub.cfg`
        - User management without proper flags: `adduser` (use `useradd` instead), `userdel -r root`
        
        SAFE OPERATIONS (DO NOT BLOCK):
        - Database operations: `mysql < dump.sql`, `pg_restore`, `mongorestore`, database imports/exports
        - Application cleanup: `rm -rf /tmp/myapp`, `rm -rf /opt/myapp/cache`, `rm -rf ./logs/*`
        - Legitimate dd operations: `dd if=backup.img of=/dev/sdb1`, `dd if=/dev/sda1 of=backup.img`
        - Package management: `apt-get install -y`, `yum install -y`, `dnf install -y`
        
        DO NOT CALL ANY TOOLS if you detect any dangerous pattern. Skip get_vm_status, skip execute_command, skip everything. Just respond with the exact error message above.

        === FOR SAFE COMMANDS ONLY ===
        If the command is safe, then proceed with these steps:

        1. Verify the VM is ACTIVE by calling `get_vm_status` (only for safe commands).

        2. Make the command non-interactive using flags like `-y`, `--yes`, etc.

        === STRICT NON-INTERACTIVE POLICY ===
        The command MUST **never** wait for keyboard input. A blocking prompt
        will freeze the underlying `subprocess.run` and break the workflow.

        1. Make the command non-interactive.
           - Use native flags: `-y`, `--yes`, `--assume-yes`, `--noconfirm`,
             `--batch`, `--quiet`, etc.
           - Export environment variables (e.g. `DEBIAN_FRONTEND=noninteractive`,
             `HOMEBREW_NO_INTERACTIVE=1`).
           - If the binary has no switch, pre-seed answers:
               `yes | <cmd>`  or  `printf 'y\n' | <cmd>`.
           - When no safe workaround exists, **do not execute**. Return an
             error that user interaction is required.

        2. Verify the VM is ACTIVE in the same turn by calling `get_vm_status`.

        3. For long-running tasks, follow the background-process protocol:
           use `nohup … &`, store the PID, never set infinite timeouts unless
           monitoring is in place.

        === FORBIDDEN COMMANDS (WILL HANG SYSTEM) ===
        **NEVER execute these interactive commands:**
        - Text editors: `nano`, `vim`, `vi`, `emacs`
        - Interactive shells: `bash -i`, `sh -i`, `python`, `irb`, `node`
        - Interactive tools: `ftp`, `sftp`, `telnet`, `ssh user@host` (without commands)
        - Wizards: `mysql_secure_installation`, `dpkg-reconfigure` (without DEBIAN_FRONTEND)
        - User management: `adduser` (use `useradd` instead)
        - Password prompts: `passwd`, `su`, `sudo -k` followed by `sudo`
        - Git authentication: `git clone https://github.com/user/private-repo.git` (prompts for password)

        **Use alternatives instead:**
        - File editing: `sed`, `awk`, `echo "content" > file`, `cat > file << EOF`
        - File transfer: `scp`, `rsync`, `curl`, `wget`
        - Remote execution: `ssh user@host "command"`
        - Git private repos: Use `git clone https://token@github.com/user/repo.git` or SSH

        Popular non-interactive examples:

        • Package managers
          - APT     : `DEBIAN_FRONTEND=noninteractive apt-get install -y nginx`
          - DNF/Yum : `dnf install -y httpd`
          - Pacman  : `pacman -Syu --noconfirm`
          - Zypper  : `zypper --non-interactive install git`
          - Homebrew: `brew install --quiet wget`

        • Configuration tools (NEVER interactive!)
          - Timezone    : `DEBIAN_FRONTEND=noninteractive dpkg-reconfigure tzdata`
          - Locale      : `DEBIAN_FRONTEND=noninteractive dpkg-reconfigure locales`
          - Time sync   : `timedatectl set-timezone America/New_York`
          - NEVER use   : `dpkg-reconfigure tzdata` (prompts for input)

        • System operations
          - User creation : `useradd -m bob && echo 'bob:P@ss' | chpasswd`
          - Service restart: `systemctl restart nginx`
          - File copy     : `cp /src/file /dest/file`

        • File editing (NO interactive editors!)
          - Add line      : `echo "127.0.0.1 example.com" >> /etc/hosts`
          - Replace text  : `sed -i 's/old/new/g' /etc/hosts`
          - Create file   : `cat > /etc/hosts << EOF\ncontent\nEOF`
          - NEVER use     : `nano /etc/hosts`, `vim /etc/hosts` (will hang)

        • Containers & orchestration
          - Docker pull   : `docker pull nginx:latest --quiet`
          - Docker run    : `docker run -d --name web -p 80:80 nginx:latest`
          - Kubernetes    : `kubectl get pods -o json --request-timeout=10s`

        • Databases (NEVER prompt for passwords!)
          - MySQL with pass: `mysql -u root -pPASSWORD -e "CREATE DATABASE test;"`
          - MySQL env var : `MYSQL_PWD=password mysql -u root -e "CREATE DATABASE test;"`
          - MySQL import  : `mysql --batch --silent -u root -pPASS < dump.sql`
          - PostgreSQL    : `PGPASSWORD=pwd psql -U postgres -d db -c "SELECT 1;"`
          - NEVER use     : `mysql -u root` (prompts for password)

        • Git operations (NEVER prompt for credentials!)
          - Public repo   : `git clone https://github.com/user/public-repo.git`
          - Private token : `git clone https://token:x-oauth-basic@github.com/user/repo.git`
          - SSH keys      : `git clone git@github.com:user/repo.git`
          - Credential env: `GIT_ASKPASS=echo git clone https://github.com/user/repo.git`
          - NEVER use     : `git clone https://github.com/user/repo.git` (WILL HANG - prompts for password)
          
        **CRITICAL**: Private repositories ALWAYS require authentication. The command 
        `git clone https://github.com/user/repo.git` will FREEZE the system waiting 
        for username/password input. You MUST use tokens, SSH keys, or refuse the task.

        • File transfer (NO interactive sessions!)
          - Upload file   : `scp localfile user@host:/path/`
          - Download file : `scp user@host:/path/file .`
          - Sync folders  : `rsync -av source/ user@host:/dest/`
          - HTTP download : `wget https://example.com/file.zip`
          - NEVER use     : `ftp server`, `sftp server` (interactive sessions hang)

        • SSL/TLS certificates (NO password prompts!)
          - OpenSSL cert  : `openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=example.com"`
          - Let's Encrypt : `certbot --nginx --non-interactive --agree-tos --email admin@example.com -d example.com`
          - Self-signed   : `openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt -subj "/C=US/ST=State/L=City/O=Org/CN=example.com"`
          - NEVER use     : `openssl req` (without -nodes/-passout, prompts for passphrase)

        === BACKGROUND PROCESS EXAMPLES ===
        ```bash
        # Start log monitoring
        nohup tail -f /var/log/syslog > /tmp/syslog_monitor.log 2>&1 & echo $! > /tmp/syslog_pid.txt

        # Check output periodically
        tail -n 20 /tmp/syslog_monitor.log

        # Stop monitoring
        kill $(cat /tmp/syslog_pid.txt)
        ```

        === RETURN FORMAT ===
        <result>
          <vm_ip_address>...</vm_ip_address>
          <command>...</command>
          <output>...</output>
        </result>

        Parameters:
        - vm_ip_address: target VM address.
        - command      : shell command to execute.
        """,
    )
    def execute_command(vm_ip_address: str, command: str) -> str:
        """Execute a shell command inside an OpenNebula virtual machine.

        Args:
            vm_ip_address: target VM address.
            command: shell command to execute.

        Returns:
            str: XML string with command execution result or error message.
        """
        # --- Permission guard -------------------------------------------------------------
        if not allow_write:
            logger.warning(
                "execute_command called while allow_write=False – refusing to execute command"
            )
            return (
                "<error><message>Write operations are disabled on this MCP instance."
                "</message></error>"
            )

        # Sanitize command for logging (truncate if very long, avoid logging sensitive commands)
        cmd_preview = command[:100] + "..." if len(command) > 100 else command
        logger.debug(f"Executing command on VM {vm_ip_address}: '{cmd_preview}'")

        # Check if the IP address is valid
        if not is_valid_ip_address(vm_ip_address):
            logger.error(f"Invalid IP address provided: {vm_ip_address}")
            return "<error><message>Invalid IP address</message></error>"

        # Construct a direct SSH command, bypassing the 'onevm ssh' wrapper to avoid authentication issues
        ssh_command_parts = ["ssh", f"root@{vm_ip_address}", command]
        logger.debug(f"SSH command constructed for VM {vm_ip_address}")

        try:
            output = execute_one_command(ssh_command_parts)
            logger.debug(f"Command execution completed on VM {vm_ip_address}")
        except Exception as e:
            logger.error(f"SSH command execution failed on VM {vm_ip_address}: {e}")
            output = f"<error><message>Command execution failed via direct SSH: {e}</message></error>"

        result_root = ET.Element("result")
        ET.SubElement(result_root, "vm_ip_address").text = vm_ip_address
        ET.SubElement(result_root, "command").text = command
        ET.SubElement(result_root, "output").text = output
        return ET.tostring(result_root, encoding="unicode")

    @mcp.tool(
        name="list_vms",
        description=f"""Retrieve a list of all virtual machines, with optional filters. 
        It is possible to pass the state, host_id, and cluster_id as a string, but they must represent non-negative integers otherwise you cannot use the tool.
        The host_id is used to filter on the HID field of the HISTORY_RECORDS element.
        The cluster_id is used to filter on the CID field of the HISTORY_RECORDS element.
        The state is used to filter on the STATE field of the VM element.
        {VM_STATES_DESCRIPTION}
        {VM_TEMPLATE_DESCRIPTION}
        {HOST_STATES_DESCRIPTION}
        """,
    )
    def list_vms(
        state: Optional[str] = None,
        host_id: Optional[str] = None,
        cluster_id: Optional[str] = None,
    ) -> str:
        """List VMs with optional filters for state, host, and cluster.

        Args:
            state (Optional[str]): Filter by VM state ID.
            host_id (Optional[str]): Filter by host ID where the VM is running.
            cluster_id (Optional[str]): Filter by cluster ID where the VM is running.

        Returns:
            str: XML string conforming to VM Pool XSD Schema.
        """
        # Log the tool invocation with filters
        filters_desc = []
        if state:
            filters_desc.append(f"state={state}")
        if host_id:
            filters_desc.append(f"host_id={host_id}")
        if cluster_id:
            filters_desc.append(f"cluster_id={cluster_id}")
        filters_str = ", ".join(filters_desc) if filters_desc else "no filters"
        logger.debug(f"Listing VMs with filters: {filters_str}")

        try:
            result = execute_one_command(["onevm", "list", "--xml"])
            logger.debug(f"Retrieved VM list from OpenNebula")
        except Exception as e:
            logger.error(f"Failed to retrieve VM list: {e}")
            raise

        if all(f is None for f in [state, host_id, cluster_id]):
            logger.debug("No filters applied, returning all VMs")
            return result
        else:
            # Validate that non-None filter values are integers
            filter_values = [f for f in [state, host_id, cluster_id] if f is not None]
            if any(not f.isdigit() for f in filter_values):
                logger.error(
                    f"Invalid filter values provided: {filter_values} (must be integers)"
                )
                return "<error><message>Invalid filter values. All filter values must represent integers.</message></error>"

        try:
            root = ET.fromstring(result)
            total_vms = len(root.findall("VM"))
            logger.debug(f"Parsing XML and applying filters to {total_vms} VMs")
        except ET.ParseError as e:
            logger.error(f"Failed to parse VM list XML: {e}")
            raise

        filtered_vms = []

        for vm in root.findall("VM"):
            # State filter
            if state is not None:
                vm_state = vm.find("STATE")
                if vm_state is None or vm_state.text != state:
                    continue

            # History-based filters (host and cluster)
            history = vm.find("HISTORY_RECORDS/HISTORY[last()]")
            if history is not None:
                # Host filter
                if host_id is not None:
                    vm_host_id = history.find("HID")
                    if vm_host_id is None or vm_host_id.text != host_id:
                        continue
                # Cluster filter
                if cluster_id is not None:
                    vm_cluster_id = history.find("CID")
                    if vm_cluster_id is None or vm_cluster_id.text != cluster_id:
                        continue
            elif host_id is not None or cluster_id is not None:
                # If history is required for filtering but not present, skip VM
                continue

            filtered_vms.append(vm)

        logger.debug(
            f"Filtering completed: {len(filtered_vms)}/{total_vms} VMs match criteria"
        )

        # Create new XML with filtered VMs
        new_root = ET.Element("VM_POOL")
        for vm in filtered_vms:
            new_root.append(vm)

        return ET.tostring(new_root, encoding="unicode")

    @mcp.tool(
        name="instantiate_vm",
        description="""Create a new OpenNebula virtual machine from an existing template with specified resources.
            The function performs minimal validation of the provided parameters, constructs the
            appropriate *onetemplate instantiate* CLI call and, upon success, retrieves the full
            VM details in XML format so that callers always receive a valid VM XSD document.

            Args:
                template_id: String ID of the template to instantiate but it must be a non-negative integer otherwise you cannot use the tool
                vm_name: Optional - name for the new VM
                cpu: Optional - CPU percentage reserved for the VM (1=100% one CPU)
                memory: Optional - Memory amount given to the VM. By default the unit is megabytes.
                network_name: Optional - network name to attach
                num_instances: Optional - number of VMs to instantiate

            Returns:
                str: XML string with VM details or error message. If multiple VMs are created,
                     the XML will contain a <VMS> root element with a <VM> for each.
        """,
    )
    def instantiate_vm(
        template_id: str,
        vm_name: Optional[str] = None,
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        network_name: Optional[str] = None,
        num_instances: Optional[str] = None,
    ) -> str:
        """Instantiate a new VM from an existing template.

        The function performs minimal validation of the provided parameters, constructs the
        appropriate *onetemplate instantiate* CLI call and, upon success, retrieves the full
        VM details in XML format so that callers always receive a valid VM XSD document.

        Args:
            template_id: String ID of the template to instantiate
            vm_name: Optional - name for the new VM
            cpu: Optional - CPU percentage reserved for the VM (1=100% one CPU)
            memory: Optional - Memory amount given to the VM. By default the unit is megabytes.
            network_name: Optional - network name to attach
            num_instances: Optional - number of VMs to instantiate

        Returns:
            str: XML string with VM details or error message. If multiple VMs are created,
                 the XML will contain a <VMS> root element with a <VM> for each.
        """
        # --- Permission guard -------------------------------------------------------------
        if not allow_write:
            logger.warning(
                "instantiate_vm called while allow_write=False – refusing to create VM"
            )
            return (
                "<error><message>Write operations are disabled on this MCP instance."  # noqa: E501
                "</message></error>"
            )

        # Validate all numeric parameters that are provided
        numeric_params = {
            "template_id": template_id,
            "cpu": cpu,
            "memory": memory,
            "num_instances": num_instances,
        }

        for param_name, value in numeric_params.items():
            if value is not None:
                if (
                    not isinstance(value, str)
                    or not value.isdigit()
                    or (int(value) < 0 and param_name == "template_id")
                    or (int(value) <= 0 and param_name != "template_id")
                ):
                    logger.error(f"Invalid {param_name} provided: {value}")
                    return f"<error><message>{param_name} must be a a non-negative integer for the template_id, and a positive integer for the other parameters</message></error>"

        cmd_parts = ["onetemplate", "instantiate", template_id]

        # Optional flags
        if vm_name:
            cmd_parts.extend(["--name", vm_name])

        if num_instances:
            cmd_parts.extend(["--multiple", num_instances])

        if cpu is not None:
            cmd_parts.extend(["--cpu", cpu])

        if memory is not None:
            cmd_parts.extend(["--memory", memory])

        if network_name is not None:
            cmd_parts.extend(["--nic", network_name])

        logger.debug(
            "Instantiating VM from template with command: %s",
            " ".join(cmd_parts),
        )

        instantiate_output = execute_one_command(cmd_parts)

        # Parse the textual output to extract the new VM IDs
        vm_ids: list[str] = []
        for line in instantiate_output.splitlines():
            line = line.strip()
            if line.lower().startswith("vm id"):
                vm_id = line.split(":")[-1].strip()
                if vm_id.isdigit():
                    vm_ids.append(vm_id)

        if not vm_ids:
            logger.error(
                "Failed to parse VM ID from instantiate output: %s", instantiate_output
            )
            return (
                "<error><message>Unable to determine new VM ID – raw output: "
                f"{instantiate_output}</message></error>"
            )

        logger.debug(f"Fetching XML details for newly created VMs {vm_ids}")
        if len(vm_ids) == 1:
            return execute_one_command(["onevm", "show", vm_ids[0], "--xml"])
        else:
            root = ET.Element("VMS")
            for vm_id in vm_ids:
                vm_xml_str = execute_one_command(["onevm", "show", vm_id, "--xml"])
                try:
                    vm_element = ET.fromstring(vm_xml_str)
                    root.append(vm_element)
                except ET.ParseError as e:
                    logger.error(f"Failed to parse XML for VM {vm_id}: {e}")
                    logger.error(f"XML content: {vm_xml_str}")
            return ET.tostring(root, encoding="unicode")

    @mcp.tool(
        name="manage_vm",
        description=f"""Manages the lifecycle state of an OpenNebula virtual machine. Use this tool to perform power operations (start, stop, reboot) or to permanently delete a VM.
        
        IMPORTANT: If you need to perform the same lifecycle action on *several* VMs, you **MUST** batch them into a *single* call using either a comma-separated list (e.g., "1,2,3") or an OpenNebula numeric range (e.g., "5..10").
        Never loop over individual IDs or emit multiple `manage_vm` calls – it wastes API calls and increases race-condition risk. The OpenNebula CLI natively supports lists/ranges and will process each VM atomically, skipping invalid ones without blocking the rest.

        Before calling this tool, ALWAYS perform these checks in the same turn:
        - vm_id validation
            - For all supported operations you MAY pass a single ID *or* a list/range. Batch mode (list/range) is strongly preferred whenever more than one VM is targeted.
            - If the user supplies anything else (letters, symbols, negative numbers), DO NOT call manage_vm.
            - Instead, respond with a short apology and explain the input must be a non-negative integer.
        - operation validation
            - Allowed operations: start, stop, reboot, terminate.
            - If the user asks for any other action (lock, hibernate, etc.), DO NOT call manage_vm.
            - Explain that the requested action is unsupported and list the valid operations.
        {VM_STATES_DESCRIPTION}

        Args:
            vm_id: The target VM identifier(s). This must be a single string in one of the following formats:
                • A single numeric ID (e.g., "42").
                • A comma-separated list (e.g., "1,2,3").
                • A numeric range (e.g., "5..10").

                **CRITICAL ID NORMALIZATION**: If a user's request contains a mix of formats (e.g. "stop VMs 1,2 and 5 to 7"), you MUST normalize it into a single valid format before calling the tool. For example:
                - "VMs 1,2 and 5 to 7" becomes a comma-separated list: "1,2,5,6,7".
                - "VMs 1 through 5" becomes a range: "1..5".
                Mixed formats like "1..2,3" or space-separated lists like "1 2 3" are INVALID and MUST be normalized or rejected.

                When multiple IDs are provided, you MUST invoke this tool **once** with the normalized list/range. Per-VM state validation is skipped client-side; the OpenNebula backend enforces it and will reject only the non-eligible VMs while processing the rest.

            operation: Lifecycle action to perform. Supported values are:
                - "start"  → maps to `onevm resume`
                - "stop"   → maps to `onevm poweroff`
                - "reboot" → maps to `onevm reboot`
                - "terminate" → maps to `onevm terminate`

            hard: When `True`, adds `--hard` to poweroff, reboot and terminate commands. Ignored for resume.

        Available operations:
        - start: Start a VM (from STOPPED, POWEROFF, SUSPENDED, UNDEPLOYED states)
        - stop: Poweroff a VM (from RUNNING state)
        - reboot: Reboot a VM (from RUNNING state)
        - terminate: Permanently delete a VM (from any state except DONE)

        The hard parameter applies to certain operations:
        - stop: if True, performs immediate shutdown instead of graceful
        - terminate: if True, forces deletion even if VM is in problematic state

        The tool validates current VM state and only allows valid state transitions according to OpenNebulas VM lifecycle.
        """,
    )
    def manage_vm(vm_id: str, operation: str, hard: Optional[bool] = False) -> str:
        """Manage VM lifecycle operations with state validation.

        Args:
            vm_id: The target VM identifier(s). This can be:
                • A single numeric ID (e.g., "42").
                • A comma-separated list (e.g., "1,2,3") **or** a numeric range using the CLI syntax (e.g., "5..10").

            operation: Lifecycle action to perform. Supported values are:
                - "start"  → maps to `onevm resume`
                - "stop"   → maps to `onevm poweroff`
                - "reboot" → maps to `onevm reboot`
                - "terminate" → maps to `onevm terminate`

            hard: When `True`, adds `--hard` to poweroff, reboot and terminate commands. Ignored for resume.

        Returns:
            str: XML string with operation result or error message
        """

        if not allow_write:
            logger.warning(
                f"manage_vm called while allow_write=False - refusing operation {operation} on VM {vm_id}"
            )
            return "<error><message>Write operations are disabled on this MCP instance.</message></error>"

        valid_operations = ["start", "stop", "reboot", "terminate"]
        operation = operation.strip().lower()
        if operation not in valid_operations:
            logger.error(f"Invalid operation: {operation}")
            return f"<error><message>Invalid operation '{operation}'. Valid operations: {', '.join(valid_operations)}</message></error>"

        # Multi-VM handling (comma list or range)
        is_multi_vm = _is_multi_vm(vm_id)
        if is_multi_vm:
            cmd_parts = _build_cmd_parts(operation, vm_id, hard)

            logger.debug(f"Executing multi-VM {operation} command: {' '.join(cmd_parts)}")
            try:
                result = execute_one_command(cmd_parts)

                return _wrap_success_xml(vm_id, operation, hard, result, True)

            except Exception as e:
                logger.error(f"Failed to execute multi-VM {operation} for {vm_id}: {e}")
                return f"<error><message>Failed to execute multi-VM {operation}: {e}</message></error>"

        # Single VM operation logic
        if not vm_id.isdigit() or int(vm_id) < 0:
            logger.error(f"Invalid VM ID provided: {vm_id}")
            return (
                "<error><message>vm_id must be a non-negative integer</message></error>"
            )

        # Get current VM status
        logger.debug(f"Getting current status for VM {vm_id} before {operation}")
        try:
            vm_status_xml = execute_one_command(["onevm", "show", vm_id, "--xml"])
        except Exception as e:
            logger.error(f"Failed to get VM status for {vm_id}: {e}")
            return f"<error><message>Failed to get VM status: {e}</message></error>"

        # Parse VM state
        try:
            root = ET.fromstring(vm_status_xml)
            state = root.find("STATE")
            lcm_state = root.find("LCM_STATE")

            if state is None:
                return "<error><message>Could not determine VM state</message></error>"

            current_state = int(state.text)
            current_lcm = int(lcm_state.text) if lcm_state is not None else None

            logger.debug(
                f"VM {vm_id} current state: STATE={current_state}, LCM_STATE={current_lcm}"
            )

        except (ET.ParseError, ValueError) as e:
            logger.error(f"Failed to parse VM status XML: {e}")
            return f"<error><message>Failed to parse VM status: {e}</message></error>"

        # State validation and operation mapping
        validation = STATE_VALIDATIONS.get(operation)
        if not validation:
            return f"<error><message>Unknown operation: {operation}</message></error>"

        # Check if current state allows the operation
        if current_state not in validation["valid_states"]:
            logger.warning(
                f"VM {vm_id} operation {operation} not allowed in state {current_state}"
            )
            return f"<error><message>{validation['error_msg']} (current state: {current_state})</message></error>"

        # Additional LCM state validation is only applied when the VM is in an ACTIVE state
        if "valid_lcm_states" in validation and current_state == 3:
            if current_lcm not in validation["valid_lcm_states"]:
                logger.warning(
                    f"VM {vm_id} operation {operation} not allowed in LCM state {current_lcm}"
                )
                return f"<error><message>{validation['error_msg']} (current LCM state: {current_lcm})</message></error>"

        # Build CLI command for single-VM actions
        cmd_parts = _build_cmd_parts(operation, vm_id, hard)

        logger.debug(f"Executing VM {operation} command: {' '.join(cmd_parts)}")

        # Execute operation
        try:
            result = execute_one_command(cmd_parts)
            logger.info(f"VM {vm_id} {operation} operation completed")

            # Return success message in XML format
            return _wrap_success_xml(vm_id, operation, hard, result, False)

        except Exception as e:
            logger.error(f"Failed to execute {operation} on VM {vm_id}: {e}")
            return (
                f"<error><message>Failed to execute {operation}: {e}</message></error>"
            )
