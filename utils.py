import re

def extract_json(text):
    """
    Extract the first JSON object substring from a string.
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
    except Exception:
        pass
    return text
