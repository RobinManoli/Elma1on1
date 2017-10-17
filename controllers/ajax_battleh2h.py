# -*- coding: utf-8 -*-
@auth.requires_login()
def register():
    if not request.vars.player1 or not request.vars.player2: return
    player1 = request.vars.player1
    player2 = request.vars.player2
    if player1 == player2: return
    user1 = db( db.auth_user.username==player1 ).select( limitby=(0,1) ).first()
    user2 = db( db.auth_user.username==player2 ).select( limitby=(0,1) ).first()
    if not user1 or not user2: return
    # don't allow host as player
    if user1.id == auth.user_id or user2.id == auth.user_id: return

    battle = db.battle_h2h.insert( length=10, host=auth.user, player1=user1, player2=user2, host_status='registered', player1_status='invited', player2_status='invited' )
    return battle.id

@auth.requires_login()
def player_ready():
    if not request.vars.id:
        return
    id = request.vars.id
    battle = db.battle_h2h( id )
    if not battle:
        return

    if battle.player1.id == auth.user_id and battle.player1_status == 'invited':
        battle.player1_status = 'ready'
    elif battle.player2.id == auth.user_id and battle.player2_status == 'invited':
        battle.player2_status = 'ready'
    else:
        # request not coming from player of this battle
        return

    battle.update_record()
    return response.json( dict(player1_status=battle.player1_status, player2_status=battle.player2_status) )

@auth.requires_login()
def check_acceptance():
    if not request.vars.id:
        return
    id = request.vars.id
    battle = db.battle_h2h( id )
    if not battle or battle.host != auth.user_id:
        return

    if battle.player1_status != 'ready' or battle.player2_status != 'ready':
        return response.json( dict(player1_status=battle.player1_status, player2_status=battle.player2_status) )

    if not battle.level_filename:
        # level filenaming base
        filename = "Lg14zzzz"
        # get latest battle by filename, ascending since battles go from z to a to 9 to 2
        latest_battle = db( db.battle_h2h.level_filename ).select( orderby=db.battle_h2h.level_filename, limitby=(0,1) ).first()
        if latest_battle and latest_battle.level_filename:
            battle.level_filename = get_prev_filename( latest_battle.level_filename )
        else:
            battle.level_filename = get_prev_filename( filename )

    # strip out all non alphanumeric characters of username, for being able to enter username in level title in elma editor
    player1 = ''.join(ch for ch in battle.player1.username if ch.isalnum()).lower()
    player2 = ''.join(ch for ch in battle.player2.username if ch.isalnum()).lower()
    host = ''.join(ch for ch in battle.host.username if ch.isalnum()).lower()
    # elma editor allows to type 29 characters in title
    battle.level_title = "%s vs %s by %s" % ( player1, player2, host )[:29]
    battle.update_record()

    return response.json( dict(player1_status=battle.player1_status, player2_status=battle.player2_status, level_filename=battle.level_filename, level_title=battle.level_title) )

@auth.requires_login()
def check_upload():
    if not request.vars.id:
        return
    id = request.vars.id
    battle = db.battle_h2h( id )
    if not battle or battle.host != auth.user_id:
        return
    if battle.player1_status != 'ready' or battle.player2_status != 'ready' or battle.host_status != 'registered':
        return
    if not battle.level_filename or not battle.level_title:
        return

    if not battle.eol_level_id:
        # find case insensitive filename* case sensitive *TitLE* levels
        # returns list of eol level id's, latest levels last
        levels = eol_find_level( battle.level_filename, battle.level_title )
        if len( levels ) > 1:
            # there are level duplicates, so remove last char of level title
            battle.update_record( level_title=battle.level_title[:-1] )
            return response.json( dict(level_title=battle.level_title) )
        if len( levels ) < 1:
            return response.json( dict(eol_level_id=0) )

        # battle starts here
        battle.eol_level_id = int( levels[0] )

        battle.started = request.utcnow
        battle.host_status = "uploaded"
        #import datetime
        #local_battle_end = request.now + datetime.timedelta( minutes=battle.length+1 )

        # load url after setting started value, as otherwise the end call will happen before the actual end
        #import urllib2
        #import urllib
        #url = 'http://localhost/call.php?id=%d&seconds=%d' % ( battle.id, battle.length*60 )
        #html = urllib.urlopen(url).read()

        #import threading
        #url = 'http://elma.eartheart.se/ajax_battleh2h/end_battle?id=%s' % battle.id
        #def go():
        #    html = urllib.urlopen(url).read()
        #threading.Timer( battle.length*10, go ).start()


        #data = dict( id=battle.id, hour=local_battle_end.hour, minute=local_battle_end.minute ) # set post data
        #data = dict( id=battle.id, seconds=battle.length ) # set post data
        #data = urllib.urlencode(data)
        #req = urllib2.Request(url, data)
        #resp = urllib2.urlopen(req) # perform request
        #html = resp.read()
        #seconds_left = battle.length * 60 + 60 - local_battle_end.second
        # if couldn't contact own server, unlikely to happen
        #if not html:
        #    return
        # everything worked, now update
        battle.update_record()


    return response.json( dict(eol_level_id=battle.eol_level_id, seconds_left=battle.length*60) )

@auth.requires_login()
def check_started():
    if not request.vars.id:
        return
    id = request.vars.id
    battle = db.battle_h2h( id )
    if not battle or (battle.player1 != auth.user_id and battle.player2 != auth.user_id):
        return

    if battle.started:
        import datetime
        # calculate battle time without minding the time difference of local time and utc
        #battle_time = battle.length * 60 + 60 - battle.started.second # in seconds
        elapsed_time = request.utcnow - battle.started
        seconds_left = battle.length*60 - elapsed_time.seconds
        return response.json( dict(seconds_left=seconds_left, level_filename=battle.level_filename, eol_level_id=battle.eol_level_id) )
    # not ready yet
    return response.json( dict(player1_status=battle.player1_status, player2_status=battle.player2_status ) )


# doesn't require login, since it is done from command line, and simply checks if time is up
def end_battle():
    if not request.vars.id:
        return
    id = request.vars.id
    battle = db.battle_h2h( id )
    if not battle:
        return
    import datetime
    if not battle.ended and datetime.datetime.utcnow() >= battle.started + datetime.timedelta( minutes=battle.length ):
        # todo: end battle stuff
        times = eol_get_level_times( battle.eol_level_id )
        for time in times:
            if time['username'].lower() == battle.player1.username.lower():
                battle.player1_time = int( time['eoltime'].replace(':','').replace(",","") )
                battle.player1_timeindex = int( time['timeindex'] )
            elif time['username'].lower() == battle.player2.username.lower():
                battle.player2_time = int( time['eoltime'].replace(':','').replace(",","") )
                battle.player2_timeindex = int( time['timeindex'] )

        if battle.player1_time is None and battle.player2_time is not None:
            battle.player2_status = "won"
            battle.player1_status = "lost"

        elif battle.player2_time is None and battle.player1_time is not None:
            battle.player1_status = "won"
            battle.player2_status = "lost"

        elif battle.player1_time == battle.player2_time:
            battle.player1_status = "drew"
            battle.player2_status = "drew"

        elif battle.player1_time < battle.player2_time:
            battle.player1_status = "won"
            battle.player2_status = "lost"

        elif battle.player1_time > battle.player2_time:
            battle.player2_status = "won"
            battle.player1_status = "lost"

        battle.ended = request.utcnow
        battle.update_record()
    return '1' # return if went this far, as only first end request goes into if clause above
