

from sqlalchemy.orm import Session

from app.tools.external.gmail_tools import gmail_create_reply_draft_tool, gmail_read_latest_email_tool, gmail_read_specific_email_tool, gmail_send_drafted_email_tool, gmail_update_email_draft_tool
from app.tools.registry import TOOLS


def tool_execution_system(tool_name: str, arguments: dict, user_id:int, session: Session, conversation_id: int):

    if tool_name not in TOOLS:
        raise ValueError("Unknown tool")
    
    tool_function = TOOLS[tool_name]
    
    if tool_function == gmail_send_drafted_email_tool:
        return gmail_send_drafted_email_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    if tool_function == gmail_update_email_draft_tool:
        return gmail_update_email_draft_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    if tool_function == gmail_create_reply_draft_tool:
        return gmail_create_reply_draft_tool(arguments=arguments, user_id=user_id, session=session,
        conversation_id=conversation_id)
    if tool_function == gmail_read_specific_email_tool:
        return gmail_read_specific_email_tool(arguments=arguments, user_id=user_id, session=session,
        conversation_id=conversation_id)
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
    
    if tool_name == "gmail_get_drafted_emails":
        return f"""
            A Gmail draft list tool was executed.

            Tool result:
            {tool_result}

            These results are Gmail drafts, not received emails and not sent emails.
            The tool returns only the drafts requested for this query, usually the latest drafts.
            Do not claim this is the user's total number of drafts unless the result explicitly includes a total count.

            Rules for answering:
            - If the result is empty, tell the user no recent drafts were found.
            - If there is one draft, say it is the latest draft returned and summarize it using to, subject, and snippet.
            - If there are multiple drafts, say these are the latest drafts returned and list them clearly.
            - Do not ask the user which draft they mean unless the user asked to send, edit, or choose one.
            - Do not say the drafts were sent.
            - Do not expose draft_id unless the user explicitly asks for technical details.
    """

    if tool_name == "gmail_read_specific_email":
        return f"""
            A Gmail specific-email reading tool was executed.

            Tool result:
            {tool_result}

            Rules:
            - If reason is multiple_matching_emails, tell the user that multiple emails were found.
            - List every item from matching_emails. Do not omit any item.
            - Preserve the exact existing order and position value.
            - Never filter, regroup, reorder, or renumber the results.
            - The displayed number must be exactly the item's position value.
            - For each email show sender, subject, date, and a short snippet.
            - Ask which numbered email they want to read.
            - Do not claim that any email was read yet.
            - Do not expose message IDs.
            - If read is successful, present the email content naturally.
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
