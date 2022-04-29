import re

# ======================================================================================================================
# Basic Primitive Data Format Regexes
# ======================================================================================================================

UnitsOfMeasure = []

Address = [re.compile("[0-9]+ [A-Za-z]+ (Ave)?(St)? [A-Z][A-Z],? [A-Z][a-z]+,? [A-Z][A-Z] [0-9]+"),
           re.compile("[A-Z]{0,10}[a-z]{0,10}, [A-Z]{0,10}[a-z]{0,10}, [A-Z]{0,10}[a-z]{0,9}")]

Names = [re.compile("[A-Z][a-z]+\s[A-Z]\.\s[A-Z][a-z]+"),
    re.compile("[A-Z][a-z]+\s[A-Z][a-z]+")]

DateRanges = [re.compile("[JFMASOND]{0,1}[A-Z]{0,9}[a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]")]

DateRegexses = [
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m [A-Z][A-Z] ?[A-Z][A-Z][A-Z]?"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], [1-9][0-9][0-9][0-9]+ +\([1-9]?[0-9]:[0-9][0-9], [A-Z][A-Z][A-Z]-[0-9]+, [A-Z][A-Z][A-Z]\)"),
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m ?[A-Z][A-Z][A-Z]?"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ \([1-9]?[0-9]:[0-9][0-9][ap]m [A-Z][A-Z][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ *\([1-9]?[0-9]:[0-9][0-9][A-Z][A-Z] [A-Z][a-z]+ [Tt]ime\)"),
    re.compile("[MTWFS][a-z]+, [0-9]?[0-9] [JFMASOND][a-z]+ [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9][ap]m [A-Z][A-Z][A-Z]"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][a-zA-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+, [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ [1-3]*[0-9], [1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+,? [JFMASOND][a-z]+ [1-3]*[0-9], ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [1-3]*[0-9], [1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9] ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[1-3]?[0-9] [JFMASOND][a-z]+ [1-9][0-9][0-9][0-9]+"),
    re.compile("[0-9][0-9]\\\[0-9][0-9]\\\[0-9]+"),
    re.compile("[0-9][0-9]-[0-9][0-9]-[0-9]+")
]

AllPrimitives = []
AllPrimitives.append(DateRanges)
AllPrimitives.append(DateRegexses)
AllPrimitives.append(Names)
AllPrimitives.append(Address)

# ======================================================================================================================
# Label-less fields, broadly defined
# ======================================================================================================================
LabelLessFields = dict()

LabelLessFields['Full-Name'] = Names

LabelLessFields['Mailing-Address'] = []
LabelLessFields['Mailing-Address'].extend(Address)

# ======================================================================================================================
# Basic relational mapping, eg: person, car, location, etc
# ======================================================================================================================

DefaultMapping = []

# ======================================================================================================================
# English language grammar pre-defines
# ======================================================================================================================

Conjunctions = ['for','and','nor','but','or','yet','so','both','either','neither','only','whether']
