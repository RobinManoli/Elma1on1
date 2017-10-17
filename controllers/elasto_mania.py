# -*- coding: utf-8 -*-
def index():
    return dict()

@auth.requires_login()
def ready():
    query = ( ( auth.user_id==db.battle_h2h.player1 ) | ( auth.user_id==db.battle_h2h.player2 ) ) & ( db.battle_h2h.player1_status=='invited' ) & ( db.battle_h2h.player2_status=='invited' )
    battles = db( query ).select()
    #battles2 = db( db.battle_h2h.player2==auth.user_id ).select( join=db.battle_h2h.on(db.auth_user.id==db.battle_h2h.player1) )
    return dict( battles=battles )

@auth.requires_login()
def host():
    users = db( (db.auth_user.registered) ).select( orderby=db.auth_user.username )
    return dict( users=users )

def standings():
    battles = db( db.battle_h2h.ended ).select( orderby=~db.battle_h2h.ended )
    return dict( battles=battles )
