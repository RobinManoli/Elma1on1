# -*- coding: utf-8 -*-
"""
THESE FUNCTIONS ARE HIGHER LEVEL FUNCTIONS RELATED TO FILENAME ONLY, RELATED TO VIEWS, NOT TO BE DEPENDABLE BY MODELS
"""

# find case insensitive filename* case sensitive *TitLE* levels
# returns list of eol level id's, no intelligible order
def eol_find_level( filename, title ):
    import urllib
    url = 'http://elmaonline.net/ajax/search/%s/level' % filename
    html = urllib.urlopen(url).read()
    html = html.replace("&","")

    dom = TAG(html)
    ids = []
    elements = dom.elements('tbody')[0].elements('tr')
    for tr in elements:
        a = tr.elements('a')
        if len( a ) < 2 or len(tr) < 3: continue
        if title in a[1].flatten():
            ids.append( tr[2].flatten() )
    return ids

# returns list of dict of time info
def eol_get_level_times( eol_level_id ):
    import urllib
    url = 'http://elmaonline.net/rss?makerss=1&levelid=%s' % str( eol_level_id )
    xml = urllib.urlopen(url).read()
    xml = xml.replace("&","")

    dom = TAG(xml)
    times = []
    items = dom.elements( 'item' )
    for item in items:
        item = item.flatten().split()
        if len(item) < 4: continue
        d = {}
        d['number'] = item[0]
        d['username'] = item[1]
        d['eoltime'] = item[2]
        d['timeindex'] = item[3]
        times.append( d )
    return times

