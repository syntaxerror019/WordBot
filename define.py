import nltk
nltk.download('wordnet')
nltk.download('omw-1.4')  # For extra definitions

from nltk.corpus import wordnet as wn

def define(word):
    synsets = wn.synsets(word)
    if synsets:
        return synsets[0].definition()
    return None