import re


def detect_injection(text):
    labels = []

    if re.search(r"ignore\s+previous\s+instructions", text, re.IGNORECASE):
        labels.append("ignore_previous_instructions")

    if re.search(
        r"(print|reveal|show|get|display|export)\s+.*?(environment|env|secrets|credentials|keys|aws|token)",
        text,
        re.IGNORECASE,
    ):
        labels.append("print_reveal_environment_or_secrets")

    if re.search(
        r"(send|email|notify|contact|message|forward).{0,20}([a-z0-9_.-]+@[a-z0-9.-]+|supervisor|manager|admin)",
        text,
        re.IGNORECASE,
    ):
        labels.append("send_email_a_person")

    if re.search(r"set\s+(case|status|disposition)\s+to\s+ACT", text, re.IGNORECASE):
        labels.append("set_case_to_ACT")

    if re.search(r"<!--.*?-->|<script[^>]*>.*?</script>", text, re.IGNORECASE | re.DOTALL):
        if re.search(
            r"(<!--.*?(instruction|action|command|execute).*?-->|<script[^>]*>.*(instruction|action|command|execute).*?</script>)",
            text,
            re.IGNORECASE | re.DOTALL,
        ):
            labels.append("hidden_html_or_script_instruction")

    return labels
