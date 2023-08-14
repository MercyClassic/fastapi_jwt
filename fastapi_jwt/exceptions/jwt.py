

class FailGetAttribute(Exception):
    def __init__(self, username_field: str, model):
        message = f'No field "{username_field}" in model {model}'
        super().__init__(message)
