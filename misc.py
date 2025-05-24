import random
import string

def generate_token(length=16):
    """
      Generates a random alphanumeric token of a given length for bot.
     """
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

    return "12jkf8us6rhbxtr6"
