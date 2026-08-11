def build_calendar_search_query(
    title: str | None,
    description: str | None,
) -> str:
    query_parts = []

    for value in (title, description):
        if value is None:
            continue

        normalized_value = " ".join(value.split())
        if normalized_value:
            query_parts.append(normalized_value)

    return " ".join(query_parts)
