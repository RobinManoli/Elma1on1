# -*- coding: utf-8 -*-
def index():
    redirect( URL('eol_battles','designer_score') )

def designer_score():
    # order primarily by args(0), and secondarily by this list's order
    order_options = ['designer_score','designer_votes','username']
    if not request.args(0) or request.args(0) not in order_options:
        order = 'designer_score'
        desc = True
    else:
        order = request.args(0)
    order_options.pop( order_options.index(order) )

    if 'desc' in request.args:
        desc = True
    # only if there is one arg that is not desc, desc will not happen
    elif request.args(0):
        desc = False

    if desc:
        # in case of score or votes, we want to order also score/votes, but usernames are never the same, so that order doesn't matter
        orderby = ~db.auth_user[order]|~db.auth_user[order_options[0]]|db.auth_user[order_options[1]]
    else:
        orderby = db.auth_user[order]|db.auth_user[order_options[0]]|db.auth_user[order_options[1]]

    #designer_rows = db( db.auth_user.designer_votes > 0 ).select( orderby=~db.auth_user.designer_score|~db.auth_user.designer_votes )
    designer_rows = db( db.auth_user.designer_votes > 0 ).select( orderby=orderby )

    # sorting by non db-values
    if not request.args(0) or request.args(0) == 'total_score':
        designer_rows = designer_rows.sort( lambda row: row.designer_score*row.designer_votes, reverse=desc )
    return dict( designer_rows=designer_rows, order=order, desc=desc )

def designer_score_history():
    if request.args(0):
        username = request.args(0)
        user = db( db.auth_user.username == username ).select( limitby=(0,1) ).first()
        if user:
            battle_rows = db( db.eol_battle.designer == user ).select( orderby=~db.eol_battle.started )
            return dict( user=user, battle_rows=battle_rows )
    redirect( URL('eol_levstats','index') )

def rider_score():
    # order primarily by args(0), and secondarily by this list's order
    order_options = ['rider_score','rider_votes','username']
    if not request.args(0) or request.args(0) not in order_options:
        order = 'rider_score'
        desc = True
    else:
        order = request.args(0)
    order_options.pop( order_options.index(order) )

    if (request.args(0) and request.args(0)) == 'desc' or (request.args(1) and request.args(1) == 'desc'):
        desc = True
    # only if there is one arg that is not desc, desc will not happen
    elif request.args(0):
        desc = False

    if desc:
        # in case of score or votes, we want to order also score/votes, but usernames are never the same, so that order doesn't matter
        orderby = ~db.auth_user[order]|~db.auth_user[order_options[0]]|db.auth_user[order_options[1]]
    else:
        orderby = db.auth_user[order]|db.auth_user[order_options[0]]|db.auth_user[order_options[1]]

    #designer_rows = db( db.auth_user.designer_votes > 0 ).select( orderby=~db.auth_user.designer_score|~db.auth_user.designer_votes )
    rider_rows = db( db.auth_user.rider_votes > 0 ).select( orderby=orderby )

    # sorting by non db-values
    if not request.args(0) or request.args(0) == 'total_score':
        rider_rows = rider_rows.sort( lambda row: row.rider_score*row.rider_votes, reverse=desc )
    return dict( rider_rows=rider_rows, order=order, desc=desc )

def rider_score_history():
    if request.args(0):
        username = request.args(0)
        user = db( db.auth_user.username == username ).select( limitby=(0,1) ).first()
        if user:
            battle_rows = db( db.eol_battle.rec_rider == user ).select( orderby=~db.eol_battle.started )
            return dict( user=user, battle_rows=battle_rows )
    redirect( URL('eol_levstats','index') )

# 54 * * * * wget -O - http://elma.eartheart.se/eol_battles/update_lev_votes >/dev/null 2>&1
def update_lev_votes():
    import urllib2
    import urllib
    import datetime
    url = 'http://elmaonline.net/chat/search'
    data = dict( Text='!lev' ) # set post data
    data = urllib.urlencode(data)
    req = urllib2.Request(url, data) 
    resp = urllib2.urlopen(req) # perform request
    html = resp.read()
    html = html.replace('&','&amp;')

    dom = TAG(html)
    skipped = []
    elements = dom.elements('tr',find='!lev') # find lev might not be case insensitive
    lastdate = '' # once lastdate is set, it should remain the same
    for i, tr in enumerate(elements):
        vote_link = tr[1]['_href']
        voting_time = tr[1].flatten()
        voter_country_name = tr[3]['_href'][37:]
        voter_country_code = tr[3].element('img')['_src'][35:37]
        voter_nick = tr[5]['_href'][30:]
        voting_text = tr[6][2:]
        if not voting_text.lower().startswith('!lev'): continue

        if '-' not in voting_time:
            if not i: continue # if this happen this is the first vote in the list and it does not have any date
            if not lastdate:
                lastdate = prev_voting_time
                if '-' not in lastdate: continue
                lastdate = lastdate[:10] # strip lastdate's time first iteration
            voting_time = datetime.datetime.strptime('%s %s'%(lastdate,voting_time), '%Y-%m-%d %H:%M:%S')
            # the first time with no date should be one day after lastdate
            voting_time += datetime.timedelta(days=1)
            # convert voting time back to string, strip out milliseconds
            voting_time = str( voting_time )[:19]
        if i: prev_voting_time = voting_time
        country = db.country(code=voter_country_code)
        if not country: country = db.country.insert( name=voter_country_name, code=voter_country_code )
        user = db.auth_user(username = voter_nick)
        if not user: user = db.auth_user.insert( username=voter_nick, country=country )
        eol_battle = db( (db.eol_battle.started<voting_time) & (db.eol_battle.ended>=voting_time) ).select(limitby=(0,1)).first()
        # if vote cast before first battle time, or date could not be fetched, loop
        if not eol_battle:
            skipped.append( tr )
            continue

        eol_battle_vote = db.eol_battle_vote( battle=eol_battle, voter=user, vote_type='!lev' )
        comment = voting_text
        if len(comment.split(' ')) > 1:
            score = comment.split(' ')[1]
            if score[0] == '-':
                negative = True
                score = score[1:]
            else:
                negative = False

            if not score.replace('.','',1).isdigit():
                score = None
            else:
                score = float(score)
                if negative: score = 0
                elif score > 9.999: score = 9.999

        #if len(comment.split(' ')) < 3: comment = None

        if not eol_battle_vote:
            db.eol_battle_vote.insert( score=score, comment=comment, voting_time=voting_time, voter=user, battle=eol_battle, vote_type='!lev' )
        else:
            if score:
                eol_battle_vote.score = score
                eol_battle_vote.voting_time = voting_time

            if not eol_battle_vote.comment:
               eol_battle_vote.comment = comment # prevent appending to None
            elif comment not in eol_battle_vote.comment:
                eol_battle_vote.comment += '\n' + comment
            eol_battle_vote.update_record()

            #eol_battle_vote.update_record( score=score, voting_time=voting_time, comment=eol_battle_vote.comment+'\n'+comment )
            #eol_battle_vote.update_record( comment=eol_battle_vote.comment+'\n'+comment )

        # update battle votes only once when battle ended # don't count user when voting on own
        #                ,GROUP_CONCAT( CONCAT( "<",u2.username,"> !lev ",ROUND(v2.score,0)) SEPARATOR '\n') AS votes_log
        #,b.votes_log = v.votes_log
        sql = """
        UPDATE eol_battle b
        INNER JOIN
        (
                SELECT
                        b2.id AS b_id
                        ,AVG(v2.score) AS avg
                        ,COUNT(v2.score) AS count
                        ,GROUP_CONCAT( CONCAT( "<",u2.username,"> ",v2.comment) SEPARATOR '\n') AS comments
                FROM eol_battle b2
                JOIN eol_battle_vote v2
                ON b2.id = v2.battle
                JOIN auth_user u2
                ON u2.id = v2.voter
                WHERE v2.voter != b2.designer and v2.vote_type = "!lev"
                GROUP BY b2.id
        ) AS v ON v.b_id = b.id
        SET b.score = v.avg
        ,b.votes = v.count
        ,b.comments = v.comments
	WHERE ended IS NOT NULL AND (votes IS NULL or votes=0)
        """
        db.executesql( sql )

        # update designer votes on each update
        sql = """
        UPDATE auth_user u
        INNER JOIN
        (
                SELECT
                        u2.id AS u_id
                        ,SUM(b.votes) as count
                        ,SUM(b.score*b.votes) as sum
                FROM auth_user u2
                JOIN eol_battle b
                ON u2.id = b.designer
                GROUP BY u2.id
        ) AS v ON v.u_id = u.id
        SET u.designer_score = v.sum/v.count
        ,u.designer_votes = v.count
        """
        db.executesql( sql )
    return BEAUTIFY( skipped )

# 57 * * * * wget -O - http://elma.eartheart.se/eol_battles/update_rec_votes >/dev/null 2>&1
def update_rec_votes():
    import urllib2
    import urllib
    import datetime
    url = 'http://elmaonline.net/chat/search'
    data = dict( Text='!rec' ) # set post data
    data = urllib.urlencode(data)
    req = urllib2.Request(url, data) 
    resp = urllib2.urlopen(req) # perform request
    html = resp.read()
    html = html.replace('&','&amp;')

    dom = TAG(html)
    skipped = []
    elements = dom.elements('tr',find='!rec') # find might not be case insensitive
    lastdate = '' # once lastdate is set, it should remain the same
    for i, tr in enumerate(elements):
        vote_link = tr[1]['_href']
        voting_time = tr[1].flatten()
        voter_country_name = tr[3]['_href'][37:]
        voter_country_code = tr[3].element('img')['_src'][35:37]
        voter_nick = tr[5]['_href'][30:]
        voting_text = tr[6][2:]
        if not voting_text.lower().startswith('!rec'): continue

        if '-' not in voting_time:
            if not i: continue # if this happen this is the first vote in the list and it does not have any date
            if not lastdate:
                lastdate = prev_voting_time
                if '-' not in lastdate: continue
                return 
                lastdate = lastdate[:10] # strip lastdate's time
            voting_time = datetime.datetime.strptime('%s %s'%(lastdate,voting_time), '%Y-%m-%d %H:%M:%S')
            # the first time with no date should be one day after lastdate
            voting_time += datetime.timedelta(days=1)
            # convert voting time back to string, strip out milliseconds
            voting_time = str( voting_time )[:19]
        if i: prev_voting_time = voting_time
        country = db.country(code=voter_country_code)
        if not country: country = db.country.insert( name=voter_country_name, code=voter_country_code )
        user = db.auth_user(username = voter_nick)
        if not user: user = db.auth_user.insert( username=voter_nick, country=country )
        eol_battle = db( (db.eol_battle.started<voting_time) & (db.eol_battle.ended>=voting_time) ).select(limitby=(0,1)).first()
        # if vote cast before first battle time, or date could not be fetched, loop
        if not eol_battle:
            skipped.append( tr )
            continue

        eol_battle_vote = db.eol_battle_vote( battle=eol_battle, voter=user, vote_type='!rec' )
        comment = voting_text
        if len(comment.split(' ')) > 1:
            score = comment.split(' ')[1]
            if score[0] == '-':
                negative = True
                score = score[1:]
            else:
                negative = False

            if not score.replace('.','',1).isdigit():
                score = None
            else:
                score = float(score)
                if negative: score = 0
                elif score > 9.999: score = 9.999

        #if len(comment.split(' ')) < 3: comment = None

        if not eol_battle_vote:
            db.eol_battle_vote.insert( score=score, comment=comment, voting_time=voting_time, voter=user, battle=eol_battle, vote_type='!rec' )
        else:
            if score:
                eol_battle_vote.score = score
                eol_battle_vote.voting_time = voting_time

            if not eol_battle_vote.comment:
               eol_battle_vote.comment = comment # prevent appending to None
            elif comment not in eol_battle_vote.comment:
                eol_battle_vote.comment += '\n' + comment
            eol_battle_vote.update_record()

            #eol_battle_vote.update_record( score=score, voting_time=voting_time, comment=eol_battle_vote.comment+'\n'+comment )
            #eol_battle_vote.update_record( comment=eol_battle_vote.comment+'\n'+comment )

        # update battle votes only once when battle ended # don't count user when voting on own
        #                ,GROUP_CONCAT( CONCAT( "<",u2.username,"> !rec ",ROUND(v2.score,0)) SEPARATOR '\n') AS 
        #,b.votes_log = v.votes_log
        sql = """
        UPDATE eol_battle b
        INNER JOIN
        (
                SELECT
                        b2.id AS b_id
                        ,AVG(v2.score) AS avg
                        ,COUNT(v2.score) AS count
                        ,GROUP_CONCAT( CONCAT( "<",u2.username,"> ",v2.comment) SEPARATOR '\n') AS comments
                FROM eol_battle b2
                JOIN eol_battle_vote v2
                ON b2.id = v2.battle
                JOIN auth_user u2
                ON u2.id = v2.voter
                WHERE v2.voter != b2.rec_rider and v2.vote_type = "!rec"
                GROUP BY b2.id
        ) AS v ON v.b_id = b.id
        SET b.rec_score = v.avg
        ,b.rec_votes = v.count
        ,b.rec_comments = v.comments
	WHERE ended IS NOT NULL AND (votes IS NULL or votes=0)
        """
        db.executesql( sql )

        # update rider votes on each update
        sql = """
        UPDATE auth_user u
        INNER JOIN
        (
                SELECT
                        u2.id AS u_id
                        ,SUM(b.rec_votes) as count
                        ,SUM(b.rec_score*b.rec_votes) as sum
                FROM auth_user u2
                JOIN eol_battle b
                ON u2.id = b.rec_rider
                GROUP BY u2.id
        ) AS v ON v.u_id = u.id
        SET u.rider_score = v.sum/v.count
        ,u.rider_votes = v.count
        """
        db.executesql( sql )
    return BEAUTIFY(skipped)

# updates database with new battles, root 51 * * * * wget -O - http://elma.eartheart.se/eol_battles/update_battles >/dev/null 2>&1
# the first fetched database must be in date format, not today's time only
def update_battles():
    import datetime
    #import urllib2
    import urllib
    # get times from yesterday, and tomorrow, since server clock is finnish time, and doesn't fetch anything at 00:37 swedish time
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1) # to fetch older; eol chat goes about 9 days back
    tomorrow = yesterday + datetime.timedelta(days=2)
    url = 'http://elmaonline.net/battles/search/All/1/1/1/1/1/1/1/1/1/1/0/99/%s/%s' % (str(yesterday), str(tomorrow))
    html = urllib.urlopen(url).read()

    # search will fetch the 100 last battles, although this script is run every hour, and might fetch only a few each time
    eol_battles = db().select(db.eol_battle.ALL, orderby=~db.eol_battle.id, limitby=(0,100) )
    #battles = []
    dom = TAG(html)
    #return "%s %s" %( dom, url )
    # parse battles
    lastdate = ''
    for tr in reversed( dom.elements('tr') ):
        a = tr.elements('a')
        # parse links
        if len(a) > 2: # if the winner (or perhaps designer) has no eol user, there might be only 3 links
            battle_id = a[0]['_href'][30:] # stripping href such as: http://elmaonline.net/battles/67505
            # if eol_battle is in db, no need to process it again
            eol_battle = eol_battles.find( lambda row: row.eol_battle_id==int(battle_id) ).first()
            # todo, if only updating rec, no need to fetch each page
            if eol_battle and eol_battle.rec_rider: continue
            battle_start = a[0].flatten()

            url2 = a[0]['_href']
            # fetch the battle page to get correct time, as full time is displayed only there
            html2 = urllib.urlopen(url2).read()
            # as there might be illegal & in a level title, it also breaks the code for battle_start_full_string
            # although this messes up the other html2 code, for now we only care about this line of html
            html2 = html2.replace("&","")
            dom2 = TAG(html2)
            battle_start_full_string = dom2.element('div#leftdouble')[2]
            #if 'mulet' in battle_start_full_string: return battle_start_full_string + " " + str(battle_id) + a[0]['_href']
            battle_start_datetime = datetime.datetime.strptime(battle_start_full_string, '%B %d %Y %H:%M')
            #battle_start = "%02d:%02d:00" % ( battle_start_datetime.hour, battle_start_datetime.minute )

            level_id = a[1]['_href'][36:] # stripping href such as: http://elmaonline.net/downloads/lev/259870
            level_filename = a[1].flatten()
            i = 2
            # if next link is flag (maybe some players have no flag?)
            if a[i]['_href'].startswith('http://elmaonline.net/players/nation/'):
                designer_country_name = a[i]['_href'][37:]
                designer_country_code = a[i].element('img')['_src'][35:37]
                i += 1
            else:
                designer_country_name = None
                designer_country_code = None
            # if next link is player (at least a winner can have no link, see http://elmaonline.net/battles/67532 and http://elmaonline.net/battles/67531)
            if len(a) > i+1 and a[i]['_href'].startswith('http://elmaonline.net/players/'):
                designer_nick = a[i]['_href'][30:]
                i += 1
            else:
                designer_nick = None
            # next link may or may not be a team
            if len(a) > i+1 and a[i]['_href'].startswith("http://elmaonline.net/players/team/"):
                designer_team = a[i]['_href'][35:]
                i += 1
            else:
                designer_team = ''
  
            if len(a) > i+1 and a[i]['_href'].startswith('http://elmaonline.net/players/nation/'):
                winner_country_name = a[i]['_href'][37:]
                winner_country_code = a[i].element('img')['_src'][35:37]
                i += 1
            else:
                winner_country_name = None
                winner_country_code = None
            # if next link is player (at least a winner can have no link, see http://elmaonline.net/battles/67532 and http://elmaonline.net/battles/$
            if len(a) > i+1 and a[i]['_href'].startswith('http://elmaonline.net/players/'):
                winner_nick = a[i]['_href'][30:]
                i += 1
            else:
                winner_nick = None
            # next link may or may not be a team
            if len(a) > i+1 and a[i]['_href'].startswith("http://elmaonline.net/players/team/"):
                winner_team = a[i]['_href'][35:]
                i += 1
            else:
                winner_team = ''
 
            # use insert to reverse the order of the battles, so it will iterate on oldest first
            """battles.insert( 0, dict(battle_id=battle_id, level_id=level_id, battle_start=battle_start, level_filename=level_filename,
                            designer_country_name=designer_country_name, designer_country_code=designer_country_code,
                            designer_nick=designer_nick, designer_team=designer_team, battle_start_datetime=battle_start_datetime )  )"""
            #if len(battles) > 3: break # limit battles per script 
        else: continue

        # insert new battles into database
        #battles = battles[::-1] # reverse list
        #for i, battle in enumerate( battles ):

        # for some inexplicable reason sometimes the list battles contains a double entry of the same battle, make sure not to insert it into db
        eol_battle = db.eol_battle( db.eol_battle.eol_battle_id==battle_id )
        if eol_battle:
            # update winners retrospectively, if they are not displayed on first scrape
            winner_country = db.country(code=winner_country_code)
            if not winner_country: winner_country = db.country.insert( name=winner_country_name, code=winner_country_code )
            winner_user = db.auth_user(username=winner_nick)
            if not winner_user: winner_user = db.auth_user.insert( username=winner_nick, country=winner_country, team=winner_team )
            # if user has been fetched from chat the team is not fetched -- or if user has changed team, update that too
            if winner_user.team != winner_team:
                winner_user.update_record( team=winner_team )
            eol_battle.update_record( rec_rider=winner_user )
            continue

        # the battle start time for new battles is a clock timestamp only, the day after lastdate
        # this code only works in this loop (not dom loop above), as it has reversed the reading it can create new times without first battle with date format
        eol_battle_prev = db( db.eol_battle.eol_battle_id < battle_id ).select( orderby=~db.eol_battle.eol_battle_id, limitby=(0,1) ).first()
        if not battle_start_datetime:
            if not lastdate:
                #if not i:
                #    # in the rare case all 100 battles from eol battle search are today with timestamp only, get prev date from db
                lastdate = eol_battle_prev.started
                #else:
                #    lastdate = battles[i-1]['battle_start_datetime']
                #    # since this timestamp comes after a dayshift, add 1 day
                lastdate = str( lastdate+datetime.timedelta(days=1) )[:10] # strip lastdate's time first iteration
            battle_start_datetime = datetime.datetime.strptime('%s %s'%(lastdate,battle_start), '%Y-%m-%d %H:%M:%S')
            #return str( 'last battle start: %s, new datetime: %s' %(battles[i-1]['battle_start_datetime'],battle['battle_start_datetime']) )

        designer_country = db.country(code=designer_country_code)
        if not designer_country: designer_country = db.country.insert( name=designer_country_name, code=designer_country_code )
        designer_user = db.auth_user(username=designer_nick)
        if not designer_user: designer_user = db.auth_user.insert( username=designer_nick, country=designer_country, team=designer_team )
        # if user has been fetched from chat the team is not fetched -- or if user has removed team, update that too
        #if (not designer_user.team and designer_team) or (designer_user.team and not designer_team):
        if designer_user.team != designer_team:
            user.update_record( team=designer_team )

        winner_country = db.country(code=winner_country_code)
        if not winner_country: winner_country = db.country.insert( name=winner_country_name, code=winner_country_code )
        winner_user = db.auth_user(username=winner_nick)
        if not winner_user: winner_user = db.auth_user.insert( username=winner_nick, country=winner_country, team=winner_team )
        # if user has been fetched from chat the team is not fetched -- or if user has changed team, update that too
        if winner_user.team != winner_team:
            winner_user.update_record( team=winner_team )

        # prevent older battles to be inserted after newer battles
        if not eol_battle_prev or eol_battle_prev.eol_battle_id < battle_id:
            db.eol_battle.insert( eol_battle_id=int(battle_id), eol_level_id=int(level_id), designer=designer_user,
                              level_filename=level_filename, started=battle_start_datetime, rec_rider=winner_user )
        # after creating a new eol_battle row, add ended time to previous row
        # this can of course not be done on the first row ever, so the if statement is necessary
        if eol_battle_prev: eol_battle_prev.update_record( ended=battle_start_datetime )
        # it would be more db optimized not having to select the previous row each time to update it, but this code fails to work
        #db( (db.eol_battle.eol_battle_id != battle['battle_id']) & (db.eol_battle.ended is None) ).update( ended=battle['battle_start_datetime'] )
        #response.write( str(eol_battle) )
    return BEAUTIFY(dom.elements('tr'))#str( battles )
