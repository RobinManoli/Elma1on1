# -*- coding: utf-8 -*-
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #if dev:
    db = DAL('mysql://user:pass@localhost/elma', pool_size=5, check_reserved=['mysql','postgres'], lazy_tables=True)

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## configure email
#mail = auth.settings.mailer
#mail.settings.server = 'logging' or 'smtp.gmail.com:587'
#mail.settings.sender = 'you@gmail.com'
#mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
auth.settings.login_url = URL('person', 'login')
#auth.settings.logged_url = URL('vs', 'index')
auth.settings.logout_next = URL('person', 'login') 
auth.settings.long_expiration = 3600*24*30 # one month

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
#from gluon.contrib.login_methods.rpx_account import use_janrain
#use_janrain(auth, filename='private/janrain.key')

auth.settings.extra_fields['auth_user'] = [
                                          Field('created', 'datetime', default=request.utcnow, writable=False, readable=False ),
                                          Field('updated', 'datetime', update=request.utcnow, writable=False, readable=False ),

                                          #Field('username', label='Username', comment="This will be part of your profile's url, such as http://%s/p$
                                          #Field('nick', comment='What do you want us to call you?', length=128, ),
                                          Field('team', label='Current Team'),
                                          Field('country', 'reference country'),
                                          Field('designer_score', 'decimal(4,3)'),
                                          Field('designer_votes', 'integer'),
                                          Field('registered', 'datetime'),
                                          Field('verification', length=6),
                                          Field('logged_in', 'datetime'),
                                          Field('rider_score', 'decimal(4,3)'),
                                          Field('rider_votes', 'integer'),
                                          ]

## create all tables needed by auth if not custom tables
auth.define_tables(username=True,signature=False)

db.define_table('chat',
    Field('created', 'datetime', default=request.utcnow),
    Field('person', 'reference auth_user' ),
    Field('text', length=128),
)
# this system stuff not prefixed, or ie battle types are prefixed battle
db.define_table('battle_h2h',
                Field('level_filename', writable=False, readable=False ),
                Field('level_title', writable=False, readable=False ),
                Field('eol_level_id', 'integer', writable=False, readable=False ),
                Field('started', 'datetime' ), # when voting started
                Field('ended', 'datetime' ), # when voting ended
                Field('player1', 'reference auth_user', writable=False, readable=False ),
                Field('player2', 'reference auth_user' ),
                Field('host', 'reference auth_user' ),
                Field('player1_status', length=16 ),
                Field('player2_status', length=16 ),
                Field('host_status', length=16 ),
                Field('player1_time', 'integer', length=6 ),
                Field('player2_time', 'integer', length=6 ),
                Field('player1_timeindex', 'integer'), # eol timeindex reference
                Field('player2_timeindex', 'integer'), # eol timeindex reference
                Field('length', 'integer', length=6, default=10 ), # in minutes, one year is 525600 minutes
                Field('created', 'datetime', default=request.utcnow ), # when voting ended
               )

# eol stuff prefixed eol
db.define_table('eol_battle',
                Field('level_filename', writable=False, readable=False ),
                Field('score', 'decimal(4,3)',  writable=False, readable=False ),
                Field('votes', 'integer', default=0, writable=False, readable=False ),
                Field('designer', 'reference auth_user', writable=False, readable=False ),
                Field('created', 'datetime' ),
                Field('started', 'datetime' ),
                Field('ended', 'datetime' ),
                Field('eol_battle_id', 'integer', writable=False, readable=False ),
                Field('eol_level_id', 'integer', writable=False, readable=False ),
                Field('comments', length=1024, default='', writable=False, readable=False ),
                Field('rec_score', 'decimal(4,3)',  writable=False, readable=False ),
                Field('rec_votes', 'integer', default=0, writable=False, readable=False ),
                Field('rec_rider', 'reference auth_user', writable=False, readable=False ),
                Field('rec_comments', length=1024, default='', writable=False, readable=False ),
                #Field('votes_log', length=1024, default='', writable=False, readable=False ),
               )

db.define_table('eol_battle_vote',
                Field('score', 'decimal(4,3)'),
                Field('comment'),
                Field('voting_time', 'datetime'),
                Field('voter', 'reference auth_user'),
                Field('battle', 'reference eol_battle'),
                Field('vote_type', length=26, default='!lev'),
               )

db.define_table('country',
                Field('name', writable=False, readable=False ),
                Field('code', length=2, writable=False, readable=False ),
               )


## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)
