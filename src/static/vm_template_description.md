# OpenNebula VM Template Schema

This document describes the key XML tags for a Virtual Machine (VM) object in OpenNebula. This helps in understanding a VM's status and configuration from its XML representation.

## Main VM Tags

- `<VM>`: The root element for a single virtual machine.
- `<ID>`: A unique integer identifying the VM.
- `<NAME>`: The name given to the VM by a user.
- `<STATE>`: The main state of the VM (e.g., 3 = ACTIVE).
- `<LCM_STATE>`: The detailed "Lifecycle Manager" state. It provides more detail when the main `STATE` is ACTIVE (e.g., 3 = RUNNING).

## History Records

The `<HISTORY_RECORDS>` section contains the lifecycle history of the VM. It shows where and when the VM has run.

- `<HISTORY>`: A single entry in the VM's history. A new entry is created each time the VM is deployed on a host.
- `<HID>`: **Host ID**. The unique integer ID of the physical host machine where the VM is (or was) running for this history entry. This tag is commonly used to filter VMs by host.
- `<CID>`: **Cluster ID**. The unique integer ID of the cluster to which the host belongs. This tag is commonly used to filter VMs by cluster.

---

### **Critical Instructions for Data Filtering and Counting**

When a user asks a question that involves filtering or counting (e.g., "how many VMs...", "list VMs on host..."), you **MUST** follow these steps:

1.  **Identify the Filter Criteria**: Read the user's request to understand what they want to filter by (e.g., host, cluster, state).
2.  **Scan the XML for Tags**: Carefully examine the provided XML data. Use the tag descriptions above to find the correct tag for the filter (e.g., use `<HID>` for host, `<CID>` for cluster, `<STATE>` for state).
3.  **Apply the Filter**: Go through each `<VM>` entry one by one and check if it contains the tag and value that match the user's criteria.
4.  **Perform the Action**: Only after you have a list of matching VMs, perform the requested action (e.g., count the matching VMs, list their names).

**Example**: If the user asks, "How many VMs on host 0?", you must first scan all `<VM>` elements, find the ones that contain `<HID>0</HID>`, and only then count how many you found. Do not just count all VMs.
