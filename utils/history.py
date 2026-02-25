def gradio_history_to_openai(history):
    """
    Supports:
      - list[tuple[user, assistant]]
      - list[dict{role,content}]
    """
    if not history:
        return []
    out = []
    for item in history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            out.append({"role": item["role"], "content": item["content"]})
            continue
        if isinstance(item, (list, tuple)) and len(item) == 2:
            u, a = item
            if u:
                out.append({"role": "user", "content": str(u)})
            if a:
                out.append({"role": "assistant", "content": str(a)})
    return out