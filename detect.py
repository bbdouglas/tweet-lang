#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Detects a language based on n-gram cosine similarity.

import sys
import re
import math
import unicodedata
import cPickle

if len(sys.argv) < 2:
    print >>sys.stderr,"usage: %s <model file> <tweet>"%(sys.argv[0])
    print >>sys.stderr
    print >>sys.stderr,"example: %s langid.model \"Go #Giants! Beat the #Tigers\""%(sys.argv[0])
    sys.exit(1)

n = 3

def fix_newlines(s):
    return s.replace(u"\r\n",u"\n").replace(u"\r",u"\n").replace(u"\n",u"↵")

def fix_tabs(s):
    return s.replace(u"\t",u"⟼")

def extract_text(s):
    return fix_tabs(
        fix_newlines(
            re.sub(ur"http:\S+","",
                re.sub(ur"#\S+",u"",
                    re.sub(ur"@\w+",u"",s)
                )
            )
        )
    )

def normalize(t):
    "Basic multilingual normalization"
    return unicodedata.normalize("NFKC",t).lower()

def ngram(t):
    gram_vector = {}
    for l in range(0,len(t)-n+1):
        gram = t[l:l+n]
        count = gram_vector.setdefault(gram,0)
        gram_vector[gram] = count + 1
    return gram_vector

# For sparse vectors represented by dictionaries. A vector is represented by a
# string -> number dictionary, where the string is the name of the dimension, and
# the float is the magnitude along that dimension. For example:
#   {"x":4,"y":8}

def smag(sv):
    "Sparse vector magnitude."
    return math.sqrt(sum([x**2 for x in sv.values()]))

def sdot(sv1,sv2):
    """Sparse vector dot product.
    Note, if you know ahead of time that one vector has fewer dimensions than 
    the other, put the fewer-dimensional one first in the parameter list, 
    since it will run faster."""
    tot = 0
    for (k,v) in sv1.items():
        if k in sv2:
            tot += v*sv2[k]
    return tot

def scos(sv1,sv2):
    "Cosine similarity between two sparse vectors"
    return sdot(sv1,sv2)/(smag(sv1)*smag(sv2))

models = cPickle.load(open(sys.argv[1],"rb"))
tweet = ngram(normalize(extract_text(sys.argv[2].decode("UTF-8"))))

best = 0.0
best_lang = "n/a"
for lang,model in models.items():
    sim = scos(tweet,model)
    if sim > best:
        best = sim
        best_lang = lang

print best_lang
