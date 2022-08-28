import context.broad_context
import context.formats.html

import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

# https://stackoverflow.com/questions/17669952/finding-proper-nouns-using-nltk-wordnet

tst = "computer-networks-conferences-in-2022"

is_noun = lambda pos: pos[:2] == 'NN'

tst = tst.replace('-',' ')

# Split off the prepositional phrases (need the core subject's plurality)
preps = [' on ', ' in ', ' about ', ' of ', ' for ']

for prep in preps:

    try:
        tst = tst[:tst.index(prep)]
        break
    except:
        pass

tokenized = nltk.word_tokenize(tst)

nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]

print('{}'.format(nouns))

currentElement = context.formats.html.Element()

for formatType in context.broad_context.AllPrimitives:
    newElements = context.formats.html.Cleanup_GeneralMatchSplittingSingle(currentElement, formatType)