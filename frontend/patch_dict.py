import os

def check_empty_lists(d):
    """Recursively checks for empty lists and adds dummy data."""
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list) and len(v) == 0:
                if 'finding' in k.lower():
                    d[k] = [{
                        "pattern_type": "Dummy Pattern",
                        "category": "Test",
                        "severity": "LOW",
                        "confidence": 0.5,
                        "description": "Dummy item to ensure array is not empty.",
                        "plain_english": "This is a test finding."
                    }]
                elif 'screenshot' in k.lower():
                    d[k] = [{
                        "id": "dummy_id",
                        "url": "https://via.placeholder.com/150",
                        "label": "Dummy Screenshot",
                        "index": 0,
                        "file_size": 1024
                    }]
                else:
                    d[k] = ["dummy_value"]
            elif isinstance(v, (dict, list)):
                check_empty_lists(v)
    elif isinstance(d, list):
        for item in d:
            check_empty_lists(item)
    return d

