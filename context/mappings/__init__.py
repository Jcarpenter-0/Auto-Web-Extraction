from typing import List
from typing import Dict

import json
import re

import context.formats.html

# ====================================================================================================
# Methods for applying mappings
# ====================================================================================================
# Field: ('Field-Label', [Regexes], {PoS Characteristics}, Primitive, Is-Label, Behavior Function)

# Labeled Data Example: Name + Name
# ('Name', [('Name-Label', [Regexes], ...), ('Name-Data', [Regexes], ...)])

def MatchMappings(elements:List[context.formats.html.Element], mappings:List[tuple]) -> List[tuple]:
    """Given a set of mapping rules, apply ratings to them"""

    ratings = []

    for element in elements:

        for mapping in mappings:

            # Adjust overall scores based on cluster size disconnect? Eg: if mapping is 3 elements, and cluster is 300, then reduce overall scores?
            #clusterToMappingDiff = 1 - abs(len(elements) - len(mapping[1]))/max(len(elements),len(mapping))

            mappingName = mapping[0]
            mappingScore = 0

            fieldScores = []

            for field in mapping[1]:

                fieldName = field[0]

                for fieldRules in field[1]:
                    fieldScore = 0

                    fieldComponentName = fieldRules[0]

                    # apply the text characteristic check
                    if fieldRules[2] is not None:
                        for PoSChar in fieldRules[2]:

                            threshold = fieldRules[2][PoSChar]

                            if PoSChar in element.TextType.keys():
                                occurrence = element.TextType[PoSChar]

                                if occurrence >= threshold:
                                    fieldScore += 1

                    # apply the type check
                    if fieldRules[3] is not None:
                        if element.Primitive == fieldRules[3]:
                            fieldScore += 1

                    # apply the regex checks
                    if fieldRules[1] is not None:
                        for regex in fieldRules[1]:
                            foundEntries = regex.findall(element.InnerHTML)

                            if len(foundEntries) > 0:
                                fieldScore += 1
                                break

                    # apply behavior rules
                    if fieldRules[5] is not None:
                        fieldScore += fieldRules[5](element.InnerHTML)

                    fieldScores.append((fieldScore, fieldName, fieldComponentName, fieldRules[4]))
                    mappingScore += fieldScore

            ratings.append((mappingScore, mappingName, element, fieldScores))

    return ratings


# ====================================================================================================
# Common mappings and relationships, here one defines the rules that will take clustered data and map
# ====================================================================================================

EventMapping = ('Event', [('Event-Date', [('Event-Date-Label', None, {'NNP':0.25}, 'String', True, None),
                                          ('Event-Date-Data', None, None,'Date Range', False, None),])
                          ,('Event-Important-Date', [('Event-Date-Label', None, {'NN':0.25}, 'String', True, None),
                                          ('Event-Date-Data', None, None,'Date', False, None),])])

#
ProductMapping = ('Product', [('Product-Name', [('Product-Name-Label', None, {'NN':0.25}, 'String', True, None),
                                                ('Product-Name-Data', None, {'NNP':0.75}, 'String', False, None)]),
                              ('Product-Price', [('Product-Price-Label', [re.compile("[Pp]rice"), re.compile("[Bb]uy")], {'NN':0.25}, 'String', True, None),
                                                 ('Product-Price-Data', None, None, 'Currency', False, None)])])

# =====================================================================================================

AllMappings = []

AllMappings.append(ProductMapping)
AllMappings.append(EventMapping)

# =====================================================================================================
# Specific Mapping Cases
# =====================================================================================================
