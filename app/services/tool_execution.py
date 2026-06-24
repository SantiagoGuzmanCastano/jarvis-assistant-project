

from sqlalchemy.orm import Session

from app.tools.registry import TOOLS


def tool_execution_system(tool_name: str, arguments: dict, user_id:int, session: Session):

    if tool_name not in TOOLS:
        raise ValueError("Unknown tool")
    
    tool_function = TOOLS[tool_name]

    #esto devuelve la funcion EJECUTADA
    return tool_function(arguments=arguments, user_id=user_id, session=session)


def build_tool_context(tool_name: str, tool_result: dict) -> str:

    if tool_name == "gmail_search_drafted_emails":
        return f"""
            A Gmail draft search tool was executed.

            Tool result:
            {tool_result}

            These results are Gmail drafts, not received emails and not sent emails.

            Rules for answering:
            - If the result is empty, tell the user no matching draft was found.
            - If there is one draft, summarize the draft using to, subject, and snippet.
            - If there are multiple drafts, show the main differences and ask the user which draft they mean.
            - Do not say the draft was sent.
            - Do not expose draft_id unless the user explicitly asks for technical details.
        """

    return f"""
        A backend tool was executed.

        Tool name:
        {tool_name}

        Tool result:
        {tool_result}

        Use this result to answer the user naturally.
        Do not claim success unless the tool result clearly indicates success.
        If the tool result indicates an error, no match, missing permission, or multiple possible matches, explain that the action was not completed.
        Never infer success from the fact that a tool was executed.
        Only say the action succeeded if the tool result explicitly confirms it.
    """