# -*- coding: utf-8 -*-
@auth.requires_login()
def index():
    #if not auth.user: redirect( URL('vs','standings') )
    users = db( (db.auth_user.registered!=None)&(db.auth_user.id!=auth.user_id) ).select( orderby=db.auth_user.username )
    return dict( users=users )
