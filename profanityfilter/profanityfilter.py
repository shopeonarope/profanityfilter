import os
import re

import inflection


class ProfanityFilter:
    def __init__(self, **kwargs):
        """
        Returns a ProfanityFilter instance.

        Kwargs:
            - custom_censor_list (list): 
                A custom list of bad words to be used instead of the default list.
            - extra_censor_list (list): 
                A custom list of bad words to be used in conjunction with the default list.
            - no_word_boundaries (bool): 
                False means no word boundaries will be used in the regex for bad words. 
                i.e abc\ **badword**\ abc will be treated as profane.
            - censor_char (str):
                single charater to use for censored word. Default: '_'
            - censor_length (int):
                length to make censored replacement. Default '-1' use original word length
        """

        # If defined, use this instead of _censor_list
        self._custom_censor_list = kwargs.get("custom_censor_list", [])

        # Words to be used in conjunction with _censor_list
        self._extra_censor_list = kwargs.get("extra_censor_list", [])

        # Toggle use of word boundaries in regex
        self._no_word_boundaries = kwargs.get("no_word_boundaries", False)

        # What to be censored -- should not be modified by user
        self._censor_list = []

        # What to censor the words with
        self._censor_char = kwargs.get("censor_char", '_')

        self._censor_length = kwargs.get("censor_length", -1)

        # Where to find the censored words
        self._BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        self._words_file = os.path.join(self._BASE_DIR, 'data', 'badwords.txt')

        self._load_words()

    def _load_words(self):
        """Loads the list of profane words from file."""
        with open(self._words_file, 'r') as f:
            self._censor_list = [line.strip() for line in f.readlines()]

    def define_words(self, word_list):
        """Define a custom list of profane words to be used instead of the default list."""
        self._custom_censor_list = word_list

    def append_words(self, word_list):
        """Define a custom list of profane words to be used in conjunction with the default list."""
        self._extra_censor_list.extend(word_list)

    def remove_word(self, word):
        """Remove given word from censor list."""
        self._censor_list.remove(word)

    def set_censor(self, character):
        """Replaces the original censor character '*' with ``character``."""
        # TODO: what if character isn't str()-able?
        if isinstance(character, int):
            character = str(character)
        self._censor_char = character

    def has_bad_word(self, text):
        """Returns True if text contains profanity, False otherwise."""
        return self.censor(text) != text

    def get_custom_censor_list(self):
        """Returns the list of custom profane words."""
        return self._custom_censor_list

    def get_extra_censor_list(self):
        """Returns the list of custom additional profane words."""
        return self._extra_censor_list

    def get_profane_words(self):
        """Returns all profane words currently in use."""
        profane_words = []

        if self._custom_censor_list:
            profane_words = [w for w in self._custom_censor_list]  # Previous versions of Python don't have list.copy()
        else:
            profane_words = [w for w in self._censor_list]

        profane_words.extend(self._extra_censor_list)
        profane_words.extend([inflection.pluralize(word) for word in profane_words])
        profane_words = list(set(profane_words))

        # We sort the list based on decreasing word length, leaving regex patterns sorted by length at the end
        profane_words.sort(key=lambda x: (is_regex_pattern(x), -len(x)))

        return profane_words

    def restore_words(self):
        """Clears all custom censor lists and reloads the default censor list."""
        self._custom_censor_list = []
        self._extra_censor_list = []
        self._load_words()

    def censor(self, input_text):
        """Returns input_text with any profane words censored."""
        bad_words = self.get_profane_words()
        res = input_text

        for word in bad_words:
            # Apply word boundaries to the bad word
            regex_string = r'{0}' if self._no_word_boundaries else r'\b{0}\b'
            regex_string = regex_string.format(word)
            regex = re.compile(regex_string, re.IGNORECASE)
            res = regex.sub(self._censor_char * (self._censor_length if self._censor_length > -1 else len(word)), res)

        return res


    def is_clean(self, input_text):
        """Returns True if input_text doesn't contain any profane words, False otherwise."""
        return not self.has_bad_word(input_text)


    def is_profane(self, input_text):
        """Returns True if input_text contains any profane words, False otherwise."""
        return self.has_bad_word(input_text)

def is_regex_pattern(s):
    # Regex to catch common regex elements including:
    # - Escape sequences like \d, \w, \b, \S, etc.
    # - Quantifiers like *, +, ?, {n}, etc.
    # - Grouping, alternation, character classes, etc.
    regex_pattern = re.compile(r'\\[dDwWsSbB]|\*|\+|\?|\{|\}|\[|\]|\(|\)|\.|\^|\$|\\\|')
    return bool(regex_pattern.search(s))
