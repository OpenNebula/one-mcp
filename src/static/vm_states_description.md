# OpenNebula VM States Reference

**Note:** For any prompts or queries about "active" or "running" VMs, you should always check for VMs where `STATE=3` (ACTIVE). Only these VMs are considered currently running in OpenNebula. The LCM_STATE provides further detail, but STATE=3 is the primary indicator for running VMs.

In OpenNebula a Virtual Machine has 2 variables to define its state: STATE and LCM_STATE. The LCM_STATE is only relevant when the STATE is ACTIVE. Both states can be seen from the CLI (onevm show).

## Main States (STATE)

- **0 - INIT**: Internal initialization state right after VM creation, not visible to end users
- **1 - PENDING**: VM waiting for resources to run on, stays until scheduler deploys it
- **2 - HOLD**: VM held by owner, won't be scheduled until released but can be deployed manually
- **3 - ACTIVE**: VM is active and running (see LCM States below for detailed substates)
- **4 - STOPPED**: VM is stopped, state saved and transferred back to system datastore
- **5 - SUSPENDED**: Same as stopped but files left on host for later resume
- **6 - DONE**: VM completed, kept in database for accounting but not shown in onevm list
- **8 - POWEROFF**: Like suspended but no checkpoint file generated, files left on host
- **9 - UNDEPLOYED**: VM shut down, disks transferred to system datastore, can be resumed
- **10 - CLONING**: VM waiting for disk images to finish initial copy to repository
- **11 - CLONING_FAILURE**: Failure during cloning, one or more images went into ERROR state

## LCM States (when STATE = 3 ACTIVE)

### Initialization & Boot
- **0 - LCM_INIT**: Internal initialization state, not visible to end users
- **1 - PROLOG**: Transferring VM files to target host
- **2 - BOOT**: Waiting for hypervisor to create the VM
- **19 - BOOT_UNKNOWN**: Waiting for hypervisor to create VM from UNKNOWN state
- **20 - BOOT_POWEROFF**: Waiting for hypervisor to create VM from POWEROFF state
- **21 - BOOT_SUSPENDED**: Waiting for hypervisor to create VM from SUSPENDED state
- **22 - BOOT_STOPPED**: Waiting for hypervisor to create VM from STOPPED state
- **32 - BOOT_UNDEPLOY**: Waiting for hypervisor to create VM from UNDEPLOY state
- **35 - BOOT_MIGRATE**: Waiting for hypervisor to create VM from cold migration

### Running State
- **3 - RUNNING**: VM is running and being monitored periodically

### Migration Operations
- **4 - MIGRATE**: VM migrating between hosts (hot migration)
- **7 - SAVE_MIGRATE**: Saving VM files for cold migration
- **8 - PROLOG_MIGRATE**: File transfers during cold migration
- **43 - PROLOG_MIGRATE_POWEROFF**: File transfers during cold migration from POWEROFF
- **45 - PROLOG_MIGRATE_SUSPEND**: File transfers during cold migration from SUSPEND
- **60 - PROLOG_MIGRATE_UNKNOWN**: File transfers during cold migration from UNKNOWN

### Save Operations
- **5 - SAVE_STOP**: Saving VM files after stop operation
- **6 - SAVE_SUSPEND**: Saving VM files after suspend operation

### Resume Operations
- **9 - PROLOG_RESUME**: File transfers after resume from stopped state
- **31 - PROLOG_UNDEPLOY**: File transfers after resume from undeployed state

### Cleanup Operations
- **10 - EPILOG_STOP**: File transfers from host to system datastore
- **11 - EPILOG**: Cleaning up host and copying disk images back to datastores
- **15 - CLEANUP_RESUBMIT**: Cleanup after delete-recreate action
- **23 - CLEANUP_DELETE**: Cleanup after delete action
- **30 - EPILOG_UNDEPLOY**: Cleaning up host and transferring VM files to system datastore

### Shutdown Operations
- **12 - SHUTDOWN**: Sent shutdown ACPI signal, waiting for completion
- **18 - SHUTDOWN_POWEROFF**: Shutdown ACPI signal sent, waiting for poweroff completion
- **29 - SHUTDOWN_UNDEPLOY**: Shutdown ACPI signal sent, waiting for undeploy completion

### Hotplug Operations
- **17 - HOTPLUG**: Disk attach/detach operation in progress
- **25 - HOTPLUG_NIC**: NIC attach/detach operation in progress
- **26 - HOTPLUG_SAVEAS**: Disk-saveas operation in progress
- **27 - HOTPLUG_SAVEAS_POWEROFF**: Disk-saveas operation from POWEROFF in progress
- **28 - HOTPLUG_SAVEAS_SUSPENDED**: Disk-saveas operation from SUSPENDED in progress
- **33 - HOTPLUG_PROLOG_POWEROFF**: File transfers for disk attach from poweroff
- **34 - HOTPLUG_EPILOG_POWEROFF**: File transfers for disk detach from poweroff
- **65 - HOTPLUG_NIC_POWEROFF**: NIC attach/detach operation from POWEROFF in progress
- **66 - HOTPLUG_RESIZE**: Hotplug resize VCPU and memory in progress
- **67 - HOTPLUG_SAVEAS_UNDEPLOYED**: Disk-saveas operation from UNDEPLOYED in progress
- **68 - HOTPLUG_SAVEAS_STOPPED**: Disk-saveas operation from STOPPED in progress

### Snapshot Operations
- **24 - HOTPLUG_SNAPSHOT**: System snapshot action in progress
- **51 - DISK_SNAPSHOT_POWEROFF**: Disk snapshot create from POWEROFF in progress
- **52 - DISK_SNAPSHOT_REVERT_POWEROFF**: Disk snapshot revert from POWEROFF in progress
- **53 - DISK_SNAPSHOT_DELETE_POWEROFF**: Disk snapshot delete from POWEROFF in progress
- **54 - DISK_SNAPSHOT_SUSPENDED**: Disk snapshot create from SUSPENDED in progress
- **55 - DISK_SNAPSHOT_REVERT_SUSPENDED**: Disk snapshot revert from SUSPENDED in progress
- **56 - DISK_SNAPSHOT_DELETE_SUSPENDED**: Disk snapshot delete from SUSPENDED in progress
- **57 - DISK_SNAPSHOT**: Disk snapshot create from RUNNING in progress
- **59 - DISK_SNAPSHOT_DELETE**: Disk snapshot delete from RUNNING in progress

### Disk Operations
- **62 - DISK_RESIZE**: Disk resize with VM in RUNNING state
- **63 - DISK_RESIZE_POWEROFF**: Disk resize with VM in POWEROFF state
- **64 - DISK_RESIZE_UNDEPLOYED**: Disk resize with VM UNDEPLOYED

### Backup Operations
- **69 - BACKUP**: Backup operation in progress (VM running)
- **70 - BACKUP_POWEROFF**: Backup operation in progress (VM poweroff)
- **71 - RESTORE**: VM disks being restored from backup image

### Special States
- **16 - UNKNOWN**: VM couldn't be monitored, in unknown state

### Failure States
- **36 - BOOT_FAILURE**: Failure during BOOT
- **37 - BOOT_MIGRATE_FAILURE**: Failure during BOOT_MIGRATE
- **38 - PROLOG_MIGRATE_FAILURE**: Failure during PROLOG_MIGRATE
- **39 - PROLOG_FAILURE**: Failure during PROLOG
- **40 - EPILOG_FAILURE**: Failure during EPILOG
- **41 - EPILOG_STOP_FAILURE**: Failure during EPILOG_STOP
- **42 - EPILOG_UNDEPLOY_FAILURE**: Failure during EPILOG_UNDEPLOY
- **44 - PROLOG_MIGRATE_POWEROFF_FAILURE**: Failure during PROLOG_MIGRATE_POWEROFF
- **46 - PROLOG_MIGRATE_SUSPEND_FAILURE**: Failure during PROLOG_MIGRATE_SUSPEND
- **47 - BOOT_UNDEPLOY_FAILURE**: Failure during BOOT_UNDEPLOY
- **48 - BOOT_STOPPED_FAILURE**: Failure during BOOT_STOPPED
- **49 - PROLOG_RESUME_FAILURE**: Failure during PROLOG_RESUME
- **50 - PROLOG_UNDEPLOY_FAILURE**: Failure during PROLOG_UNDEPLOY
- **61 - PROLOG_MIGRATE_UNKNOWN_FAILURE**: Failure during PROLOG_MIGRATE_UNKNOWN