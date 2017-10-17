# -*- coding: utf-8 -*-
"""
THESE FUNCTIONS ARE LOW LEVEL FUNCTIONS THAT CAN BE USED ALREADY BEFORE DB.PY
"""

# return dictionary of _data-prefixed keys
# takes args such as _content_theme='a' and returns {'_data-content-theme':'a'}, for faster jqm data-attributes typing
def datattr( **kwargs ):
    result = {}
    for key, value in kwargs.iteritems():
        if len(key) > 1 and key[0] == '_':
            result[ '_data-' + key[1:].replace('_','-') ] = value
    return result

# create an icon that automatically changes sorting direction
# column is the name of the column to give or given (if already sorted by this column) as an url arg
# if default_column is True, it means this column is not written in url
def asc_desc( column, default_column=False, default_sort='desc' ):
    args = []
    # if column is default and desc is default, there is no way to sort asc other than to add column to url
    if not default_column or (default_column and default_sort):
        args.append( column )

    # not sorting by column right now, so apply default
    if column not in request.args:
        if default_sort: args.append( default_sort )
    # is sorting by column right now, so apply opposite
    else:
        if 'desc' not in request.args:
            args.append( 'desc' )

    if 'desc' in args:
        img = IMG( _src=URL('static','images/keyamoon/arrow-down2.png'), _class='icon' )
    else:
        img = IMG( _src=URL('static','images/keyamoon/arrow-up2.png'), _class='icon' )
    a = A( img, _href=URL(args=args) )
    return a
        

# returns a string without lower-case L, 0 (zero), 1 (one) or upper-case o, or upper-case i
# if the parameter is an integer, it will decide the length of the returned string, and be random
def superstring( length ):
    letters = 'abcdefghijkmnopqrstuvwxyz'
    numbers = '23456789'

    import random
    ss = ''
    for char in range(0,length):
        if not ss: ss += random.choice(letters) # start with a letter
        else: ss += random.choice(letters+numbers)
    return ss
