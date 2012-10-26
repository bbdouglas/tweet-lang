#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Trains monolingual cumulative n-gram vector from a set of tweets.
# It processes tweets from multiple files, assuming that each file contains all
# tweets in a single user profile language.

import sys
import unicodedata
import json
import os.path
import cPickle

if len(sys.argv) < 2:
    print >>sys.stderr,"usage: %s <tweet files...>"%(sys.argv[0])
    print >>sys.stderr
    print >>sys.stderr,"example: %s en.json de.json ja.json"%(sys.argv[0])
    sys.exit(1)

# Tri-grams (n=3) seem to work the best for European languages, bi-grams (n=2) 
# are perhaps better for East Asian languages.
n = 3

def unescape(s):
    s = s.replace(u"&lt;", u"<")
    s = s.replace(u"&gt;", u">")
    # this has to be last:
    s = s.replace(u"&amp;", u"&")
    return s

def fix_newlines(s):
    return s.replace(u"\r\n",u"\n").replace(u"\r",u"\n").replace(u"\n",u"↵")

def fix_tabs(s):
    return s.replace(u"\t",u"⟼")

def extract_text(j):
    "Extracts plain text from the 'text' element of a tweet structure"
    p = u""
    if u'user' in j:
        #think about ignoring truncated ones...
        #if j[u'truncated']:
        #    continue   
        text = j[u'text']
        # get rid of hashtags, urls and user mentions
        spans = [] # list of [start,end] pairs
        if len(j[u'entities'][u'user_mentions']) > 0:
            # get rid of retweets
            # RT @one: RT"@two: ...
            # TODO: add support for 'via @somebody'
            i = text.find(u'RT')
            while i != -1:
                restart = -1
                for m in range(len(j[u'entities'][u'user_mentions'])):
                    mention = j[u'entities'][u'user_mentions'][m][u'indices']
                    if mention[0] == i + 3:
                        if text[mention[1]:].startswith(u':'):
                            del j[u'entities']['user_mentions'][m]           
                            spans.append([i,mention[1] + 2])
                            restart = mention[1] + 2
                            break
                    elif mention[0] > i + 3:
                        break
                if restart == -1:
                    restart = i + 2
                i = text.find(u'RT',restart)
        spans += [x[u'indices'] for x in j[u'entities'][u'hashtags']]
        spans += [x[u'indices'] for x in j[u'entities'][u'urls']]
        spans += [x[u'indices'] for x in j[u'entities'][u'user_mentions']]
        if u'media' in j[u'entities']:
            spans += [x[u'indices'] for x in j[u'entities'][u'media']]
        spans.sort() # sorts by start

        end = 0
        for span in spans:
            p += text[end:span[0]]
            end = span[1]
        p += text[end:]
        p = fix_newlines(fix_tabs(unescape(unescape(p.strip()))))
    return p

def normalize(t):
    "Basic multilingual normalization"
    return unicodedata.normalize("NFKC",t).lower()

model = {}
for f in sys.argv[1:]:
    # files are named by their language, eg "en.json", "fr.json", etc.
    lang = os.path.splitext(os.path.basename(f))[0]
    print "processing %s..."%f
    cumul = {}
    for tweet in open(f):
        j = json.loads(tweet)
        plain_text = extract_text(j)
        norm_t = normalize(plain_text)
    
        gram_vector = {}
        for l in range(0,len(norm_t)-n+1):
            gram = norm_t[l:l+n]
            count = gram_vector.setdefault(gram,0)
            gram_vector[gram] = count + 1
            count = cumul.setdefault(gram,0)
            cumul[gram] = count + 1
    model[lang] = cumul

cPickle.dump(model,open("langid.model","wb"))

print "model written to langid.model"
