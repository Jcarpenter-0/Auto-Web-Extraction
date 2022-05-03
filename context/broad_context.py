import re

# ======================================================================================================================
# Basic Primitive Data Format Regexes
# ======================================================================================================================

Currency = [re.compile("\$[0-9]+\.[0-9][0-9]")]

Address = [re.compile("[0-9]+ [A-Za-z]+ (Ave)?(St)? [A-Z][A-Z],? [A-Z][a-z]+,? [A-Z][A-Z] [0-9]+"),
           re.compile("[A-Z]{1,10}[a-z]{1,10}, [A-Z]{1,3}[a-z]{0,3}, [A-Z]{1,3}")]

Names = [re.compile("[A-Z][a-z]{1,14}\s[A-Z][a-z]{1,14}")]

DateRanges = [re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.[JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][A-Z]{0,9}[a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9] - [0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2} \d{4,6}"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]{1,2}–[0-9]{1,2} [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}–[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}-[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}.[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.\d{1,2}, \d{4,6}")]

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
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9] [1-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9] ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z][a-z] [1-3]?[0-9] ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[1-3]?[0-9] [JFMASOND][a-z]+ [1-9][0-9][0-9][0-9]+"),
    re.compile("[0-9][0-9]\\\[0-9][0-9]\\\[0-9]+"),
    re.compile("[0-9][0-9]-[0-9][0-9]-[0-9]+")
]

AllPrimitives = []
AllPrimitives.append(Currency)
AllPrimitives.append(DateRanges)
AllPrimitives.append(DateRegexses)
AllPrimitives.append(Address)
AllPrimitives.append(Names)
