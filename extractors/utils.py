import re

def trim_dup_space(text:str) -> str:
    return re.sub(" +"," ", text)

def peek_generator(generator) -> bool:
    """check does generator end
    """
    try:
        next(generator)
    except StopIteration:
        return True
    return False

def count_text_words(text:str) -> int:
    """
    " " -> 0
    "abc" -> 1
    "abc " -> 1
    "abc  d" -> 2
    """
    count = 0
    lastIsChar = False
    for c in text:
        if c.isspace():
            if lastIsChar: lastIsChar = False
        else:
            if not lastIsChar:
                count += 1
                lastIsChar = True
    return count

def camel_match(text:str, pat:str) -> bool:
    # assume both text and pat are not empty
    firstCapMatch = text[0] == pat[0]
    if len(text) < len(pat): return False
    patLowerMatch = text[:len(pat)].lower() == pat.lower()
    return firstCapMatch and patLowerMatch