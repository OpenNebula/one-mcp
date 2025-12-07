# OpenNebula MCP Server

An MCP (Model Context Protocol) server that provides AI assistants with tools to manage OpenNebula virtual machines and infrastructure. This server enables AI-powered interactions with OpenNebula clouds for VM lifecycle management, template operations, and infrastructure inspection.

## Prerequisites

**⚠️ Important**: You must have a working OpenNebula deployment before running this MCP server. The server requires access to OpenNebula's API and command-line tools.

### Required Software

- **Python 3.10+**
- **UV** (Python package manager)
- **OpenNebula CLI**
- **MCP Client** (e.g., Cursor, Windsurf, Warp Terminal, mcphost)

# Testing
[Promptfoo](https://promptfoo.dev) is used to test the MCP Server's ability to select and use the correct tools.

**⚠️ Important**: Use promptfoo version 0.117.4 for compatibility with the test suite:

```bash
npx promptfoo@0.117.4 eval -c promptfooconfig.yaml
```

## Documentation
[Documentation for one-mcp is in the project Wiki](../../wiki/)

## Contributing

* Guidelines
* [Development and issue tracking](https://github.com/OpenNebula/one-mcp/issues).
* [Community Forum](https://forum.opennebula.io/c/development/one-mcp/).

## Contact Information

* [OpenNebula web site](https://opennebula.io).
* [Enterprise Services](https://opennebula.io/enterprise).
  
## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Author Information

Copyright 2002-2025, OpenNebula Project, OpenNebula Systems

## Acknowledgements

Some of the software features included in this repository have been made possible through the funding of the following innovation projects: [ONEnextgen](http://onenextgen.eu/).
