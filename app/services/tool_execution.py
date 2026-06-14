

from app.tools.registry import TOOLS


def tool_execution_system(tool_name: str, arguments: dict):

    if tool_name not in TOOLS:
        raise ValueError("Unknown tool")
    
    tool_function = TOOLS[tool_name]

    #esto devuelve la funcion EJECUTADA
    return tool_function(arguments)


def build_tool_context(tool_name: str, tool_result: dict) -> str:

    return f"""
        A backend tool was executed.

        Tool name:
        {tool_name}

        Tool result:
        {tool_result}

        Use this result to answer the user naturally.
    """