import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')

#tst = "computer-networks-and-computer-science-conference-in-may-2022-in-dubai"
#tst = "international-conference-on-computer-engineering-and-computer-networks-iccecn-2022-august-new-york-us"
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

