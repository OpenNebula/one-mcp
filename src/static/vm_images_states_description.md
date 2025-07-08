# OpenNebula Image States Reference

An OpenNebula Image represents a VM disk. Images can have multiple formats (e.g., filesystem or block device) and can store OS installations, data filesystems, images, or kernels.

## Image State Values

OpenNebula images define their state using the `STATE` variable. The following states are possible:

| State ID | State Name        | Short | Meaning                                              |
|----------|-------------------|-------|------------------------------------------------------|
| 0        | INIT              | init  | Initialization state                                 |
| 1        | READY             | rdy   | Image ready to use                                   |
| 2        | USED              | used  | Image in use by one or more VMs                     |
| 3        | DISABLED          | disa  | Image cannot be instantiated by a VM                |
| 4        | LOCKED            | lock  | Filesystem operation for the Image in process       |
| 5        | ERROR             | err   | Error state - the operation FAILED                  |
| 6        | CLONE             | clon  | Image is being cloned                                |
| 7        | DELETE            | dele  | Datastore is deleting the image                      |
| 8        | USED_PERS         | used  | Image is in use and persistent                       |
| 9        | LOCKED_USED       | lock  | FS operation in progress, VMs waiting               |
| 10       | LOCKED_USED_PERS  | lock  | FS operation in progress, VMs waiting. Persistent   |

## Image Lifecycle States

### Operational States
- **READY (1)**: Image is available and can be used to instantiate new VMs
- **USED (2)**: Image is currently being used by at least one VM (non-persistent)
- **USED_PERS (8)**: Image is being used by VMs and is persistent

### Transitional States
- **INIT (0)**: Image is being initialized after creation
- **LOCKED (4)**: Image is undergoing a filesystem operation (copy, resize, etc.)
- **LOCKED_USED (9)**: Image operation in progress while VMs are waiting
- **LOCKED_USED_PERS (10)**: Same as LOCKED_USED but for persistent images
- **CLONE (6)**: Image is being cloned to create a copy

### Terminal/Error States
- **DISABLED (3)**: Image has been disabled and cannot be used for new VMs
- **ERROR (5)**: An operation on the image failed
- **DELETE (7)**: Image is being removed from the datastore

## Image Types and Usage

### Image Types
- **OS**: Operating system disk images
- **CDROM**: CD-ROM/ISO images
- **DATABLOCK**: Additional data disks
- **KERNEL**: Kernel files for direct kernel boot
- **RAMDISK**: Initial ramdisk files
- **CONTEXT**: Contextualization images

### Persistent vs Non-Persistent
- **Non-persistent**: The modifications will not be preserved after terminating the VM. Non-persistent Images can be used by multiple VMs at the same time as each one will work on its own copy.
- **Persistent**: The modifications you make to persistent images will be preserved after terminating the VM. There can be only one VM using a persistent Image at any given time.

## Common Image Operations

### Safe Operations by State
- **READY**: Can instantiate VMs, clone, disable, delete
- **USED/USED_PERS**: Can view info, cannot delete or modify
- **DISABLED**: Can enable, delete (if not used), cannot instantiate
- **ERROR**: Can retry operation, delete, or troubleshoot
