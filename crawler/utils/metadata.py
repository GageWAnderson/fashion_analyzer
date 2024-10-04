import json


def extract_media_urls(media_urls_metadata_json_str: str) -> list[str]:
    return json.loads(media_urls_metadata_json_str)
