import re
from timing import Timer


class Dictionary:
    def __init__(self, file_path):
        self.file_path = file_path
        self.words = self.load_words()

    def load_words(self):
        with open(self.file_path, 'r') as f:
            return f.read().lower().splitlines()

    def find_word(self, syllable, used_words=set(), invalid_words=set()):
        pattern = re.compile(rf'\b\w*{syllable}\w*\b', re.IGNORECASE)
        return [
            word for word in self.words
            if pattern.match(word)
            and word.lower() not in used_words
            | invalid_words
        ]

    def check_word(self, word):
        return word in self.words

    def remove_word(self, word):
        timer = Timer()
        timer.start()
        self.words.remove(word)
        self.save_words()
        return timer.stop()

    def add_word(self, word):
        timer = Timer()
        timer.start()
        self.words.append(word)
        self.save_words()
        return timer.stop()

    def save_words(self):
        with open(self.file_path, 'w') as f:
            f.write('\n'.join(self.words))
