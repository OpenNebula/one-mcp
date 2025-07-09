OpenNebula's Hosts define their state using the STATE variable.
This state can be viewed from the CLI using `onehost show` command.

States and Their Meanings
State 0 - INIT (init):
Initial state for enabled hosts.

State 1 - MONITORING_MONITORED (update):
The host is currently being monitored.

State 2 - MONITORED (on):
The host has been successfully monitored.

State 3 - ERROR (err):
An error occurred during host monitoring.

State 4 - DISABLED (dsbl):
The host has been disabled.

State 5 - MONITORING_ERROR (retry):
Monitoring the host again after an error.

State 6 - MONITORING_INIT (init):
Monitoring the host from the initial state.

State 7 - MONITORING_DISABLED (dsbl):
Monitoring the host after it was disabled.

State 8 - OFFLINE (off):
The host has been set to offline.