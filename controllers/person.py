# -*- coding: utf-8 -*-
@auth.requires_login()
def index():
    return ""

def login():
    #db.auth_user(db.auth_user.username=='ribot').update_record( password=db.auth_user.password.validate('capitene')[0] )
    username = ''
    if request.args(0): username = request.args(0)
    form=FORM(
              'Nick',
              INPUT( _name='username', _value=username, requires=IS_NOT_EMPTY(error_message='You need to write your nick') ),
              'Password',
              INPUT( _name='password', _type='password', requires=IS_NOT_EMPTY(error_message='You need to write your password') ),
              INPUT( _name='login', _type='submit', _value='Login', **datattr(_theme='b') ),
              **datattr( _ajax='false')
             )

    if request.args(1): response.flash = "Yay! You have been verified."

    def form_process( form ):
        user = auth.login_bare( form.vars.username, form.vars.password )
        if not user: form.errors.login = "Couldn't login. Wrong username or password."
        if not user.registered: redirect( URL('person','register') )

    if form.accepts( request, session, onvalidation=form_process ):
        redirect( URL('vs','index') )

    return dict( form=form )

def logout():
    auth.logout(onlogout=lambda user: session.update({'auth':None}))

def register():
    form=FORM(
              'EOL Nick (use exact spelling)',
              INPUT( _name='username', requires=IS_NOT_EMPTY(error_message='You need to write your EOL nick') ),
              BR(),
              'E-mail',
              INPUT( _name='email', _type='email' ),
              'E-mail again',
              INPUT(_name='email2', _type='email', requires=IS_EQUAL_TO(request.vars.email,error_message='Email fields are not the same') ),
              BR(),
              'Password',
              INPUT( _name='password', _type='password', requires=IS_NOT_EMPTY(error_message='You need a password') ),
              'Password again',
              INPUT( _name='password2', _type='password', requires=IS_EQUAL_TO(request.vars.password,error_message='Password fields are not the same.') ),
              INPUT( _name='register', _type='submit', _value='Register', **datattr(_theme='b') ),
              **datattr(_ajax='false')
             )

    def form_process(form):
        # find if user is in db, for example from !lev voting
        user = db( db.auth_user.username == form.vars.username ).select( limitby=(0,1) ).first()
        if user and user.registered:
            form.errors.register = "You are already registered."
        if not user:
            import urllib
            url = 'http://elmaonline.net/players/%s' % form.vars.username
            html = urllib.urlopen(url).read()
            if html.startswith("Player does not exist."):
                form.errors.username = "The nick you entered is not in EOL's database."            
            else:
                user = db.auth_user.insert( username=form.vars.username )
        if user and not user.registered:
            verification = superstring(6)
            user.update_record( verification = verification, password=db.auth_user.password.validate(form.vars.password)[0] )
            form.vars.verification = verification

    if form.accepts( request, session, onvalidation=form_process ):
        redirect( URL('person','verify',args=[form.vars.username,form.vars.verification]) )
    elif form.errors:
        response.flash = 'Registration failed. Please read the red text and fix the issues.'
    return dict(form=form)

def verify():
    if not request.args(1): redirect( URL('person','register') )
    user = db( db.auth_user.username == request.args(0) ).select( limitby=(0,1) ).first()
    verification = request.args(1)
    if not user or verification != user.verification: redirect( URL('person','register') )
    if user.registered: redirect( URL('person','login') )

    form = FORM( INPUT(_type='submit',_value='Verify'), **datattr(_ajax='false', _theme='b') )

    def form_process(form):
        import urllib2
        import urllib
        url = 'http://elmaonline.net/chat/search'
        data = dict( Text=verification ) # set post data
        data = urllib.urlencode(data)
        req = urllib2.Request(url, data)
        resp = urllib2.urlopen(req) # perform request
        html = resp.read()
        html = html.replace('&','&amp;')

        verified = False
        for tr in TAG(html).elements('tr'):
            if '( %s) !register %s'%(user.username.lower(),verification.lower()) in tr.flatten().lower():
                verified = True
                user.update_record( registered=request.utcnow )
                break
        if not verified:
            form.errors.verified = "You could not be verified. Are you sure that you are %s and wrote !register %s ?" % (user.username,verification)

    if form.accepts( request, session, onvalidation=form_process ):
        redirect( URL('person','login',args=[user.username,'verified']) )
    elif form.errors:
        response.flash = form.errors.verified


    return dict( user=user, form=form )
