from dotenv import load_dotenv
import os

def get_secret(key):
    load_dotenv()
    return os.getenv(key)
