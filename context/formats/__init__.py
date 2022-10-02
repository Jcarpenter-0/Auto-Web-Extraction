from typing import List
from typing import Dict
import re

indexingTag = re.compile('[0-9]+\-')

def CleanupWhiteSpaces(dataToClean:Dict[str,str])->Dict[str,str]:
    """Simply cleans the whitespace in the dicts keys"""
    returnDict = dict()

    for key in dataToClean:
        newKey = key.strip()
        #newData = dataToClean[key].strip()

        returnDict[newKey] = dataToClean[key]

    return returnDict


def AliasGrouping(data:Dict[str, list], topName:str, aliases:List[str]) -> Dict[str, list]:
    """Just do grouping based on set of aliases and a top name"""

    returnDict = {}

    returnDict[topName] = []

    for key in data.keys():
        aliased = False

        for alias in aliases:
            if alias in data[key]:
                returnDict[topName].append(data[key])
                aliased = True
                break

        if aliased is False:
            # If alias not found, just lump it back into the data
            returnDict[key] = data[key]

    return returnDict


# ==========================================================
# Parse Primitives, the broad definitions that do not require "further context"
# ==========================================================

Currency = ('Currency',
            [re.compile("\$[0-9]+\.[0-9][0-9]"),
            re.compile("\$[0-9]+"),
             re.compile("\b[Ff]ree\s")])

Address = ('Address',
           [re.compile("[0-9]+ [A-Za-z]+ (Ave)?(St)? [A-Z][A-Z],? [A-Z][a-z]+,? [A-Z][A-Z] [0-9]+"),
           re.compile("[A-Z]{1,10}[a-z]{1,10}, [A-Z]{1,3}[a-z]{0,3}, [A-Z]{1,3}"),
           re.compile("[A-Z]{1,10}[a-z]{1,10}, [A-Z][a-z]{3,10} [A-Z][a-z]{3,10}")])

DateRanges = ('Date Range',[
              re.compile("\d{1,2} [JFMASOND][a-z]{1,9}-[JFMASOND][a-z]{1,9} \d{1,2} \d{4,6}"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.[JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.[JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[MTWFS][a-z]+ [0-9]?[0-9] - [MTWFS][a-z]+ [0-9]?[0-9] [JFMASOND][a-z]{0,10} [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z][a-z]\. [0-9]?[0-9] - [0-9]?[0-9], [0-9][0-9][0-9][0-9]+"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][A-Z]{0,9}[a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9] - [0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2} \d{4,6}"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]{1,2}–[0-9]{1,2} [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}–[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}-[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.\d{1,2}, \d{4,6}")])

DateRegexses = ('Date', [
    re.compile("[MTWFS][a-z]+, [1-9]?[0-9] ?[JFMASOND][a-z]+ ?[1-9][0-9][0-9][0-9]+ ?[1-9]?[0-9]:[0-9][0-9][ap]m ?\([A-Z][A-Z][A-Z]\)?"),
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m [A-Z][A-Z] ?[A-Z][A-Z][A-Z]?"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], [1-9][0-9][0-9][0-9]+ +\([1-9]?[0-9]:[0-9][0-9] [AaPp][Mm] [A-Z][A-Za-z][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], [1-9][0-9][0-9][0-9]+ +\([1-9]?[0-9]:[0-9][0-9], [A-Z][A-Z][A-Z]-[0-9]+, [A-Z][A-Z][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ [0-9]?[0-9], [0-9][0-9][0-9][0-9]+ \[[0-9][0-9]:[0-9][0-9] [PpAa]\.[Mm]\. [A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\]"),
    re.compile("[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] anywhere on earth ?\([A-Z][A-Z][A-Z]? -[0-9][0-9]\)"),
    re.compile("[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ at ?[1-9]?[0-9]:[0-9][0-9] [PpAa][Mm] [A-Z][a-z][A-Z]"),
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m ?[A-Z][A-Z][A-Z]?"),
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ ?\([A-Z][A-Z][A-Z]\)"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ \([1-9]?[0-9]:[0-9][0-9][ap]m [A-Z][A-Z][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ \[[1-9]?[0-1]:[0-9][0-9] [ap]\.m\. [A-Z][A-Z][A-Z]\]"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ *\([1-9]?[0-9]:[0-9][0-9][A-Z][A-Z] [A-Z][a-z]+ [Tt]ime\)"),
    re.compile("[MTWFS][a-z][a-z]\. [JFMASOND][a-z]+ [0-9]?[0-9], [0-9][0-9][0-9][0-9]+ \([0-9]?[0-9]:[0-9][0-9][AaPp][Mm] [A-Z][A-Z][A-Z][A-Z]?, [0-9]?[0-9]:[0-9][0-9][AaPp][Mm] [A-Z][A-Z][A-Z][A-Z]?\)"),
    re.compile("[JFMASOND][a-z][a-z]\. [0-9]?[0-9], [0-9][0-9][0-9][0-9]+ \([0-9]?[0-9]:[0-9][0-9][AaPp][Mm] [A-Z][a-z]+ [Tt]ime\)"),
    re.compile("[MTWFS][a-z]+, [0-9]?[0-9] [JFMASOND][a-z]+ [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9][ap]m [A-Z][A-Z][A-Z]"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[1-9]?[0-9], [1-9][0-9][0-9][0-9]+ +\([1-9]?[0-9]:[0-9][0-9], [A-Z][A-Za-o][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][a-zA-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+, [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [0-9]?[0-9] [A-Z][A-Za-z][A-Z], [1-9][0-9]+"),
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
    re.compile("[JFMASOND][a-z][a-z]\. [0-9]?[0-9], [0-9][0-9][0-9][0-9]+"),
    re.compile("[JFMASOND][a-z]+ [0-3]?[0-9][ntrs][hdt],? [1-9][0-9][0-9][0-9]+\s+\([A-Z][A-Za-z][A-Z]\)"),
    re.compile("[MTWFS][a-z][a-z]+ [JFMASOND][a-z]+ [0-3]?[0-9][ntrs][hdt],? [1-9][0-9][0-9][0-9]+"),
    re.compile("[JFMASOND][a-z]+ [0-3]?[0-9][ntrs][hdt],? [1-9][0-9][0-9][0-9]+"),
    re.compile("[0-3]?[0-9][ntrs][hdt],? [JFMASOND][a-z]+,? [1-9][0-9][0-9][0-9]+\s+\([1-9]?[0-9]:[0-9][0-9] [A-Z][A-Za-z][A-Z]\)"),
    re.compile("[0-3]?[0-9][ntrs][hdt],? of [JFMASOND][a-z]+,? [1-9][0-9][0-9][0-9]+\s+\([1-9]?[0-9]:[0-9][0-9] [A-Z][A-Za-z][A-Z]\)"),
    re.compile("[0-3]?[0-9][ntrs][hdt],?\s+[JFMASOND][a-z]+,?\s+[1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]{2,3} [0-3]?[0-9] [JFMASOND][a-z]+ [1-9][0-9][0-9][0-9]+"),
    re.compile("[0-3]?[0-9] [JFMASOND][a-z]+ [1-9][0-9][0-9][0-9]+"),
    re.compile("[JFMASOND][a-z]{2,3} [0-9]?[0-9]\s?\([Aa]nywhere on [Ee]arth\)"),
    re.compile("[JFMASOND][a-z]{2,3} [0-9]?[0-9]"),
    re.compile("[0-9][0-9]\\\[0-9][0-9]\\\[0-9]+"),
    re.compile("[0-9][0-9]/[0-9][0-9]/[0-9]+"),
    re.compile("[0-9][0-9]-[0-9][0-9]-[0-9]+")
])

Floats = ('Float', [re.compile("[\s\b][0-9]+\.[0-9][0-9]\s")])

Ints = ('Integer',[re.compile("[\s\b][0-9]+\s")])

Bools = ('Boolean',[re.compile("[Tt][Rr][Uu][Ee]\s"),
         re.compile("[Ff][Aa][Ll][Ss][Ee]\s")])

PhoneNumbers = ('Phone Number', [re.compile("[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]")])

UnitsOfMeasure = ('Unit Of Measure',[])

# Specific Context Primitives ~ These come about if we can specify them ahead of time (included as examples of what a little pre-def can achieve)
OnlineSpecific = ('Virtual Address',
           [re.compile("\w[Vv]irtual [Cc]onference\s"),])

MiscData = ('Misc',
            [re.compile("\wTBA\s")])


AllPrimitives = []
AllPrimitives.append(Currency)
AllPrimitives.append(DateRanges)
AllPrimitives.append(DateRegexses)
AllPrimitives.append(PhoneNumbers)
AllPrimitives.append(Floats)
AllPrimitives.append(Ints)
AllPrimitives.append(Bools)
AllPrimitives.append(UnitsOfMeasure)
AllPrimitives.append(Address)


# ===============================================================================================
# Label Primitives, these are used to sift through the non-primitives using well-knowns,
# this is not fleshed out yet as it is too pre-define and context specific
# ===============================================================================================

AllLabelPrimitives = []