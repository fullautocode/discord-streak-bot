from random import choice, randint

def get_response(user_input: str) -> str:
    """
    Generates a response based on the user's input.

    Parameters:
    user_input (str): The input string from the user.

    Returns:
    str: A response string.
    """
    lowered: str = user_input.lower()

    if lowered == '':
        return "Well, you're awfully silent..."
    elif 'hello' in lowered:
        return 'Hello there'
    else:
        return choice(['choice 1', 'choice 2', 'choice 3'])
