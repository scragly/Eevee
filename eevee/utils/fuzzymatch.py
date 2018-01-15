from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def get_match(word_list, word):
    result = process.extractOne(word, word_list, scorer=fuzz.ratio, score_cutoff=60)
    if not result:
        return [None, None]
    return result
