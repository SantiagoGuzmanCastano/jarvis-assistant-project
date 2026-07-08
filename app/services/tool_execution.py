

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

    emails = tool_result.get("emails", [])
    returned_count = tool_result.get("returned_count", len(emails))
    has_more = tool_result.get("has_more", False)

    if has_more and returned_count < 15:
        expansion_instruction = (
                f"You MUST tell the user that only {returned_count} emails are "
                "currently being shown and that more matching emails are "
                "available. Ask whether they want to expand the search up to "
                "15 emails."
                )
    elif has_more and returned_count >= 15:
        expansion_instruction = (
                "Tell the user that 15 matching emails are currently shown, which "
                "is the maximum display limit. More matching emails are available, "
                "so do not claim these are all the results. Invite the user to refine "
                "the search using a sender or recipient, subject, keyword, or narrower date range."
            )
    else:
            expansion_instruction = (
                "Do not offer to expand the search because no additional page "
                "of results is available. Tell the user these are all the "
                "matching emails that were found."
            )

    if tool_name == "get_latest_emails":
        return f"""
        A Gmail recent-email listing tool was executed.

        Tool result:
        {tool_result}

        Mandatory pagination instruction:
        {expansion_instruction}

        Rules for answering:
        - Treat tool_result as the only source of truth.
        - Respond in the same language as the user.
        - These are recent received emails and may include both read and unread emails.
        - Use returned_count to describe how many emails are currently shown.
        - Do not describe returned_count as the user's total number of emails.
        - If no emails were returned, clearly state that no recent emails were found.
        - If one email was returned, present its sender, subject, date, and a brief description based only on the available metadata.
        - If multiple emails were returned, list every returned email in a numbered list.
        - Preserve the exact order in which the emails appear in tool_result.
        - For each email, include sender, subject, date, and a short description based only on the available metadata.
        - If has_more is true, do not claim that the displayed emails are all the user's emails.
        - If has_more is false, do not suggest expanding the list.
        - Follow the mandatory pagination instruction exactly.
        - After listing the emails, invite the user to select one or search by sender, subject, keyword, or date.
        - Do not claim to have read the complete email body.
        - Do not invent senders, subjects, dates, snippets, counts, or email content.
        - Do not mention internal tool names.
        - Do not expose message_id, thread_id, next_page_token, or other technical identifiers unless explicitly requested.
        - Keep the response concise and easy to scan.
        """

    if tool_name == "gmail_get_sent_emails":
        return f"""
        A Gmail recent-sent-email listing tool was executed.

        Tool result:
        {tool_result}

        Mandatory pagination instruction:
        {expansion_instruction}

        Rules for answering:
        - Treat tool_result as the only source of truth.
        - Respond in the same language as the user.
        - These are emails sent by the user, not received emails.
        - Use returned_count to describe how many emails are currently shown.
        - Do not describe returned_count as the user's total number of sent emails.
        - If no emails were returned, clearly state that no sent emails were found.
        - If one email was returned, present its recipient, subject, date, and a brief description based only on the available metadata.
        - If multiple emails were returned, list every returned email in a numbered list.
        - Preserve the exact order in which the emails appear in tool_result.
        - For each email, include recipient, subject, date, and a short description based only on the available metadata.
        - If has_more is true, do not claim that the displayed emails are all the user's sent emails.
        - If has_more is false, do not suggest expanding the list.
        - After listing the emails, invite the user to select one or refine the search by recipient, subject, keyword, or date.
        - Do not claim to have read the complete email body.
        - Do not invent recipients, subjects, dates, snippets, counts, or email content.
        - Do not mention internal tool names.
        - Do not expose message_id, thread_id, next_page_token, or other technical identifiers unless explicitly requested.
        - Keep the response concise and easy to scan.
    """
    if tool_name == "gmail_search_email_message":
        return f"""
        A Gmail received-email search tool was executed.

        Tool result:
        {tool_result}

        Mandatory pagination instruction:
        {expansion_instruction}

        Rules for answering:
        - Respond in the same language as the user.
        - Treat tool_result as the only source of truth.
        - Never invent senders, subjects, dates, snippets, counts, or emails.
        - Use returned_count to describe how many emails are currently shown.
        - If no emails were found, clearly state that no received emails matched the search.
        - If one email was found, present its sender, subject, date, and a brief description based only on the available metadata.
        - If multiple emails were found, list every returned email in a numbered list.
        - For each email, include its sender, subject, date, and a short description supported only by its metadata.
        - Make it clear that these are received emails, not sent emails or drafts.
        - Never claim that all matching emails were found when has_more is true.
        - Follow the mandatory pagination instruction exactly.
        - After listing the emails, invite the user to select one and specify what they want to do with it.
        - If has_more is true and returned_count is below 15, naturally offer to show more emails or act on one already listed.
        - The maximum number of emails displayed in one response is 15.
        - If the requested email is not shown, tell the user they can provide a sender, subject, keyword, or date to refine the search.
        - Do not claim to have read the complete email body.
        - Do not mention internal tool names, scores, or ranking logic.
        - Do not expose message_id, thread_id, next_page_token, or other technical identifiers unless explicitly requested.
        - Keep the response concise and easy to scan.
    """
    if tool_name == "gmail_search_sent_emails":

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

        return f"""
            A Gmail unread-email listing tool was executed.

            Tool result:
            {tool_result}

            Mandatory pagination instruction:
            {expansion_instruction}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Never invent senders, subjects, dates, snippets, email counts, or example emails.
            - Never describe an email that is not present in tool_result.
            - The returned emails represent the current result batch.
            - If the user asks for emails other than a previously mentioned sender or topic, exclude matching emails from the answer.
            - In that case, present only returned emails that do not match the excluded sender or topic.
            - If every returned email matches the excluded sender or topic, do not list invented alternatives.
            - Instead, tell the user that no different emails appeared in the current batch.
            - Follow the mandatory pagination instruction when no different emails appeared.
            - If the returned emails list is empty, clearly state that no unread emails matched the search.
            - If one relevant email remains, present its sender, subject, date, and a brief description based only on its metadata.
            - If multiple relevant emails remain, list every relevant returned email in a numbered list.
            - For each listed email, include only its sender, subject, date, and a short description supported by its metadata.
            - Never claim that all matching emails were found when has_more is true.
            - If has_more is false, do not suggest expanding the search.
            - After listing relevant emails, invite the user to select one and specify what they want to do.
            - The maximum number of emails displayed in one response is 15.
            - Do not mention internal tool names.
            - Do not claim to have read the complete email body.
            - Do not expose message_id, thread_id, or next_page_token unless the user explicitly requests technical details.
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
        reason = tool_result.get("reason")

        if reason == "multiple_email_read_not_supported":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that only one complete email can be read per request.
                - Ask which requested email they want to read first.
                - Do not claim that emails were searched or found.
                - Do not invent or list email metadata.
            """

        if reason == "multiple_matching_emails":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that multiple matching emails were found.
                - List every item from matching_emails.
                - Preserve each item's exact order and position value.
                - Show sender, subject, date, and snippet.
                - Ask which numbered email they want to read.
                - Do not claim that any email was read.
                - Do not invent information.
                - Do not expose message IDs.
            """

        return f"""
            Tool result:
            {tool_result}

            Rules:
            - If read is successful, present the complete email naturally.
            - Treat tool_result as the only source of truth.
            - Do not invent missing information.
            - Do not expose message IDs.
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
