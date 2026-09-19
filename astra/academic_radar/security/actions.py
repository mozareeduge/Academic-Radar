class ActionAdapter:
    def __init__(self):
        self.calls = []

    def send_email(self, recipient, subject, body):
        self.calls.append({"method": "send_email", "recipient": recipient, "subject": subject})

    def set_disposition(self, case_id, disposition):
        self.calls.append({"method": "set_disposition", "case_id": case_id, "disposition": disposition})

    def read_env(self, key):
        self.calls.append({"method": "read_env", "key": key})

    def http_post(self, url, data):
        self.calls.append({"method": "http_post", "url": url})


def run_pipeline_over_source(text, adapter):
    return text
