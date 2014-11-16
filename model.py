#!/usr/bin/env python
# encoding=utf-8
import re
import random
import os.path
import argparse
import itertools
from pattern.en.wordlist import BASIC
from pattern.en import wordnet, conjugate, pluralize, singularize, quantify, parsetree
# from pattern.search import taxonomy, WordNetClassifier
# http://www.clips.ua.ac.be/pages/pattern-en

BASE_DIR = 'data'
make_fn = lambda x: os.path.join(BASE_DIR, x)
NOUN_FILE = make_fn('nouns.txt')
VERB_FILE = make_fn('verbs.txt')
ADJ_FILE = make_fn('adjectives.txt')

singled_if_word = lambda x: singularize(x) if wordnet.synsets(singularize(x)) else None
singled_if_word_2 = lambda x: x[:-1] if wordnet.synsets(x[:-1]) else None

SOURCE = 2
if SOURCE == 0:
    NOUNS = wordnet.NOUNS.keys()
    VERBS = wordnet.VERBS.keys()
    ADJS = wordnet.ADJECTIVES.keys()
elif SOURCE == 1:
    basic_words = lambda pos: [w for w in BASIC if wordnet.synsets(w, pos=pos)]
    NOUNS = basic_words('NN')
    VERBS = basic_words('VB')
    ADJS = basic_words('JJ')
else:
    # http://dictionary-thesaurus.com/wordlists.html
    load = lambda filename: [w.lower().strip() for w in open(filename).read().split('\n') if w.lower().strip() and wordnet.synsets(w.lower().strip())]

    NOUNS = load(NOUN_FILE)
    NOUNS = [singled_if_word(x) if x.endswith('s') else x for x in NOUNS if not x.endswith('s') or singled_if_word(x)]

    VERBS = load(VERB_FILE)
    ADJS = load(ADJ_FILE)

A1 = ['start', 'stop']
A2 = ['always', 'never']
A3 = ['occasionally', 'constantly']
C = ['the', 'the', 'all those', 'so many']
C2 = ['the', 'the', 'all those']
coin_flip = lambda p: random.random() < p

# taxonomy.classifiers.append(WordNetClassifier())

def subject_from_message_old(message):
    tags = tag(message)
    print tags
    ns = [w[0] for w in tags if 'NN' in w[1]]
    if len(ns) == 0:
        return protect_against_plurals(random.choice(message.split(' ')).lower())
    return protect_against_plurals(ns[0].lower())

def max_ic(words, pos):
    subj = None
    syns = [wordnet.synsets(w, pos=pos) for w in words]
    syns = [random.choice(s) for s in syns if s]
    if syns:
        vals = [(s.synonyms[0], s.ic) for s in syns]
        if vals:
            word, val = max(vals, key=lambda x: x[1])
            subj = word
    return subj

def subject_from_message(message):
    subj = None
    tree = parsetree(message, relations=True, lemmata=True)
    nouns = [n.string for s in tree for n in s.nouns if len(n.string) > 1]
    verbs = [n.lemma if hasattr(n, 'lemma') else (n.lemmata[0] if n.lemmata else n.string) for s in tree for n in s.verbs if len(n.string) > 1]
    adjs = [n.string for s in tree for n in s.adjectives if len(n.string) > 1]
    subj = max_ic(nouns, 'NN')
    if not subj:
        ts = [v for s in tree for v in s.subjects]
        ts += [v for s in tree for v in s.objects]
        if ts:
            subj = random.choice(ts).string
    vrb = max_ic(verbs, 'VB')
    adj = max_ic(adjs, 'JJ')
    return (protect_against_plurals(subj) if subj else subj), vrb, adj

def get_related_or_not(word, d=True, pos='NN'):
    w = wordnet.synsets(word, pos=pos)
    if w:
        w = w[0]
        w1 = w.hyponyms()
        w2 = w.hypernyms()
        if w1 + w2:
            nw = random.choice([w] + w1 + w2)
            if nw and nw.senses:
                return nw.senses[0]
    elif wordnet.synsets(singularize(word)) and d:
        return get_related_or_not(singularize(word, False, pos))
    return word

def random_imperative(noun=None, get_related=True, verb=None, adj=None):
    if noun:
        n = get_related_or_not(noun, True, 'NN') if get_related else noun
    else:
        n = random.choice(NOUNS)
    if verb:
        v = get_related_or_not(verb, True, 'VB')
        if v is None:
            v = verb
    else:
        v = random.choice(VERBS)
    if not adj:
        adj = random.choice(ADJS) if coin_flip(0.5) else ''
    c = ''

    if coin_flip(0.7):
        n = pluralize(n)
        c = random.choice(C2)
    else:
        i = random.randint(1, 5)
        n = quantify(adj + ' ' + n, amount=i)
        adj = ''

    if coin_flip(0.25):
        a = ''
        v = conjugate(v)
    elif coin_flip(0.33):
        v = conjugate(v, 'part') # present participle
        a = random.choice(A1)
        c = random.choice(C)
    elif coin_flip(0.5):
        v = conjugate(v)
        a = random.choice(A2)
    else:
        v = conjugate(v)
        a = random.choice(A3)
    
    phrase = '{0} {1} {2} {3} {4}'.format(a, v, c, adj, n)
    phrase = phrase[1:] if phrase.startswith(' ') else phrase
    return re.sub(' +', ' ', phrase)

def add_qualifier(phrase, subj):
    n = None
    if subj:
        syns = wordnet.synsets(subj, pos='NN')
        if syns:
            syn = random.choice(syns)
            xs0 = syn.meronyms()
            xs1 = syn.hypernyms()
            xs2 = syn.hyponyms()
            xs = xs0 + xs1 + xs2
            if xs:
                n = random.choice(xs).synonyms[0]
    if not n:
        n = random.choice(NOUNS)
    v = random.choice(VERBS)
    a = 'cannot' if coin_flip(0.5) else 'can'
    b = 'of' if coin_flip(0.5) else 'for the'
    n = pluralize(n)
    v = conjugate(v)
    qual = '{0} you {1} {2}'.format(n, a, v)
    return '{0} {1} {2}'.format(phrase, b, qual)

def protect_against_plurals(word):
    wd = word
    if word.endswith('s'):
        wd = singled_if_word(word) if singled_if_word(word) else word
        if wd == word:
            wd = singled_if_word_2(word) if singled_if_word_2(word) else word
    return wd

def main(N=50, subject=None, verbose=True, get_related=True, verb=None, adj=None):
    if subject:
        subject = protect_against_plurals(subject)
    else:
        subject = protect_against_plurals(random.choice(NOUNS))
    if subject.lower() in ['you', 'me', 'i']:
        subject = random.choice(['people', 'self', 'soul', 'one', 'human', 'being'])
    imps = []
    for _ in xrange(N):
        if coin_flip(0.5):
            imp = random_imperative(subject, get_related, verb=verb, adj=adj)
        else:
            imp = add_qualifier(random_imperative(subject, get_related, verb=verb, adj=adj), subject)
        imps.append(imp)
    imps = [imp.capitalize() + '.' for imp in imps]
    if verbose:
        print '\n'.join(imps)
    return imps

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', default=50, type=int, help="The number of imperatives to generate.")
    parser.add_argument('-s', default=None, type=str, help="The related subject of the imperatives.")
    parser.add_argument("--msg", default=None, type=str, help="To get advice related to a message.")
    args = parser.parse_args()
    if args.msg:
        subj, verb, adj = subject_from_message(args.msg)
        print subj, verb, adj
        main(1, subj, True, False, verb=verb, adj=adj)
    else:
        main(args.n, args.s)
