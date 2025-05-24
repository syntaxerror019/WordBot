import os
from timing import Timer

class Categorizer:
    def __init__(self, folder_path):
        self.categories = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
        
        self.category_words = {}
        for category in self.categories:
            category_path = os.path.join(folder_path, category)
            self.category_words[category] = self.load_words(category_path)

    def load_words(self, category):
        with open(category, 'r') as f:
            return f.read().lower().splitlines()

    def check_categories(self, word):
        for category, words in self.category_words.items():
            if word in words:
                return True, category[:-4]
        return False, None