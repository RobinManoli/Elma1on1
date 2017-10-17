#!/usr/bin/env python
import sys
import time
import urllib
import threading

if len( sys.argv ) < 3: sys.exit('Usage: /var/www/web2py/applications/elma/battle_timer.py battle_id length_in_seconds')
print sys.argv
id = int( sys.argv[1] )
seconds = int(sys.argv[2])

print "sleeping in background for %s seconds, before:" % seconds
url = 'http://elma.eartheart.se/ajax_battleh2h/end_battle?id=%s' % id
print url

#time.sleep( seconds )
def go():
    html = urllib.urlopen(url).read()

threading.Timer( seconds, go ).start()

sys.exit()
