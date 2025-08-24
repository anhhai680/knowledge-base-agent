import tiktoken
import json

def count_tokens(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def load_json(json_file):
    with open(json_file) as f:
        return json.load(f)

# Determine the language for syntax highlighting
def get_language_by_extension(file_extension):
    if file_extension in ['py', 'python']:
        return 'python'
    elif file_extension in ['js', 'jsx', 'javascript']:
        return 'javascript'
    elif file_extension == 'css':
        return 'css'
    elif file_extension in ['ts', 'typescript', 'tsx']:
        return 'typescript'
    elif file_extension == 'php':
        return 'php'
    elif file_extension == 'cs':
        return 'c-sharp'
    else:
        return None