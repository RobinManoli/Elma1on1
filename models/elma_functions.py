# -*- coding: utf-8 -*-
"""
THESE FUNCTIONS ARE HIGHER LEVEL FUNCTIONS RELATED TO FILENAME ONLY, RELATED TO VIEWS, NOT TO BE DEPENDABLE BY MODELS
"""

# get a filename that in elma will be above the last battle with same prefix
# for example heh33 will return heh32, so when typing heh in elma you will get to the top level with that prefix
def get_prev_filename( base ):
    letters = 'abcdefghijkmnopqrstuvwxyz'
    numbers = '23456789'
    new_filename = ''
    # treat base as a number, and return the previous numeric sequence, starting from z and ending with 2
    # loop base from behind
    for i, char in enumerate( reversed(base) ):
        if char in numbers:
            # only loop if last char is first number
            if char == numbers[0]:
                new_filename = base[:-i-1] + letters[-1] + new_filename[-i:]
                continue
            else:
                new_filename = base[:-i-1] + numbers[ numbers.index(char) - 1 ] + new_filename[-i:]
                break
        elif char in letters:
            if char == letters[0]:
                new_filename = base[:-i-1] + numbers[-1] + new_filename[-i:]
                break
            else:
                new_filename = base[:-i-1] + letters[ letters.index(char)-1 ] + new_filename[-i:]
                break
        else:
            new_filename = base[:-i-1] + numbers[0] + new_filename[-i:]
            break
    return new_filename
