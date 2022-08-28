import copy
import re
import time
import numpy as np
from selenium.webdriver.remote.webdriver import WebDriver
import scipy.spatial.distance
import pandas as pd
import json
import html.parser
import string
from typing import List
from typing import Dict
import nltk
#nltk.download('punkt')
#nltk.download('averaged_perceptron_tagger')


import context
import context.broad_context

# https://www.guru99.com/xpath-selenium.html
# https://stackoverflow.com/questions/8577636/select-parent-element-of-known-element-in-selenium

HTMLRegex = '\\<*\\>'

# Prep for a selenium element query, this is some stuff for doing the xpath
SeleniumQueryString = ''

searchableChars = list(string.ascii_letters)
searchableChars.extend(list(string.digits))
searchableChars.extend(['${nbsp}'])

for index, char in enumerate(searchableChars):

    # Grab only text
    innerHtmlQuery = "contains(text(), '{}') or contains(@value, '{}') or @class = 'text'"

    valString = innerHtmlQuery.format(char,char)

    if index < len(searchableChars) - 1:
        valString += ' or '

    SeleniumQueryString += valString

# Main query with optimizations (but seems to have trouble with nbsp and other control code types
mainQuery = "/html/body//descendant::*[normalize-space(.) = {}]".format(SeleniumQueryString)

# The sub queries that may help get elements that otherwise are not captured by the general main query
seleniumQueries = ["/html/body//p"]
# ======================================================================================================================
# Field Definition, specifically a textual html field assumption
# ======================================================================================================================

# Field behaviors


class FieldBehavior(object):

    def Evaluate(self, data:str) -> float:
        """Evaluate how well this data matches the behavior expectations"""
        return NotImplementedError


class NameBehaviors(FieldBehavior):

    def Evaluate(self, data:str) -> float:
        """Check if data is/has a pronoun"""

        is_noun = lambda pos: pos[:2] == 'NN'

        tokenized = nltk.word_tokenize(data)

        nouns = [word for (word, pos) in nltk.pos_tag(tokenized) if is_noun(pos)]

        eval = 0

        if len(nouns) > 0:
            eval = 1

        return eval


# === === === === === === === === === === === === === === === === === === === === === === === === === === === === ===

class Field(object):

    def __init__(self, fieldName:str, labelFormats:List[re.Pattern]=[], dataFormats:List[re.Pattern]=[], dataTypeIndex:int=0, behaviorClasses:List[FieldBehavior]=[], occurences:int=1):
        """A field is a collection of definitions for an item of information: example: Name has many formats of label,
        expressions of format, number of occurences and certain behaviors."""

        self.FieldName:str = fieldName
        self.LabelFormats:List[re.Pattern] = labelFormats
        self.DataFormats:List[re.Pattern] = dataFormats
        self.Behaviors:List[FieldBehavior] = behaviorClasses
        self.Ocurrences:int = occurences
        self.DataTypeIndex:int = dataTypeIndex


# Some field helper methods
def GetAllFormats(fields:List[Field], labelFormats:bool=False) -> List[re.Pattern]:
    """Given a list of fields, return all the regexes defined for them. If labelFormats true will return the label
    formats else the data formats"""

    returnData = []

    for field in fields:
        if labelFormats:
            returnData.extend(field.LabelFormats)
        else:
            returnData.extend(field.DataFormats)

    return returnData


# ======================================================================================================================
# Element definition, a component of the DOM
# ======================================================================================================================


class Element(object):

    def __init__(self, tagName:str, tagID:str, parentTags:list, parentIDs:list, ancestorTags:list, ancestorTagIDs:list, elementTags:list, tagDepth:int=-1, tagIndex:int=-1
                 , innerHTML:str=None, rawInnerHTML:str=None
                 , renderX:int=-1, renderY:int=-1, containerWidth:int=-1, containerHeight:int=-1):
        """The grouping of an HTML element"""

        self.TagName:str = tagName
        self.TagID:str = tagID

        # Where the element is rendered on the page
        self.RenderedX:float = renderX
        self.RenderedY:float = renderY

        self.RenderContainerWidth:float = containerWidth
        self.RenderContainerHeight:float = containerHeight

        self.MiddleRenderX = self.RenderedX + self.RenderContainerWidth/2
        self.MiddleRenderY = self.RenderedY + self.RenderContainerHeight/2

        # Data (if any) that the tag encompassed
        self.InnerHTML:str = innerHTML
        #self.RawInnerHTML:str = rawInnerHTML

        # Demographics if this is a string (noun, proper noun, verb, etc)
        self.TextDemographics:list = []
        # Overall type, string, currency,
        self.Type:str = []

        self.Len: int = -1

        if self.InnerHTML is not None:
            self.Len:int = len(innerHTML)

        # Metrics as to where the tags occur in the html
        self.TagDepth:int = tagDepth
        self.TagIndex:int = tagIndex

        self.ParentTags:list = parentTags
        self.ParentIDs:list = parentIDs

        self.AncestorTags:list = ancestorTags
        self.AncestorTagIDs:list = ancestorTagIDs

        self.ElementTags:list = elementTags

    def GetVector(self) -> list:
        return [self.RenderedX, self.RenderedY, self.TagDepth, self.TagIndex]


def Contained(elem1:Element, elem2:Element) -> bool:
    """Check if an html element is contained within another element"""

    startX = elem2.RenderedX
    endX = elem2.RenderedX + elem2.RenderContainerWidth
    startY = elem2.RenderedY
    endY = elem2.RenderedY + elem2.RenderContainerHeight

    inX = elem1.RenderedX <= endX and elem1.RenderedX >= startX

    inY = elem1.RenderedY <= endY and elem1.RenderedY >= startY

    return inX and inY


def Distance(elem1:Element, elem2:Element) -> float:

    return scipy.spatial.distance.euclidean(elem1.GetVector(), elem2.GetVector())


def ParseWebPage(siteURL:str, seleniumWebBrowser:WebDriver, tagIgnores=['<script>', '</script>'], pageWait:float=5, verbose=False) -> (pd.DataFrame, pd.DataFrame, List[Element]):
    """Start with Selenium first, get all the rendered elements, then resolve the html locations"""

    data = pd.DataFrame()

    dataList = []

    # Open page in selenium
    seleniumWebBrowser.get(siteURL)

    time.sleep(pageWait)

    # find the element
    try:

        elems = seleniumWebBrowser.find_elements_by_xpath(mainQuery)

        for subQuery in seleniumQueries:
            subElementQuery = seleniumWebBrowser.find_elements_by_xpath(subQuery)

            elems.extend(subElementQuery)

        for idx, elem in enumerate(elems):

            t4 = elem.id
            t0 = elem.text
            t3 = elem.tag_name
            t0 = t0.lstrip()
            t0 = t0.rstrip()

            #tm = elem.get_attribute('innerHTML')

            parentTagIDs = []
            parentTagNames = []

            ancestorTags = elem.find_elements_by_xpath(".//ancestor::*")

            ancestorTagIDs = []
            ancestorTagNames = []

            for ancestorTag in ancestorTags:
                ancestorTagIDs.append(ancestorTag.id)
                ancestorTagNames.append(ancestorTag.tag_name)

            parentTags = elem.find_elements_by_xpath(".//parent::*")

            for parentTag in parentTags:
                parentTagNames.append(parentTag.tag_name)
                parentTagIDs.append(parentTag.id)

            refinedNodeTagsList = None

            if len(t0) > 1:

                if len(t0) > 0:

                    # If there is html inside of the inner html we need to do trimming of the nested html from the tags list
                    t1 = elem.get_attribute('innerHTML')

                    while '<' in t1 and '>' in t1:
                        openingCode = t1.index('<')
                        closingCode = t1.index('>')

                        if openingCode > closingCode:
                            openingCode = t1.index(openingCode+1, '<')

                        extractedTag = t1[openingCode:closingCode+1]

                        # remove only the tags
                        t1 = t1.replace(extractedTag, '')

                        extractedTag = extractedTag.replace('<','')
                        extractedTag = extractedTag.replace('>','')

                        try:
                            indexOfElementToRemove = parentTagNames.index(extractedTag)

                            del parentTagNames[indexOfElementToRemove]

                        except Exception as ex:
                            pass
                    try:
                        refinedNodeTagsList = parentTagNames[:parentTagNames.index(t3) + 1]
                    except:
                        print('Cannot find {} in parents'.format(t3))

                    tagDepth = len(ancestorTagNames) - len(parentTagNames)

                    location = elem.location
                    rectangle = elem.rect

                    x = location['x']
                    y = location['y']

                    width = rectangle['width']
                    height = rectangle['height']

                    if verbose:
                        print('===+===')
                        print('{} - x:{} y:{} w:{} h:{} tagDepth: {} tagIndex: {}'.format(t0, x, y, width, height, tagDepth, idx))

                    dataElement = Element(tagName=t3, tagID=t4, parentTags=parentTagNames, parentIDs=parentTagIDs, ancestorTags=ancestorTagNames, ancestorTagIDs=ancestorTagIDs, elementTags=refinedNodeTagsList, tagDepth=tagDepth, tagIndex=idx,
                            innerHTML=t0, rawInnerHTML=None, renderX=x, renderY=y, containerWidth=width, containerHeight=height)

                    newRow = pd.DataFrame(
                        columns=dataElement.__dict__.keys(),
                        data=[dataElement.__dict__.values()])

                    data = data.append(newRow, ignore_index=True)

                    dataList.append(dataElement)

    except Exception as ex:
        print(ex)

    return data, pd.DataFrame(columns=['Element'], data=dataList), dataList


class HTMLStrip(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.rawHTMLData:str = ''

    def handle_data(self, d):
        unbla = str(d).strip()

        if len(unbla) > 1:
            self.rawHTMLData += ' ' + unbla

    def get_data(self) -> str:
        return self.rawHTMLData

# ======================================================================================================================
# Process for taking HTML elements extracted from web pages and turning them into labeled, process-capable data
# ======================================================================================================================

def CleanupTagDumping(elements:List[Element], removeTags:List[str] = ['strike', 's']) -> List[Element]:
    """Simply go through all elements and remove the elements if the html tag is indicated in the parent tags"""

    newList = []

    for element in elements:
        foundTag = False

        for removeTag in removeTags:
            if removeTag in element.ElementTags:
                foundTag = True

        if foundTag is False:
            newList.append(element)

    return newList


def CleanupTrimming(elements:List[Element], removes:List[str]=['The ', ' the ', ' of ', 'All ', ' all ', ' and ', ' a ', 'A ', ' is ', ' Is ', ' are ', ' Are ']):
    """Simple go through all the elements and remove indicated strings in simple erasure scheme."""

    for element in elements:
        for removeItem in removes:
            if removeItem in element.InnerHTML:
                element.InnerHTML = element.InnerHTML.replace(removeItem, '')

            # trim potential whitespaces
            element.InnerHTML = element.InnerHTML.lstrip()
            element.InnerHTML = element.InnerHTML.rstrip()


def CleanupElementSubsplittingSpecific(elements:List[Element], specialSplitter='\n') -> List[Element]:
    newElementsList: List[Element] = []

    # NOTED BUG: Only splits on first character in specials list, easy fix, but focusing elsewhere

    # split on special splitters
    for idx, element in enumerate(elements):

        ongoingTagIndex = 0
        ongoingRenderedY = 32

        if specialSplitter in element.InnerHTML:

            elementSubPieces = element.InnerHTML.split(specialSplitter)

            for subPiece in elementSubPieces:

                newElement = copy.copy(element)

                ongoingTagIndex += 1
                ongoingRenderedY += 32

                newElement.InnerHTML = subPiece
                newElement.TagIndex = newElement.TagIndex + ongoingTagIndex
                newElement.TagDepth += 1
                # Magic number for "breaking"
                newElement.RenderedY += ongoingRenderedY
                newElement.Len = len(subPiece)

                newElementsList.append(newElement)

                element.InnerHTML = element.InnerHTML.replace(subPiece, '')

        else:
            newElementsList.append(element)

        if ongoingTagIndex > 0:
            # update the subsequent elements tagIndexes
            for element in elements[idx:]:
                element.TagIndex = element.TagIndex + ongoingTagIndex

    return newElementsList


def CleanupElementSubsplittingSpecifics(elements:List[Element], specialSplitters=['\n', '<br>','//', '—']) -> List[Element]:

    finalElements = elements

    for specialSplitter in specialSplitters:

        finalElements = CleanupElementSubsplittingSpecific(finalElements, specialSplitter)

    return finalElements


def Cleanup_GeneralMatchSplittingSingle(element:Element, listOfDataFormats:List[List[re.Pattern]]) -> List[Element]:
    """Given a single element, parse it out, across all formats"""

    # In order of most complex to least complex, take pieces out of the element's string
    currentText = element.InnerHTML

    tempTexts = []

    for formatType in listOfDataFormats:
        for formatSpecific in formatType:
            foundEntries = formatSpecific.findall(currentText)

            for found in foundEntries:
                # Don't add a new element if the whole element matches
                if len(found) != len(currentText):

                    foundIndex = element.InnerHTML.index(found)

                    # Where was this format found in the overall original string? this will determine "order" before return
                    tempTexts.append((found,foundIndex))

                    # Remove from original string
                    currentText = currentText.replace(found,'')

    # If there is remaining text at the end, that didn't match any formats, clean it up
    remainingTextFoundIndex = element.InnerHTML.index(currentText)
    tempTexts.append((currentText,remainingTextFoundIndex))

    # Sort by the index order
    tempTexts.sort(key=lambda x:x[1], reverse=False)

    # For each split text, make a corresponding element
    newElements = []

    for idx, textObj in enumerate(tempTexts):
        text = textObj[0]
        occurrenceIndex = textObj[1]

        newElement = copy.copy(element)

        newElement.InnerHTML = text
        # Change the Ti based on occurrence in original string
        newElement.TagIndex += idx

        # Change Render X based on the "distance in the text"
        newElement.RenderedX += (4*occurrenceIndex)

        newElements.append(newElement)

    return newElements


def Cleanup_GeneralMatchSplitting(elements:List[Element], dataFormats:List[re.Pattern]) -> List[Element]:
    """Simply take formats and if matched extract them from the element and create a new element with it"""

    # these will be where the new elements are placed, this list will be returned and "appended" to the old list
    newElementsList:List[Element] = []

    moddedElements = copy.deepcopy(elements)

    for idx, element in enumerate(moddedElements):

        ongoingTagIndex = 0

        # Want to avoid case where it will uneccessarily keep splitting, but what about combininatorial cases?
        matchedAFormatAlready = False

        for soughtItem in dataFormats:

            if matchedAFormatAlready:
                # No more format matching
                break

            foundEntries = soughtItem.findall(element.InnerHTML)

            for found in foundEntries:
                # split the found value out of the original, and make new elements

                matchedAFormatAlready = True

                if len(found) != len(element.InnerHTML):

                    parentElementCopy = copy.copy(element)

                    # erase the found value from the parent
                    element.InnerHTML = element.InnerHTML.replace(found, '')

                    ongoingTagIndex += 1

                    parentElementCopy.TagIndex = parentElementCopy.TagIndex + ongoingTagIndex

                    # set the copy's data to be what was found (the subset)
                    parentElementCopy.InnerHTML = found

                    newElementsList.append(parentElementCopy)
                else:
                    # already small (eg: matches a full format
                    break

        if ongoingTagIndex > 0:
            # update the subsequent elements tagIndexes
            for element in moddedElements[idx:]:
                element.TagIndex = element.TagIndex + ongoingTagIndex

    newElementsList.extend(moddedElements)

    return newElementsList


def Cleanup_MatchSplitting(elements:List[Element], soughtItems:List[context.Format]) -> List[Element]:
    """Go through text and try to break it into smaller elements by looking for what doesn't match any of what the
    context is looking for. Intended to alleviate cases where there are multiple data elements in the same text cluster"""

    # these will be where the new elements are placed, this list will be returned and "appended" to the old list
    newElementsList:List[Element] = []

    for idx, element in enumerate(elements):

        for soughtItem in soughtItems:

            ongoingTagIndex = 0

            # Take the first match and split on that
            # iterate over each format
            for formats, parseLogic in soughtItem.Formats:

                for format in formats:
                    foundEntries = format.findall(element.InnerHTML)

                    for found in foundEntries:
                        # split the found value out of the original, and make new elements

                        parentElementCopy = copy.copy(element)

                        # erase the found value from the parent
                        element.InnerHTML = element.InnerHTML.replace(found, '')

                        ongoingTagIndex += 1

                        parentElementCopy.TagIndex = parentElementCopy.TagIndex + ongoingTagIndex

                        # set the copy's data to be what was found (the subset)
                        parentElementCopy.InnerHTML = found

                        newElementsList.append(parentElementCopy)

        if ongoingTagIndex > 0:
            # update the subsequent elements tagIndexes
            for element in elements[idx:]:
                element.TagIndex = element.TagIndex + ongoingTagIndex

    newElementsList.extend(elements)

    return newElementsList


def Cleanup_RecursiveInnerHTMLRemover(elements:List[Element]) -> List[Element]:
    """Go through each element, and if subsequent elements are container in a bigger or preceding element, remove it from the parent. Essentially fragmenting."""

    for idx, element in enumerate(elements):

        for potentialSubElement in elements[idx+1:]:

            if len(element.InnerHTML) <= len(potentialSubElement.InnerHTML):
                # the "subset" is bigger than the set, which likely means we need to move on
                break

            if potentialSubElement.InnerHTML in element.InnerHTML:
                # remove the subset from the superset
                element.InnerHTML = element.InnerHTML.replace(potentialSubElement.InnerHTML, '')
            else:
                # if not, then softly assume that we need to move on
                break

    return elements


def Cleanup_DuplicateRemoval(elements:List[Element]) -> List[Element]:

    newElements = elements.copy()

    for idx, element in enumerate(elements):
        for trgIdx, trgElement in enumerate(elements):
            if idx != trgIdx:
                if element.InnerHTML == trgElement.InnerHTML:
                    if element not in newElements:
                        pass
                    else:
                        newElements.remove(trgElement)

    return newElements


def Clean_DuplicateMarking(elements:List[Element]) -> List[Element]:
    """When duplicate labels are found, will add some kind of textual differentiator, like the tag index"""

    for idx, element in enumerate(elements):
        for potentialSubElement in elements[idx+1:]:
            if potentialSubElement.InnerHTML in element.InnerHTML:
                # make it unique
                element.InnerHTML = element.InnerHTML.replace(potentialSubElement.InnerHTML, "{}-{}".format(potentialSubElement.TagIndex, potentialSubElement.InnerHTML))

    return elements


# ======================================================================================================================
# Evaluation Approaches
# ======================================================================================================================

class EvaluationApproaches():

    def Evaluate(self, element1:Element, element2:Element) -> float:
        return NotImplementedError


class BasicEvaluation(EvaluationApproaches):

    def Evaluate(self, element1:Element, element2:Element) -> float:

        # do horizontal biases for label association
        dataVector = element1.GetVector()

        dataSpatialVector = dataVector[0:2]

        labelVector = element2.GetVector()

        labelSpatialVector = labelVector[0:2]

        eval = scipy.spatial.distance.euclidean(dataSpatialVector, labelSpatialVector)

        return eval


class DataToLabelEvaluationHeuristic(EvaluationApproaches):

    def Evaluate(self, element1:Element, element2:Element) -> float:
        """Evaluate """

        # Regular distance
        fullDist = Distance(element1, element2)

        # do horizontal biases for label association
        dataVector = element1.GetVector()

        dataSpatialVector = dataVector[0:2]

        labelVector = element2.GetVector()

        labelSpatialVector = labelVector[0:2]

        # Horizontal Bias, if label is to the left of the data, increase its chances, if right, decrease
        if dataSpatialVector[0] > labelSpatialVector[0]:
            horizontalDist = 0
        else:
            horizontalDist = fullDist * 2

        if dataSpatialVector[1] >= labelSpatialVector[1]:
            # do vertical biases for label association
            dataSpatialVerticalVector = dataSpatialVector[0:2]
            dataSpatialVerticalVector[0] = 0

            # Label is "above" the data and want to evaluate its impact
            labelSpatialVertVector = labelSpatialVector[0:2]
            labelSpatialVertVector[0] = 0

            verticalDistance = scipy.spatial.distance.euclidean(dataSpatialVerticalVector, labelSpatialVertVector)
        else:
            # Label is "below the data" minimize its impact
            verticalDistance = fullDist * 2

        # bonus calculations
        # if the data is "contained within the render width and height of a label boost it"
        bonus = 0

        if Contained(element1, element2):
            bonus = fullDist * 0.25

        evalNum = verticalDistance + horizontalDist + fullDist - bonus

        return evalNum


class LabelToDataEvaluationHeuristic(EvaluationApproaches):

    def Evaluate(self, element1:Element, element2:Element) -> float:
        """Evaluate label distance to data reward closeness to the label"""
        # Regular distance
        fullDist = (Distance(element1, element2) + 1)

        # Do some reversed bias stuff, element 1 is label, element 2 is data
        # do horizontal biases for label association
        dataVector = element2.GetVector()

        dataSpatialVector = dataVector[0:2]

        labelVector = element1.GetVector()

        labelSpatialVector = labelVector[0:2]

        # Horizontal Bias, if label is to the left of the data, increase its chances, if right, decrease
        if dataSpatialVector[0] > labelSpatialVector[0]:
            horizontalDist = 0
        else:
            horizontalDist = fullDist * 2

        if dataSpatialVector[1] >= labelSpatialVector[1]:
            # do vertical biases for label association
            dataSpatialVerticalVector = dataSpatialVector[0:2]
            dataSpatialVerticalVector[0] = 0

            # Label is "above" the data and want to evaluate its impact
            labelSpatialVertVector = labelSpatialVector[0:2]
            labelSpatialVertVector[0] = 0

            verticalDistance = scipy.spatial.distance.euclidean(dataSpatialVerticalVector, labelSpatialVertVector)
        else:
            # Label is "below the data" minimize its impact
            verticalDistance = fullDist * 2

        # bonus calculations
        # if the data is "contained within the render width and height of a label boost it"
        bonus = 0

        if Contained(element1, element2):
            bonus = fullDist * 0.25

        evalNum = verticalDistance + horizontalDist + fullDist - bonus

        return evalNum


# ======================================================================================================================
# Helper Methods
# ======================================================================================================================


def _compileDictionaryValuesIntoBigList(srcDict:dict) -> List[re.Pattern]:
    """Simply take all the values of a dict of lists and compile all values into a list"""

    bigList = []

    for value in srcDict.values():
        bigList.extend(value)

    return bigList


def EvaluateDataAgainstFormats(data:List[Element], formats:List[re.Pattern], simpleMatch:bool=False) -> pd.DataFrame:
    """Given a set of data, evaluate how many matches it has against a list of formats"""

    evaluations = []

    for element in data:

        elementMatches = 0

        for dataFormat in formats:
            match = dataFormat.match(element.InnerHTML)
            if match != None:
                elementMatches += 1
                if simpleMatch:
                    break

        evaluations.append(elementMatches)

    dataEvaluations = pd.DataFrame()

    dataEvaluations['Element-Object'] = data
    dataEvaluations['Element-Match'] = evaluations

    return dataEvaluations


def EvaluateDataRelationships(data:List[Element], targetData:List[Element], evaluationApproach:EvaluationApproaches) -> Dict[Element, list]:
    """Generate a matrix of values for each data element and how it relates to another. Note each matrix entry has the evaluation and the element it compared to"""

    rows = dict()

    for element1 in data:

        columns = []

        for y, element2 in enumerate(targetData):

            if element1 != element2:
                columns.append((evaluationApproach.Evaluate(element1, element2), element2))
            else:
                columns.append((0,None))

        columns.sort(key=lambda x: x[0])

        rows[element1] = (columns)

    return rows


# ======================================================================================================================
# Parsing Methods
# ======================================================================================================================

def ParseFromDataFrameToList(data:pd.DataFrame) -> List[Element]:
    """Just for loading dataframes into list structures for specific python class"""

    dataList = []

    dictRows = data.to_dict('records')

    for row in dictRows:

        newDataUnit = Element(None, None, None, None, None, None, None)

        newDataUnit.__dict__ = row

        tempList1 = row['ParentTags'].replace('\'', '"')
        tempList2 = row['ParentIDs'].replace('\'', '"')

        newDataUnit.ParentTags = json.loads(tempList1)
        newDataUnit.ParentIDs = json.loads(tempList2)

        tempList3 = row['AncestorTags'].replace('\'', '"')
        tempList4 = row['AncestorTagIDs'].replace('\'', '"')

        newDataUnit.AncestorTags = json.loads(tempList3)
        newDataUnit.AncestorTagIDs = json.loads(tempList4)

        tempList5 = row['ElementTags'].replace('\'', '"')

        newDataUnit.ElementTags = json.loads(tempList5)

        dataList.append(newDataUnit)

    return dataList


