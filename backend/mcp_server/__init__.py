"""AI Lab Portal MCP server.

Exposes internal application tools via the Model Context Protocol so that
Agents SDK agents can query project context, check idea status, and search
content during generation.

The server runs as a stdio subprocess launched by ``MCPServerStdio`` from
the Agents SDK. It shares code with the main application but runs in its
own process.
"""
