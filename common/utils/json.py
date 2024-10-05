

def extract_json_from_markdown(text: str) -> str:
    """
    Extracts JSON content from markdown-formatted text.
    LLMs often return code in markdown format for users, parses for use with raw code.
    Args:
        text (str): The markdown-formatted text containing JSON.
    
    Returns:
        str: The extracted JSON content, or an empty string if no JSON is found.
    """
    import re
    
    # Pattern to match JSON blocks in markdown, both with and without the 'json' specifier
    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    
    # Find all matches
    matches = re.findall(pattern, text)
    
    # Return the first match if found, otherwise an empty string
    return matches[0] if matches else ""