

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.tools.external.gmail.draft_deletion import gmail_delete_draft_tool
from app.tools.external.gmail.draft_reading import gmail_read_specific_draft_tool
from app.tools.external.gmail.draft_sending import gmail_send_drafted_email_tool
from app.tools.external.gmail.draft_updates import gmail_update_email_draft_tool
from app.tools.external.gmail.draft_listings import gmail_search_drafted_emails_tool
from app.tools.external.gmail.received_email_actions import gmail_move_email_to_trash_tool
from app.tools.external.gmail.received_email_reading import (
    gmail_read_latest_email_tool,
    gmail_read_specific_email_tool,
)
from app.tools.external.gmail.reply_drafts import gmail_create_reply_draft_tool
from app.tools.external.gmail.sent_email_actions import gmail_move_sent_email_to_trash_tool
from app.tools.registry import TOOLS


def tool_execution_system(tool_name: str, arguments: dict, user_id:int, session: Session, conversation_id: int):

    if tool_name not in TOOLS:
        raise ValueError("Unknown tool")
    
    tool_definition  = TOOLS[tool_name]
    tool_function = tool_definition["function"]
    tool_arguments_schema = tool_definition["arguments_schema"]
    tool_result_schema = tool_definition.get("result_schema")

    if tool_arguments_schema is not None:
        try:
            validated_arguments = tool_arguments_schema.model_validate(arguments)
            arguments = validated_arguments.model_dump(mode="json")
        except ValidationError as error:

            safe_errors = [
                {
                    "field": ".".join(str(part) for part in item["loc"]),
                    "message": item["msg"],
                }
                for item in error.errors()
            ]

            raise AppError(
                code="invalid_tool_arguments",
                message="The tool arguments are invalid.",
                status_code=422,

                details={"fields": safe_errors},
            ) from error
    
    if tool_function == gmail_send_drafted_email_tool:
        tool_result = gmail_send_drafted_email_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_update_email_draft_tool:
        tool_result = gmail_update_email_draft_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_create_reply_draft_tool:
        tool_result = gmail_create_reply_draft_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_read_specific_email_tool:
        tool_result = gmail_read_specific_email_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_read_specific_draft_tool:
        tool_result = gmail_read_specific_draft_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_move_email_to_trash_tool:
        tool_result = gmail_move_email_to_trash_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_move_sent_email_to_trash_tool:
        tool_result = gmail_move_sent_email_to_trash_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_delete_draft_tool:
        tool_result = gmail_delete_draft_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    elif tool_function == gmail_search_drafted_emails_tool:
        tool_result = gmail_search_drafted_emails_tool(arguments=arguments, user_id=user_id, session=session, conversation_id=conversation_id)
    else:
        tool_result = tool_function(arguments=arguments, user_id=user_id, session=session)

    if tool_result_schema is None:
        return tool_result

    try:
        validated_result = tool_result_schema.model_validate(tool_result)
    except ValidationError as error:
        safe_errors = [
            {
                "field": ".".join(str(part) for part in item["loc"]),
                "message": item["msg"],
            }
            for item in error.errors()
        ]
        raise AppError(
            code="invalid_tool_result",
            message="The tool returned an invalid result.",
            status_code=500,
            details={"fields": safe_errors},
        ) from error

    return validated_result.model_dump(mode="json")


def build_tool_context(tool_name: str, tool_result: dict) -> str:

    emails = tool_result.get("emails")
    returned_count = tool_result.get("returned_count")
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
        drafts = tool_result.get("drafts", [])
        returned_count = tool_result.get("returned_count", len(drafts))
        has_more = tool_result.get("has_more", False)

        if has_more and returned_count < 15:
            draft_expansion_instruction = (
                f"Tell the user that only {returned_count} matching drafts are "
                "currently shown and that more are available. Ask whether they "
                "want to expand the search up to 15 drafts."
            )
        elif has_more:
            draft_expansion_instruction = (
                "Tell the user that 15 matching drafts are currently shown, which "
                "is the maximum display limit. More drafts are available, so do "
                "not claim these are all the results. Suggest refining the search "
                "by recipient, subject, keyword, or date."
            )
        else:
            draft_expansion_instruction = (
                "No additional page of matching drafts is available. Do not offer "
                "to expand the search."
            )

        return f"""
            A Gmail draft search tool was executed.

            Tool result:
            {tool_result}

            Mandatory pagination instruction:
            {draft_expansion_instruction}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - These results are Gmail drafts, not received emails and not sent emails.
            - Use returned_count to describe how many drafts are currently shown.
            - Do not describe returned_count as the user's total number of drafts.
            - If no drafts were returned, clearly state that no matching draft was found.
            - If one draft was returned, present its recipient, subject, date, and a short description based only on its snippet.
            - If multiple drafts were returned, list every returned draft in its existing order.
            - For each draft, show position, recipient, subject, date, and a short description based only on its snippet.
            - Never claim that all matching drafts were found when has_more is true.
            - Follow the mandatory pagination instruction exactly.
            - After listing drafts, invite the user to identify one and specify what they want to do with it.
            - Do not say the draft was sent.
            - Do not claim to have read content beyond the available metadata and snippet.
            - Do not invent recipients, subjects, dates, snippets, counts, or drafts.
            - Do not mention internal tool names, queries, scores, or ranking logic.
            - Do not expose draft_id unless the user explicitly asks for technical details.
            - Keep the response concise and easy to scan.
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
    if tool_name == "gmail_send_drafted_email":
        reason = tool_result.get("reason")
        matching_drafts = tool_result.get("matching_drafts_found", [])
        returned_count = tool_result.get("returned_count", len(matching_drafts))
        has_more = tool_result.get("has_more", False)

        if reason == "multiple_matching_drafts":
            if has_more and returned_count < 15:
                draft_expansion_instruction = (
                    f"Tell the user that only {returned_count} matching drafts are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 drafts or send one of the listed drafts."
                )
            elif has_more:
                draft_expansion_instruction = (
                    "Tell the user that 15 matching drafts are currently shown, which "
                    "is the maximum display limit. More drafts are available, so do "
                    "not claim these are all the results. Ask them to select one of "
                    "the listed drafts or refine the search."
                )
            else:
                draft_expansion_instruction = (
                    "No additional page of matching drafts is available. Do not offer "
                    "to expand the search. Ask the user to select one of the listed drafts."
                )

            return f"""
                A Gmail draft-send tool was executed, but no draft was sent.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {draft_expansion_instruction}

                Rules for answering:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - Clearly state that multiple matching drafts were found and no draft was sent yet.
                - List every item from matching_drafts_found in its existing order.
                - For each draft, show position, recipient, subject, date, and a short description based only on its snippet.
                - Ask which numbered draft the user wants to send.
                - Follow the mandatory pagination instruction exactly.
                - Do not claim that the draft was sent.
                - Do not invent recipients, subjects, dates, snippets, counts, or drafts.
                - Do not expose draft_id unless the user explicitly asks for technical details.
                - Keep the response concise and easy to scan.
            """

        return f"""
            A Gmail draft-send tool was executed.

            Tool result:
            {tool_result}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If sent is true, tell the user the draft was sent.
            - If sent is false, explain the reason naturally.
            - Do not claim success unless sent is true.
            - If available_drafts is present, list the available drafts and ask the user to choose one.
            - Do not invent missing information.
            - Do not expose draft_id unless the user explicitly asks for technical details.
            - Keep the response concise.
        """
    if tool_name == "gmail_update_email_draft":
        reason = tool_result.get("reason")
        matching_drafts = tool_result.get("matching_drafts_found", [])
        returned_count = tool_result.get("returned_count", len(matching_drafts))
        has_more = tool_result.get("has_more", False)

        if reason == "multiple_matching_drafts":
            if has_more and returned_count < 15:
                draft_expansion_instruction = (
                    f"Tell the user that only {returned_count} matching drafts are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 drafts or update one of the listed drafts."
                )
            elif has_more:
                draft_expansion_instruction = (
                    "Tell the user that 15 matching drafts are currently shown, which "
                    "is the maximum display limit. More drafts are available, so do "
                    "not claim these are all the results. Ask them to select one of "
                    "the listed drafts or refine the search."
                )
            else:
                draft_expansion_instruction = (
                    "No additional page of matching drafts is available. Do not offer "
                    "to expand the search. Ask the user to select one of the listed drafts."
                )

            return f"""
                A Gmail draft-update tool was executed, but no draft was updated.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {draft_expansion_instruction}

                Rules for answering:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - Clearly state that multiple matching drafts were found and no draft was updated yet.
                - List every item from matching_drafts_found in its existing order.
                - For each draft, show position, recipient, subject, date, and a short description based only on its snippet.
                - Ask which numbered draft the user wants to update.
                - Follow the mandatory pagination instruction exactly.
                - Do not claim that any draft was updated.
                - Do not invent recipients, subjects, dates, snippets, counts, or drafts.
                - Do not expose draft_id unless the user explicitly asks for technical details.
                - Keep the response concise and easy to scan.
            """

        return f"""
            A Gmail draft-update tool was executed.

            Tool result:
            {tool_result}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If updated is true, tell the user the draft was updated.
            - If updated is false, explain the reason naturally.
            - Do not claim success unless updated is true.
            - If available_drafts is present, list the available drafts and ask the user to choose one.
            - Do not invent missing information.
            - Do not expose draft_id unless the user explicitly asks for technical details.
            - Keep the response concise.
        """
    if tool_name == "gmail_read_latest_email":
        return f"""
            A Gmail recent-email reading tool was executed.

            Tool result:
            {tool_result}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If found is false, explain that the requested recent email was not available.
            - If found is true, present the complete content of every returned email naturally.
            - These emails were retrieved specifically to read their complete content.
            - Do not invent missing content, sender, subject, or date.
            - Do not mention internal tool names or technical identifiers.
            - Keep the response concise.
        """
    if tool_name == "gmail_create_reply_draft":
        reason = tool_result.get("reason")
        matching_emails = tool_result.get("matching_emails", [])
        returned_count = tool_result.get("returned_count", len(matching_emails))
        has_more = tool_result.get("has_more", False)

        if reason == "multiple_matching_emails":
            if has_more and returned_count < 15:
                pagination_instruction = (
                    f"Tell the user that only {returned_count} matching emails are "
                    "currently shown and ask whether they want to expand the search "
                    "up to 15 emails or select one to reply to."
                )
            elif has_more:
                pagination_instruction = (
                    "Tell the user that 15 matching emails are currently shown, which "
                    "is the maximum display limit. More results are available, so do "
                    "not claim these are all the matches. Ask the user to refine the "
                    "search or choose one already listed."
                )
            else:
                pagination_instruction = (
                    "Do not offer to expand the search. Ask the user to choose one "
                    "of the listed emails."
                )

            return f"""
                A Gmail reply-draft tool found multiple emails and did not create a draft.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {pagination_instruction}

                Rules for answering:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - List every item from matching_emails in its existing order.
                - For each email, show sender, subject, date, and a short description based only on its snippet.
                - Ask which numbered email the user wants to reply to.
                - Do not claim that a reply draft was created.
                - Do not invent emails, senders, subjects, dates, or snippets.
                - Do not expose technical identifiers.
                - Keep the response concise and easy to scan.
            """

        return f"""
            A Gmail reply-draft tool was executed.

            Tool result:
            {tool_result}

            Rules for answering:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If created is true, confirm that the reply draft was created, not sent.
            - If created is false, explain the reason naturally.
            - Do not claim success unless created is true.
            - Do not invent missing information.
            - Do not expose technical identifiers.
            - Keep the response concise.
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
            - If success is true, present the complete email naturally.
            - Treat tool_result as the only source of truth.
            - Do not invent missing information.
            - Do not expose message IDs.
        """

    if tool_name == "gmail_read_specific_draft":
        reason = tool_result.get("reason")

        if reason == "multiple_draft_read_not_supported":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that only one complete draft can be read per request.
                - Ask which requested draft they want to read first.
                - Do not claim that drafts were searched or found.
                - Do not invent or list draft metadata.
            """

        if reason == "multiple_matching_drafts":
            returned_count = tool_result.get("returned_count", 0)
            has_more = tool_result.get("has_more", False)

            if has_more and returned_count < 15:
                pagination_instruction = (
                    f"Tell the user that only {returned_count} matching drafts are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 drafts or select one shown."
                )
            elif has_more:
                pagination_instruction = (
                    "Tell the user that 15 matching drafts are currently shown, which "
                    "is the maximum display limit. More matching drafts are available, "
                    "so do not claim these are all results. Ask them to select one shown "
                    "or refine the search."
                )
            else:
                pagination_instruction = (
                    "No additional page of matching drafts is available. Ask the user "
                    "to select one of the shown drafts."
                )

            return f"""
                A Gmail draft-reading tool found multiple matching drafts and did not read one yet.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {pagination_instruction}

                Rules:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - List every item from matching_drafts in its existing order.
                - Preserve each item's exact position value.
                - For each draft, show recipient, subject, date, and a short description based only on its snippet.
                - Ask which numbered draft the user wants to read.
                - Do not claim that any draft was read.
                - Do not reveal any complete body before the user selects one.
                - Do not invent information or expose draft IDs.
            """

        return f"""
            Tool result:
            {tool_result}

            Rules:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If success is true, present the selected draft's recipient, subject, date, and complete body naturally.
            - If success is false, explain the reason naturally.
            - Do not claim success unless success is true.
            - Do not invent missing information.
            - Do not expose draft IDs or technical identifiers.
        """

    if tool_name == "gmail_move_email_to_trash":
        reason = tool_result.get("reason")

        if reason == "multiple_email_trash_not_supported":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that Jarvis can move only one email to trash per request.
                - Ask which email they want to move first.
                - Do not claim that any email was moved.
                - Do not invent or list email metadata.
            """

        if reason == "multiple_matching_emails":
            returned_count = tool_result.get("returned_count", 0)
            has_more = tool_result.get("has_more", False)

            if has_more and returned_count < 15:
                pagination_instruction = (
                    f"Tell the user that only {returned_count} matching emails are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 emails or choose one shown."
                )
            elif has_more:
                pagination_instruction = (
                    "Tell the user that 15 matching emails are currently shown, which "
                    "is the maximum display limit. More matching emails are available, "
                    "so do not claim these are all results. Ask them to select one shown "
                    "or refine the search."
                )
            else:
                pagination_instruction = (
                    "No additional page of matching emails is available. Ask the user "
                    "to select one of the shown emails."
                )

            return f"""
                A Gmail move-to-trash tool found multiple matching emails and did not move any email.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {pagination_instruction}

                Rules:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - List every item from matching_emails in its existing order.
                - Preserve each item's exact position value.
                - For each email, show sender, subject, date, and a short description based only on its snippet.
                - Ask which numbered email the user wants to move to trash.
                - Do not claim that any email was moved.
                - Do not invent information or expose technical identifiers.
            """

        return f"""
            Tool result:
            {tool_result}

            Rules:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If success is true, confirm that the email was moved to Gmail Trash, not permanently deleted.
            - If success is false, explain the reason naturally.
            - Do not claim success unless success is true.
            - Do not invent missing information.
            - Do not expose message IDs or technical identifiers.
        """

    if tool_name == "gmail_move_sent_email_to_trash":
        reason = tool_result.get("reason")

        if reason == "multiple_sent_email_trash_not_supported":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that Jarvis can move only one sent email to trash per request.
                - Ask which sent email they want to move first.
                - Do not claim that any email was moved.
                - Do not invent or list email metadata.
            """

        if reason == "multiple_matching_sent_emails":
            returned_count = tool_result.get("returned_count", 0)
            has_more = tool_result.get("has_more", False)

            if has_more and returned_count < 15:
                pagination_instruction = (
                    f"Tell the user that only {returned_count} matching sent emails are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 emails or choose one shown."
                )
            elif has_more:
                pagination_instruction = (
                    "Tell the user that 15 matching sent emails are currently shown, which "
                    "is the maximum display limit. More matching emails are available, "
                    "so do not claim these are all results. Ask them to select one shown "
                    "or refine the search."
                )
            else:
                pagination_instruction = (
                    "No additional page of matching sent emails is available. Ask the user "
                    "to select one of the shown emails."
                )

            return f"""
                A Gmail move-sent-email-to-trash tool found multiple matching sent emails and did not move any email.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {pagination_instruction}

                Rules:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - List every item from matching_emails in its existing order.
                - Preserve each item's exact position value.
                - For each email, show recipient, subject, date, and a short description based only on its snippet.
                - Make it clear that these are emails sent by the user.
                - Ask which numbered email the user wants to move to trash.
                - Do not claim that any email was moved.
                - Do not invent information or expose technical identifiers.
            """

        return f"""
            Tool result:
            {tool_result}

            Rules:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If success is true, confirm that the sent email was moved to Gmail Trash, not permanently deleted.
            - Make it clear that this was an email sent by the user.
            - If success is false, explain the reason naturally.
            - Do not claim success unless success is true.
            - Do not invent missing information.
            - Do not expose message IDs or technical identifiers.
        """

    if tool_name == "gmail_delete_draft":
        reason = tool_result.get("reason")

        if reason == "multiple_draft_delete_not_supported":
            return f"""
                Tool result:
                {tool_result}

                Rules:
                - Tell the user that Jarvis can permanently delete only one draft per request.
                - Ask which draft they want to delete first.
                - Do not claim that any draft was deleted.
                - Do not invent or list draft metadata.
            """

        if reason == "multiple_matching_drafts":
            returned_count = tool_result.get("returned_count", 0)
            has_more = tool_result.get("has_more", False)

            if has_more and returned_count < 15:
                pagination_instruction = (
                    f"Tell the user that only {returned_count} matching drafts are "
                    "currently shown and that more are available. Ask whether they "
                    "want to expand the search up to 15 drafts or choose one shown."
                )
            elif has_more:
                pagination_instruction = (
                    "Tell the user that 15 matching drafts are currently shown, which "
                    "is the maximum display limit. More matching drafts are available, "
                    "so do not claim these are all results. Ask them to select one shown "
                    "or refine the search."
                )
            else:
                pagination_instruction = (
                    "No additional page of matching drafts is available. Ask the user "
                    "to select one of the shown drafts."
                )

            return f"""
                A Gmail draft-delete tool found multiple matching drafts and did not delete any draft.

                Tool result:
                {tool_result}

                Mandatory pagination instruction:
                {pagination_instruction}

                Rules:
                - Treat tool_result as the only source of truth.
                - Respond in the same language as the user.
                - List every item from matching_drafts in its existing order.
                - Preserve each item's exact position value.
                - For each draft, show recipient, subject, date, and a short description based only on its snippet.
                - Ask which numbered draft the user wants to permanently delete.
                - Do not claim that any draft was deleted.
                - Do not invent information or expose technical identifiers.
            """

        return f"""
            Tool result:
            {tool_result}

            Rules:
            - Treat tool_result as the only source of truth.
            - Respond in the same language as the user.
            - If success is true, clearly confirm that the draft was permanently deleted and cannot be restored from Trash.
            - If success is false, explain the reason naturally.
            - Do not claim success unless success is true.
            - Do not invent missing information.
            - Do not expose draft IDs or technical identifiers.
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
