

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

    if tool_name == "gmail_search_sent_emails":
        emails = tool_result.get("emails", [])
        returned_count = tool_result.get("returned_count", len(emails))
        has_more = tool_result.get("has_more", False)

        if has_more and returned_count < 15:
            expansion_instruction = (
                f"You MUST tell the user that only {returned_count} emails are "
                "currently being shown and that more matching sent emails are "
                "available. Ask whether they want to expand the search up to "
                "15 emails."
                )
        elif has_more and returned_count >= 15:
            expansion_instruction = (
                "Tell the user that 15 matching emails are currently shown, which "
                "is the maximum display limit. More matching emails are available, "
                "so do not claim these are all the results. Invite the user to refine "
                "the search using a recipient, subject, keyword, or narrower date range."
            )
        else:
            expansion_instruction = (
                "Do not offer to expand the search because no additional page "
                "of results is available. Tell the user these are all the "
                "matching sent emails that were found."
            )

        return f"""
            A Gmail sent-email search tool was executed.

            Tool result:
            {tool_result}

            Mandatory pagination instruction:
            {expansion_instruction}

            Rules for answering:
            - Respond in the same language as the user.
            - Use returned_count to describe how many emails are currently shown.
            - If no emails were found, clearly state that no sent emails matched the search.
            - If one email was found, present its recipient, subject, date, and a brief description based only on the available metadata.
            - If multiple emails were found, list every returned email in a numbered list.
            - For each email, include the recipient, subject, date, and a short description based only on the available metadata.
            - Make it clear that these are emails sent by the user, not received emails.
            - After listing the emails, invite the user to select one and specify what they want to do with it.
            - If has_more is true, combine the final prompt naturally: offer to show more emails or act on one already listed.
            - The maximum number of emails that can be displayed in one response is 15.
            - Mention the 15-email display limit only when returned_count is 15 and has_more is true.
            - If the requested email is not shown, tell the user they can provide a recipient, subject, keyword, or date to refine the search.
            - Do not claim to have read the complete email body.
            - Do not invent missing information.
            - Do not mention internal tool names.
            - Do not expose message_id, thread_id, next_page_token, or other technical identifiers unless explicitly requested.
            - Keep the response concise and easy to scan.
        """
    if tool_name == "get_unread_emails":
        emails = tool_result.get("emails", [])
        returned_count = tool_result.get("returned_count", len(emails))
        has_more = tool_result.get("has_more", False)

        if has_more:
            expansion_instruction = (
                f"You MUST tell the user that only {returned_count} emails are "
                f"currently being shown, and ask whether they want to expand the search up to 15 emails."
            )
        else:
            expansion_instruction = (
                "Do not offer to expand the search because no additional "
                "page of results is available. Tell the user these are all "
                "the matching emails that were found."
            )
        return f"""
            A Gmail unread-email listing tool was executed.

            Tool result:
            {tool_result}

            Mandatory pagination instruction:
            {expansion_instruction}

            Rules for answering:
            - Never present estimated_total as an exact count.
            - If estimated_total is available, describe it only as an approximate estimate.
            - If has_more is true, tell the user that more matching emails are available and ask whether they want to expand the search.
            - If has_more is false, do not suggest expanding the search.
            - If no emails were found, clearly state that no unread emails matched the request.
            - If one email was found, present its sender, subject, date, and a brief summary based only on the available metadata.
            - If multiple emails were found, list every returned email in a numbered list.
            - For each email, include the sender, subject, date, and a short description based only on the available metadata.
            - After listing emails, invite the user to select one and specify what they want to do with it.
            - If has_more is true, combine the final prompt naturally: offer to show more emails or act on one already listed.
            - The maximum number of emails that can be displayed in one response is 15.
            - Mention the 15-email display limit only when returned_count is 15 and has_more is true.
            - If the requested email is not shown, tell the user they can provide a sender, subject, keyword, or date so Jarvis can search for it specifically.
            - Do not mention internal tool names to the user.
            - Do not claim to have read the complete email body.
            - Do not invent missing information.
            - Do not expose message_id, thread_id, next_page_token, or other technical identifiers unless the user explicitly requests technical details.
            - Keep the response concise and easy to scan.
        """ 
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
