import re
import datetime
from typing import List
from typing import Dict

class Format():

    def __init__(self,name:str,
                 specificityRules:list=[], modifiers:list=[],
                 labels:List[re.Pattern]=[], dataFormats:List[tuple]=[], countExpected:int=1):
        """Use this to more easily find the data label associatives"""

        #The single Label for this data unit eg: "date" instead of "time-of-year" for example
        self.Name:str = name

        # the possible labels
        self.Labels = labels

        # the possible modifiers that are valid, for example: "Deadline", "Due Date", anything that can stand alone or potentially map to this
        self.Modifiers = modifiers

        # the possible data formats
        self.Formats = dataFormats

        # The logic by which contextual checks further clarify this item, these contextual checks ONLY run after data is parsed
        self.SpecificityRules = specificityRules

        # the associated data
        # the number expected, if none expect any number
        self.CountExpected = countExpected

    def MatchAgainstLabel(self, value:str) -> bool:
        """Check if this matches any of the possible labels"""
        for format in self.Labels:
            match = format.match(value)

            if match is not None:
                return True

        return False

    def MatchAgainstModifiers(self, value:str) -> bool:
        for format in self.Modifiers:
            match = format.match(value)

            if match is not None:
                return True

        return False

    def MatchAgainstValue(self, value:str) -> (bool, object):
        """Check if the is match any of the accepted formats, if it does, parse it from that format"""

        # for each data parsing cluster
        for parsingApproach in self.Formats:
            for dataFormat in parsingApproach[0]:
                match = dataFormat.match(value)

                if match is not None:
                    # Parse it
                    if parsingApproach[-1] is not None:
                        try:
                            data = parsingApproach[-1](value)
                            return True, data
                        except Exception as ex:
                            print('Cannot Parse: {} - {}'.format(value, ex))
                    else:
                        return True, None

        return False, None

    def MatchAgainstRules(self, value) -> (float, int):
        """Sees how many rules this set of data matches. Returns the match percent, and the amount matched"""

        numberMatched = 0

        for rule in self.SpecificityRules:
            if rule(value):
                numberMatched += 1

        if len(self.SpecificityRules) < 1:
            return (0, 0)
        else:
            return (numberMatched/len(self.SpecificityRules), numberMatched)

    def MatchProcess(self, value:str) -> float:
        """Match against all criteria"""

        matchValue = 0.0

        matchFormat, data = self.MatchAgainstValue(value)

        if matchFormat:
            matchValue += 1

            matchPercent, ruleMatches = self.MatchAgainstRules(data)

            matchValue += matchPercent

            matchValue += ruleMatches

        return matchValue


class DataUnit():

    def __init__(self):
        """"""

        # Value of the data item
        self.Value:str = None

        # Link or text for data label
        self.Type = None

        # Where it was found, link and text (of domain) as tuple
        self.Source:tuple = None

        # Time located/extracted
        self.TimeExtracted:datetime.datetime = None

        # Misc links/text for additional information
        self.Tags:List[str] = []
