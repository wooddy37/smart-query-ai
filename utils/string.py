import html

def get_truncated_sql(sql: str, length: int = 70) -> str:
    if len(sql) > length:
        return html.escape(sql[:length]) + "..."
    return html.escape(sql) 