import re


def redact(text):
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "[REDACTED]", text)
    text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]+", "Bearer [REDACTED]", text)
    text = re.sub(r"api_key\s*=\s*[^\s,;]+", "api_key=[REDACTED]", text)
    text = re.sub(
        r"(postgresql://[^:]*:)[^@]*(@[^\s/]*)",
        r"\1[REDACTED]\2",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(mysql://[^:]*:)[^@]*(@[^\s/]*)",
        r"\1[REDACTED]\2",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED]", text)
    return text
