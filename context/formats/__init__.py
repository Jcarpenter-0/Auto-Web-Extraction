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
