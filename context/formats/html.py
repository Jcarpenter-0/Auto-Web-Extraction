import copy
import re
import time
from selenium.webdriver.remote.webdriver import WebDriver
import scipy.spatial.distance
import pandas as pd
import json
import html.parser
import string
from typing import List
from typing import Dict
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


def ParseWebPage(siteURL:str, seleniumWebBrowser:WebDriver, tagIgnores=['<script>', '</script>'], pageWait:float=1.5, verbose=False) -> (pd.DataFrame, pd.DataFrame, List[Element]):
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


def CleanupElementSubsplittingSpecifics(elements:List[Element], specialSplitters=['\n', '<br>']) -> List[Element]:
    newElementsList: List[Element] = []

    # split on special splitters
    for idx, element in enumerate(elements):

        ongoingTagIndex = 0
        ongoingRenderedY = 32

        for splitChar in specialSplitters:

            if splitChar in element.InnerHTML:

                elementSubPieces = element.InnerHTML.split(splitChar)

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

                break

            else:
                newElementsList.append(element)
                break
        if ongoingTagIndex > 0:
            # update the subsequent elements tagIndexes
            for element in elements[idx:]:
                element.TagIndex = element.TagIndex + ongoingTagIndex

    return newElementsList


def Cleanup_GeneralMatchSplitting(elements:List[Element], dataFormats:List[re.Pattern]) -> List[Element]:
    """Simply take formats and if matched extract them from the element and create a new element with it"""

    # these will be where the new elements are placed, this list will be returned and "appended" to the old list
    newElementsList:List[Element] = []

    for idx, element in enumerate(elements):

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
            for element in elements[idx:]:
                element.TagIndex = element.TagIndex + ongoingTagIndex

    newElementsList.extend(elements)

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


def Clean_DuplicateMarking(elements:List[Element]) -> List[Element]:
    """When duplicate labels are found, will add some kind of textual differentiator, like the tag index"""

    for idx, element in enumerate(elements):
        for potentialSubElement in elements[idx+1:]:
            if potentialSubElement.InnerHTML in element.InnerHTML:
                # make it unique
                element.InnerHTML = element.InnerHTML.replace(potentialSubElement.InnerHTML, "{}-{}".format(potentialSubElement.TagIndex, potentialSubElement.InnerHTML))

    return elements


# ======================================================================================================================
# Helper Methods
# ======================================================================================================================

def _compileDictionaryValuesIntoBigList(srcDict:dict) -> List[re.Pattern]:
    """Simply take all the values of a dict of lists and compile all values into a list"""

    bigList = []

    for value in srcDict.values():
        bigList.extend(value)

    return bigList


# ======================================================================================================================
# Grab Approaches
# ======================================================================================================================

def Evaluate_By_Formats(data:List[Element], formats:List[re.Pattern]) -> pd.DataFrame:
    """Given a list of data elements and a set of formats return the ones that match"""

    dataEvaluations = pd.DataFrame()

    for dataElement in data:

        candidateEvaluation = pd.DataFrame()

        candidateEvaluation['Element'] = [dataElement]

        found = False

        for dataFormat in formats:
            match = dataFormat.match(dataElement.InnerHTML)

            if match != None:
                # found one
                found = True
                break

        if found is True:
            candidateEvaluation[dataElement.InnerHTML] = 1.00
            candidateEvaluation['Top Score'] = 1.00
        else:
            candidateEvaluation[dataElement.InnerHTML] = 0
            candidateEvaluation['Top Score'] = 0.00

        dataEvaluations = pd.concat((dataEvaluations, candidateEvaluation), axis=0, ignore_index=True)

    return dataEvaluations


def Evaluate_Labels(labelCandidates:List[Element], data:List[Element]) -> pd.DataFrame:
    """From a data-unit perspective, we must try each of the label candidates and using distance checks 'guess' which ones are right"""

    # for each data item, we want to find the possible labels (here defined as the "closest" undefined text)
    labelEvaluations = pd.DataFrame()

    for dataElement in data:

        candidateEvaluation = pd.DataFrame()

        candidateEvaluation['Element'] = [dataElement.InnerHTML]

        for labelCandidateRow in labelCandidates:

            # Regular distance
            fullDist = Distance(dataElement, labelCandidateRow)

            # do horizontal biases for label association
            dataVector = dataElement.GetVector()

            dataSpatialVector = dataVector[0:2]

            labelVector = labelCandidateRow.GetVector()

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

            if Contained(dataElement, labelCandidateRow):
                bonus = fullDist * 0.25

            evalNum = verticalDistance + horizontalDist + fullDist - bonus

            candidateEvaluation[labelCandidateRow.InnerHTML] = evalNum

        labelEvaluations = labelEvaluations.append(candidateEvaluation)

    return labelEvaluations


def Grab_LabelLessData(data:List[Element], labelName:str, labelFormats:List[re.Pattern], dataFormats:List[re.Pattern]) -> (Dict[str, object], List[Element]):
    """For data that is also its label (or standalone), the assumption is the formats here are so specific that they will standout. Will return the found fields, and the trimmed list of elements."""

    trimmedList = data.copy()

    # If any of the possible labels for this format are present, then SKIP this (eg: return empty dict)
    labelCandidates = Evaluate_By_Formats(data, labelFormats)

    labelCandidates = labelCandidates[labelCandidates['Top Score'] <= 0]

    # already have a label? End early, this is not a safe labelless grab (eg: might grab labeled data)
    if len(labelCandidates) > 0:
        return dict()

    fields = dict()

    fields[labelName] = []

    for dataElement in data:

        for dataFormat in dataFormats:
            match = dataFormat.match(dataElement.InnerHTML)

            if match != None:
                fields[labelName].append(dataElement.InnerHTML)

                # remove from the trimmed list
                trimmedList.remove(dataElement)
                break

    return fields, trimmedList


def Grab_All(data:List[Element], dataFormats) -> Dict[str, object]:
    """Find data, then reverse engineer labels from remaining text"""

    # Take the elements and refine them
    tempList = CleanupElementSubsplittingSpecifics(data)

    tempList = Cleanup_RecursiveInnerHTMLRemover(tempList)

    tempList = CleanupTagDumping(tempList)

    # for multiple formats, just iterate through all the broad context regexeses
    tempList = Cleanup_GeneralMatchSplitting(tempList, dataFormats)

    tempList = Clean_DuplicateMarking(tempList)

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = element.TagDepth * 10000
        element.TagIndex = element.TagIndex * 1000

    # Now begin evaluations to determine if data or labels, or others

    # Eval using only the date regexes
    evals = Evaluate_By_Formats(tempList, context.broad_context.DateRegexses)

    dataEvals = evals[evals['Top Score'] > 0]

    labelCandidates = evals[evals['Top Score'] <= 0]

    # Go through each data item and find the closest (with bias) text, this will be its likely label
    labelCandidates = Evaluate_Labels(list(labelCandidates['Element'].values),
                                                   list(dataEvals['Element'].values))

    # select the closest label candidate
    fields = dict()

    for rowNum, row in labelCandidates.iterrows():
        labelToDataEvaluations = row[1:]

        labelToDataEvaluations = labelToDataEvaluations.sort_values()

        labelName = labelToDataEvaluations.keys()[0]

        if labelName in fields.keys():
            # found a duplicate, make it a list
            fields[labelName].append(row[0])

        else:
            fields[labelName] = [row[0]]

    return fields


def Grab_Some(data:List[Element], dataFormats:List[re.Pattern], labelFormats:List[re.Pattern], labelName:str=None) -> Dict[str, object]:
    """Find data, find labels, then associate"""

    # Take the elements and refine them
    tempList = CleanupElementSubsplittingSpecifics(data)

    tempList = Cleanup_RecursiveInnerHTMLRemover(tempList)

    tempList = CleanupTagDumping(tempList)

    tempList = Cleanup_GeneralMatchSplitting(tempList, dataFormats)

    tempList = Clean_DuplicateMarking(tempList)

    # Boost some values, make them as or more important than the spatial values
    for element in tempList:
        element.TagDepth = element.TagDepth * 10000
        element.TagIndex = element.TagIndex * 1000

    earlyFields = dict()

    if labelName is not None:
        # Do a labelless check first
        earlyFields, tempList = Grab_LabelLessData(data, labelName=labelName, labelFormats=labelFormats, dataFormats=dataFormats)


    # Eval using only the date regexes
    evals = Evaluate_By_Formats(tempList, dataFormats)

    dataEvals = evals[evals['Top Score'] > 0]

    labelCandidates = evals[evals['Top Score'] <= 0]

    labelCandidates = Evaluate_By_Formats(list(labelCandidates['Element'].values), labelFormats)

    # Go through each data item and find the closest (with bias) text, this will be its likely label
    labelCandidates = Evaluate_Labels(list(labelCandidates['Element'].values),
                                                   list(dataEvals['Element'].values))

    # select the best label candidate
    fields = dict()

    for rowNum, row in labelCandidates.iterrows():
        labelToDataEvaluations = row[1:]

        labelToDataEvaluations = labelToDataEvaluations.sort_values()

        labelName = labelToDataEvaluations.keys()[0]

        if labelName in fields.keys():
            # found a duplicate, make it a list
            fields[labelName].append(row[0])

        else:
            fields[labelName] = [row[0]]

    fields.update(earlyFields)

    return fields

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


