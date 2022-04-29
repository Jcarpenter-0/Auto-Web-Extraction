from selenium import webdriver
import pandas as pd

import context.sources.evaluations

# ======================================================================================================================
# Data Structures for parsing web sources, used for evaluation
# ======================================================================================================================


class SearchEngine():

    def __int__(self):
        """"""

    def Query(self, browserInstance:webdriver, queryString:str, linkLimit:int=100, paginationLimit:int=10, linkEvaluator:evaluations.EvaluationModule=None) -> pd.DataFrame:
        """Given a query produce a bunch of links"""
        return None


# ======================================================================================================================
# Search Engine Implementations
# ======================================================================================================================

class Google(SearchEngine):

    def Query(self, browserInstance:webdriver, queryString:str, linkLimit:int=100, paginationLimit:int=10, linkEvaluator:evaluations.EvaluationModule=None) -> pd.DataFrame:

        # Apply query
        browserInstance.get('https://www.google.com/search?q={}'.format(queryString))

        finalLinks = dict()

        # Get Links from the search results (if any)
        # search result ID 'rso' or 'res', or class 'eqAnXb' or 'g tF2Cxc'
        try:
            searchResultLinksElement = browserInstance.find_element_by_id('res')
        except:
            searchResultLinksElement = browserInstance.find_element_by_id('rso')

        searchResultLinkElements = searchResultLinksElement.find_elements_by_tag_name('a')

        searchResultLinks = context.sources.evaluations.AnchorsToLinks(searchResultLinkElements, 'Google')
        finalLinks.update(searchResultLinks)

        # Get Links to the pagenation results (if any), all anchors here
        pagenationElement = browserInstance.find_element_by_id('xjs')
        pagenationElements = pagenationElement.find_elements_by_class_name('fl')
        pagenationLinks = context.sources.evaluations.AnchorsToLinks(pagenationElements, 'Google')

        # Related Search links, all anchors here
        #relatedSearchElements = browserInstance.find_elements_by_class_name('k8XOCe R0xfCb VCOFK s8bAkb')

        # Get Results up to n pages
        currentPage = 0

        while currentPage < len(pagenationLinks.keys()) and currentPage < paginationLimit and len(finalLinks) < linkLimit:

            print('SE Pagination : {}/{}'.format(currentPage+1, paginationLimit))

            page = list(pagenationLinks.keys())[currentPage]

            browserInstance.get(page)

            try:
                try:
                    subSearchLinkElement = browserInstance.find_element_by_id('res')
                except:
                    subSearchLinkElement = browserInstance.find_element_by_id('rso')

                subSearchLinkElements = subSearchLinkElement.find_elements_by_tag_name('a')

                subLinks = context.sources.evaluations.AnchorsToLinks(subSearchLinkElements, sourceText='Google')

                finalLinks.update(subLinks)

                # Get additional pagentation links (if any)
                subPagen = browserInstance.find_element_by_id('xjs')
                subPagenElems = subPagen.find_elements_by_class_name('fl')
                subPagenLinks = context.sources.evaluations.AnchorsToLinks(subPagenElems, 'Google')
                pagenationLinks.update(subPagenLinks)

            except Exception as ex:
                print('Issue on page {} ~ {} of Google searching {}'.format(currentPage, ex, page))

            currentPage += 1

        returnLinksDF = pd.DataFrame()

        if linkEvaluator is not None:

            for subLink in finalLinks.keys():
                subRow = linkEvaluator.EvaluateLink(browserInstance, subLink, "https://www.google.com", 0 ,-1)
                returnLinksDF = returnLinksDF.append(subRow)

        else:
            returnLinksDF['TargetURL'] = finalLinks.keys()
            returnLinksDF['SourceURL'] = finalLinks.values()

        return returnLinksDF


class Bing(SearchEngine):

    def Query(self, browserInstance:webdriver, queryString:str, linkLimit:int=100, paginationLimit:int=10, linkEvaluator:evaluations.EvaluationModule=None) -> pd.DataFrame:
        # Apply query
        browserInstance.get('https://www4.bing.com/search?q={}'.format(queryString))

        finalLinks = dict()

        # Get Links from the search results (if any)
        # search result ID 'rso' or 'res', or class 'eqAnXb' or 'g tF2Cxc'
        searchResultLinksElement = browserInstance.find_element_by_id('b_results')

        searchResultLinkElements = searchResultLinksElement.find_elements_by_tag_name('a')

        searchResultLinks = context.sources.evaluations.AnchorsToLinks(searchResultLinkElements, 'Bing')
        finalLinks.update(searchResultLinks)

        # Get Links to the pagenation results (if any), all anchors here
        #paginationElement = browserInstance.find_element_by_class_name('b_pag')
        #paginationElements = paginationElement.find_elements_by_tag_name('a')
        #pagenationLinks = context.sources.evaluations.AnchorsToLinks(paginationElements, 'Google')

        returnLinksDF = pd.DataFrame()

        if linkEvaluator is not None:

            for subLink in finalLinks.keys():
                subRow = linkEvaluator.EvaluateLink(browserInstance, subLink, "https://www.bing.com", 0 ,-1)
                returnLinksDF = returnLinksDF.append(subRow)

        else:
            returnLinksDF['TargetURL'] = finalLinks.keys()
            returnLinksDF['SourceURL'] = finalLinks.values()

        return returnLinksDF


class Yahoo(SearchEngine):

    def Query(self, browserInstance:webdriver, queryString:str, linkLimit:int=100, paginationLimit:int=10, linkEvaluator:evaluations.EvaluationModule=None) -> pd.DataFrame:
        # Apply query
        browserInstance.get('https://search.yahoo.com/search?p={}'.format(queryString))

        finalLinks = dict()

        # Get Links from the search results (if any)
        # search result ID 'rso' or 'res', or class 'eqAnXb' or 'g tF2Cxc'
        searchResultLinksElement = browserInstance.find_element_by_id('web')

        searchResultLinkElements = searchResultLinksElement.find_elements_by_tag_name('a')

        searchResultLinks = context.sources.evaluations.AnchorsToLinks(searchResultLinkElements, 'Yahoo')
        finalLinks.update(searchResultLinks)

        # Get Links to the pagenation results (if any), all anchors here
        #paginationElement = browserInstance.find_element_by_class_name('pages')
        #paginationElements = paginationElement.find_elements_by_tag_name('a')
        #pagenationLinks = context.sources.evaluations.AnchorsToLinks(paginationElements, 'Yahoo')

        returnLinksDF = pd.DataFrame()

        if linkEvaluator is not None:

            for subLink in finalLinks.keys():
                subRow = linkEvaluator.EvaluateLink(browserInstance, subLink, "https://www.yahoo.com", 0 ,-1)
                returnLinksDF = returnLinksDF.append(subRow)

        else:
            returnLinksDF['TargetURL'] = finalLinks.keys()
            returnLinksDF['SourceURL'] = finalLinks.values()

        return returnLinksDF


class DuckDuckGo(SearchEngine):

    def Query(self, browserInstance:webdriver, queryString:str, linkLimit:int=100, paginationLimit:int=10, linkEvaluator:evaluations.EvaluationModule=None) -> pd.DataFrame:
        # Apply query
        browserInstance.get('https://duckduckgo.com/?q={}'.format(queryString))

        finalLinks = dict()

        # Get Links from the search results (if any)
        # search result ID 'rso' or 'res', or class 'eqAnXb' or 'g tF2Cxc'
        searchResultLinksElement = browserInstance.find_element_by_id('links')

        searchResultLinkElements = searchResultLinksElement.find_elements_by_tag_name('a')

        searchResultLinks = context.sources.evaluations.AnchorsToLinks(searchResultLinkElements, 'Ask')
        finalLinks.update(searchResultLinks)

        # Get Links to the pagenation results (if any), all anchors here
        #paginationElement = browserInstance.find_element_by_class_name('pages')
        #paginationElements = paginationElement.find_elements_by_tag_name('a')
        #pagenationLinks = context.sources.evaluations.AnchorsToLinks(paginationElements, 'Ask')

        returnLinksDF = pd.DataFrame()

        if linkEvaluator is not None:

            for subLink in finalLinks.keys():
                subRow = linkEvaluator.EvaluateLink(browserInstance, subLink, "https://www.ask.com", 0 ,-1)
                returnLinksDF = returnLinksDF.append(subRow)

        else:
            returnLinksDF['TargetURL'] = finalLinks.keys()
            returnLinksDF['SourceURL'] = finalLinks.values()

        return returnLinksDF
