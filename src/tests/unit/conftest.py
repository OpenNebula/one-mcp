# ----------------------------------------------------------------------------
# Helper: dummy MCP object to capture registered tool functions
# ----------------------------------------------------------------------------


class DummyMCP:
    """
    Minimal FastMCP stub for unit-testing tool registration.
    Return a *decorator* because Python expects it.

        Decorator chain behind the syntax:
            @mcp.tool(...)
            def func(): ...

        is equivalent to:
            def func(): ...
            func = mcp.tool(...)(func)

        Therefore ``dummy.tool`` must *return* another function that
        receives the new tool function, stores it, and then hands it
        back unchanged.
    """
    def __init__(self):
        self.tools = {}

    def tool(self, *, name: str, description: str):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator