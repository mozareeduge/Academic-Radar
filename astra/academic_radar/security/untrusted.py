def wrap_untrusted(source_id, text):
    escaped_text = text.replace("</UNTRUSTED_SOURCE>", "[NEUTRALIZED_CLOSING_TAG]")
    return f"<UNTRUSTED_SOURCE id={source_id}>{escaped_text}</UNTRUSTED_SOURCE>"


def build_messages(system, task, case_state, sources):
    messages = [
        {"role": "system", "content": system},
        {"role": "system", "content": task},
    ]

    for source in sources:
        source_id = source.get("id")
        text = source.get("text", "")
        wrapped = wrap_untrusted(source_id, text)
        messages.append({"role": "user", "content": wrapped})

    return messages
