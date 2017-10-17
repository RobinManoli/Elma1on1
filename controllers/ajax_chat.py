# -*- coding: utf-8 -*-

# user gets chat
@auth.requires_login()
def get():
    if request.vars.id is None: return
    id = request.vars.id

    # get the 99 latest after id, or if no id, just 99 latest
    dbchat = db( db.chat.id>id ).select( orderby=~db.chat.id, limitby=(0,99) )
    chat = []
    # reverse order here, but orderby to get latest rows
    for row in dbchat:
        d = {}
        d['id'] = row.id
        d['username'] = row.person.username
        d['text'] = row.text
        d['created'] = str( row.created )[:19]
        chat.insert( 0, d )
    return response.json( chat )

# user sends chat
@auth.requires_login()
def send():
    if request.vars.text is None: return
    text = request.vars.text
    db.chat.insert( person=auth.user, text=text )
    return '1'
