import datetime
import itertools
import json
import requests
from typing import Optional, TypeVar, Union
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as xml


# Base url for all queries
BASE_URL = "https://eutils.ncbi.nlm.nih.gov"

class PubMedQuery(object):
    """PubMed API Wrapper
    """

    def __init__(self, email):
        """Object Initialization

        Args:
            email (str): email of the user of the tool, not required but kindly 
                         requested by PMC (PubMed Central) in case of enquiry.".
        """

        # Parameters
        self.tool = "IntoPubMed - Jupyter Notebook for graphic content analysis (currently in development)"
        self.email = email
        self.db = "pubmed"

        self._rateLimit = 1
        self._requestsMade = []

        # Define the standard / default query parameters
        self.parameters = {"tool": self.tool, "email": self.email, "db": self.db}
    
    def query(self: object, query: str, max_results: int = 100):
        """Method that executes a query agains the GraphQL schema, automatically
           inserting the PubMed data loader.

        Args:
            query (str): String, the GraphQL query to execute against the schema.
            max_results (int, optional): max. Number of returned entries. Defaults to 100.

        Returns:
            [type]: ExecutionResult, GraphQL object that contains the result
                    in the "data" attribute.
        """

        # Retrieve the article IDs for the query
        article_ids = self._getArticleIds(query=query, max_results=max_results)

        # Get the articles themselves
        articles = list(
            [
                self._getArticles(article_ids=batch)
                for batch in batches(article_ids, 250)
            ]
        )

        # Chain the batches back together and return the list
        return itertools.chain.from_iterable(articles)
    
    def query_ids(self: object, id_string: str,):
        # ToDo Change Comments
    
        """Method that executes a query agains the GraphQL schema, automatically
           inserting the PubMed data loader.

        Args:
            query (str): String, the GraphQL query to execute against the schema.
            max_results (int, optional): max. Number of returned entries. Defaults to 100.

        Returns:
            [type]: ExecutionResult, GraphQL object that contains the result
                    in the "data" attribute.
        """

        # Retrieve the article IDs for the query
        article_ids = id_string.replace(' ', '').replace('\n', '').split(',')

        # Get the articles themselves
        articles = list(
            [
                self._getArticles(article_ids=batch)
                for batch in batches(article_ids, 250)
            ]
        )

        # Chain the batches back together and return the list
        return itertools.chain.from_iterable(articles)


    def _exceededRateLimit(self) -> bool:
        # ToDo: own Docstring 
        """ Helper method to check if we've exceeded the rate limit.
            Returns:
                - exceeded      Bool, Whether or not the rate limit is exceeded.
        """

        # Remove requests from the list that are longer than 1 second ago
        self._requestsMade = [requestTime for requestTime in self._requestsMade if requestTime > datetime.datetime.now() - datetime.timedelta(seconds=1)]

        # Return whether we've made more requests in the last second, than the rate limit
        return len(self._requestsMade) > self._rateLimit

    def _get(
        self: object, url: str, parameters: dict, output: str = "json"
    ) -> Union[dict, str]:
        # ToDo: own Docstring 
        """ Generic helper method that makes a request to PubMed.
            Parameters:
                - url           Str, last part of the URL that is requested (will
                                be combined with the base url)
                - parameters    Dict, parameters to use for the request
                - output        Str, type of output that is requested (defaults to
                                JSON but can be used to retrieve XML)
            Returns:
                - response      Dict / str, if the response is valid JSON it will
                                be parsed before returning, otherwise a string is
                                returend
        """

        # Make sure the rate limit is not exceeded
        while self._exceededRateLimit():
            pass

        # Set the response mode
        parameters["retmode"] = output

        # Make the request to PubMed
        response = requests.get(f"{BASE_URL}{url}", params=parameters)

        # Check for any errors
        response.raise_for_status()

        # Add this request to the list of requests made
        self._requestsMade.append(datetime.datetime.now())

        # Return the response
        if output == "json":
            return response.json()
        else:
            return response.text
    
    def _getArticles(self: object, article_ids: list) -> list:
        """ Helper method that batches a list of article IDs and retrieves the content.
            Parameters:
                - article_ids   List, article IDs.
            Returns:
                - articles      List, article objects.
        """

        # Get the default parameters
        parameters = self.parameters.copy()
        parameters["id"] = article_ids

        # Make the request
        response = self._get(
            url="/entrez/eutils/efetch.fcgi", parameters=parameters, output="xml"
        )

        # Parse as XML
        root = xml.fromstring(response)

        # Loop over the articles and construct article objects
        for article in root.iter("PubmedArticle"):
            yield PubMedArticle(xml_element=article)
        for book in root.iter("PubmedBookArticle"):
            yield PubMedBookArticle(xml_element=book)

    def _getArticleIds(self: object, query: str, max_results: int) -> list:
        # ToDo: own Docstring 
        """ Helper method to retrieve the article IDs for a query.
            Parameters:
                - query         Str, query to be executed against the PubMed database.
                - max_results   Int, the maximum number of results to retrieve.
            Returns:
                - article_ids   List, article IDs as a list.
        """

        # Create a placeholder for the retrieved IDs
        article_ids = []

        # Get the default parameters
        parameters = self.parameters.copy()

        # Add specific query parameters
        parameters["term"] = query
        parameters["retmax"] = 50000

        # Calculate a cut off point based on the max_results parameter
        if max_results < parameters["retmax"]:
            parameters["retmax"] = max_results

        # Make the first request to PubMed
        response = self._get(url="/entrez/eutils/esearch.fcgi", parameters=parameters)

        # Add the retrieved IDs to the list
        article_ids += response.get("esearchresult", {}).get("idlist", [])

        # Get information from the response
        total_result_count = int(response.get("esearchresult", {}).get("count"))
        retrieved_count = int(response.get("esearchresult", {}).get("retmax"))

        # If no max is provided (-1) we'll try to retrieve everything
        if max_results == -1:
            max_results = total_result_count

        # If not all articles are retrieved, continue to make requests untill we have everything
        while retrieved_count < total_result_count and retrieved_count < max_results:

            # Calculate a cut off point based on the max_results parameter
            if (max_results - retrieved_count) < parameters["retmax"]:
                parameters["retmax"] = max_results - retrieved_count

            # Start the collection from the number of already retrieved articles
            parameters["retstart"] = retrieved_count

            # Make a new request
            response = self._get(
                url="/entrez/eutils/esearch.fcgi", parameters=parameters
            )

            # Add the retrieved IDs to the list
            article_ids += response.get("esearchresult", {}).get("idlist", [])

            # Get information from the response
            retrieved_count += int(response.get("esearchresult", {}).get("retmax"))

        # Return the response
        return article_ids


# -------------------------------------------------------------
# article.py
# -------------------------------------------------------------

class PubMedArticle(object):
    """ Data class that contains a PubMed article.
    """

    __slots__ = (
        "pubmed_id",
        "title",
        "abstract",
        "keywords",
        "journal",
        "publication_date",
        "authors",
        "methods",
        "conclusions",
        "results",
        "copyrights",
        "doi",
        "xml",
    )

    def __init__(
        self: object,
        xml_element: Optional[TypeVar("Element")] = None,
        *args: list,
        **kwargs: dict,
    ) -> None:
        """ Initialization of the object from XML or from parameters.
        """

        # If an XML element is provided, use it for initialization
        if xml_element is not None:
            self._initializeFromXML(xml_element=xml_element)

        # If no XML element was provided, try to parse the input parameters
        else:
            for field in self.__slots__:
                self.__setattr__(field, kwargs.get(field, None))

    def _extractPubMedId(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//ArticleId[@IdType='pubmed']"
        return getContent(element=xml_element, path=path)

    def _extractTitle(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//ArticleTitle"
        return getContent(element=xml_element, path=path)

    def _extractKeywords(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Keyword"
        return [
            keyword.text for keyword in xml_element.findall(path) if keyword is not None
        ]

    def _extractJournal(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Journal/Title"
        return getContent(element=xml_element, path=path)

    def _extractAbstract(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//AbstractText"
        return getContent(element=xml_element, path=path)

    def _extractConclusions(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//AbstractText[@Label='CONCLUSION']"
        return getContent(element=xml_element, path=path)

    def _extractMethods(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//AbstractText[@Label='METHOD']"
        return getContent(element=xml_element, path=path)

    def _extractResults(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//AbstractText[@Label='RESULTS']"
        return getContent(element=xml_element, path=path)

    def _extractCopyrights(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//CopyrightInformation"
        return getContent(element=xml_element, path=path)

    def _extractDoi(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//ArticleId[@IdType='doi']"
        return getContent(element=xml_element, path=path)

    def _extractPublicationDate(
        self: object, xml_element: TypeVar("Element")
    ) -> TypeVar("datetime.datetime"):
        # Get the publication date
        try:

            # Get the publication elements
            publication_date = xml_element.find(".//PubMedPubDate[@PubStatus='pubmed']")
            publication_year = int(getContent(publication_date, ".//Year", None))
            publication_month = int(getContent(publication_date, ".//Month", "1"))
            publication_day = int(getContent(publication_date, ".//Day", "1"))

            # Construct a datetime object from the info
            return datetime.date(
                year=publication_year, month=publication_month, day=publication_day
            )

        # Unable to parse the datetime
        except Exception as e:
            print(e)
            return None

    def _extractAuthors(self: object, xml_element: TypeVar("Element")) -> list:
        return [
            {
                "lastname": getContent(author, ".//LastName", None),
                "firstname": getContent(author, ".//ForeName", None),
                "initials": getContent(author, ".//Initials", None),
                "affiliation": getContent(author, ".//AffiliationInfo/Affiliation", None),
            }
            for author in xml_element.findall(".//Author")
        ]

    def _initializeFromXML(self: object, xml_element: TypeVar("Element")) -> None:
        """ Helper method that parses an XML element into an article object.
        """

        # Parse the different fields of the article
        self.pubmed_id = self._extractPubMedId(xml_element)
        self.title = self._extractTitle(xml_element)
        self.keywords = self._extractKeywords(xml_element)
        self.journal = self._extractJournal(xml_element)
        self.abstract = self._extractAbstract(xml_element)
        self.conclusions = self._extractConclusions(xml_element)
        self.methods = self._extractMethods(xml_element)
        self.results = self._extractResults(xml_element)
        self.copyrights = self._extractCopyrights(xml_element)
        self.doi = self._extractDoi(xml_element)
        self.publication_date = self._extractPublicationDate(xml_element)
        self.authors = self._extractAuthors(xml_element)
        self.xml = xml_element

    def toDict(self: object) -> dict:
        """ Helper method to convert the parsed information to a Python dict.
        """

        return {key: self.__getattribute__(key) for key in self.__slots__}

    def toJSON(self: object) -> str:
        """ Helper method for debugging, dumps the object as JSON string.
        """

        return json.dumps(
            {
                key: (value if not isinstance(value, (datetime.date, Element)) else str(value))
                for key, value in self.toDict().items()
            },
            sort_keys=True,
            indent=4,
        )


# -------------------------------------------------------------
# book.py
# -------------------------------------------------------------

class PubMedBookArticle(object):
    """ Data class that contains a PubMed article.
    """

    __slots__ = (
        "pubmed_id",
        "title",
        "abstract",
        "publication_date",
        "authors",
        "copyrights",
        "doi",
        "isbn",
        "language",
        "publication_type",
        "sections",
        "publisher",
        "publisher_location",
    )

    def __init__(
        self: object,
        xml_element: Optional[TypeVar("Element")] = None,
        *args: list,
        **kwargs: dict,
    ) -> None:
        """ Initialization of the object from XML or from parameters.
        """

        # If an XML element is provided, use it for initialization
        if xml_element is not None:
            self._initializeFromXML(xml_element=xml_element)

        # If no XML element was provided, try to parse the input parameters
        else:
            for field in self.__slots__:
                self.__setattr__(field, kwargs.get(field, None))

    def _extractPubMedId(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//ArticleId[@IdType='pubmed']"
        return getContent(element=xml_element, path=path)

    def _extractTitle(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//BookTitle"
        return getContent(element=xml_element, path=path)

    def _extractAbstract(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//AbstractText"
        return getContent(element=xml_element, path=path)

    def _extractCopyrights(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//CopyrightInformation"
        return getContent(element=xml_element, path=path)

    def _extractDoi(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//ArticleId[@IdType='doi']"
        return getContent(element=xml_element, path=path)

    def _extractIsbn(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Isbn"
        return getContent(element=xml_element, path=path)

    def _extractLanguage(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Language"
        return getContent(element=xml_element, path=path)

    def _extractPublicationType(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//PublicationType"
        return getContent(element=xml_element, path=path)

    def _extractPublicationDate(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//PubDate/Year"
        return getContent(element=xml_element, path=path)

    def _extractPublisher(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Publisher/PublisherName"
        return getContent(element=xml_element, path=path)

    def _extractPublisherLocation(self: object, xml_element: TypeVar("Element")) -> str:
        path = ".//Publisher/PublisherLocation"
        return getContent(element=xml_element, path=path)

    def _extractAuthors(self: object, xml_element: TypeVar("Element")) -> list:
        return [
            {
                "collective": getContent(author, path=".//CollectiveName"),
                "lastname": getContent(element=author, path=".//LastName"),
                "firstname": getContent(element=author, path=".//ForeName"),
                "initials": getContent(element=author, path=".//Initials"),
            }
            for author in xml_element.findall(".//Author")
        ]

    def _extractSections(self: object, xml_element: TypeVar("Element")) -> list:
        return [
            {
                "title": getContent(section, path=".//SectionTitle"),
                "chapter": getContent(element=section, path=".//LocationLabel"),
            }
            for section in xml_element.findall(".//Section")
        ]

    def _initializeFromXML(self: object, xml_element: TypeVar("Element")) -> None:
        """ Helper method that parses an XML element into an article object.
        """

        # Parse the different fields of the article
        self.pubmed_id = self._extractPubMedId(xml_element)
        self.title = self._extractTitle(xml_element)
        self.abstract = self._extractAbstract(xml_element)
        self.copyrights = self._extractCopyrights(xml_element)
        self.doi = self._extractDoi(xml_element)
        self.isbn = self._extractIsbn(xml_element)
        self.language = self._extractLanguage(xml_element)
        self.publication_date = self._extractPublicationDate(xml_element)
        self.authors = self._extractAuthors(xml_element)
        self.publication_type = self._extractPublicationType(xml_element)
        self.publisher = self._extractPublisher(xml_element)
        self.publisher_location = self._extractPublisherLocation(xml_element)
        self.sections = self._extractSections(xml_element)

    def toDict(self: object) -> dict:
        """ Helper method to convert the parsed information to a Python dict.
        """

        return {
            key: (self.__getattribute__(key) if hasattr(self, key) else None)
            for key in self.__slots__
        }

    def toJSON(self: object) -> str:
        """ Helper method for debugging, dumps the object as JSON string.
        """

        return json.dumps(
            {
                key: (value if not isinstance(value, datetime.date) else str(value))
                for key, value in self.toDict().items()
            },
            sort_keys=True,
            indent=4,
        )


# -------------------------------------------------------------
# helpers.py
# -------------------------------------------------------------

def batches(iterable: list, n: int = 1) -> list:
    """ Helper method that creates batches from an iterable.
        Parameters:
            - iterable      Iterable, the iterable to batch.
            - n             Int, the batch size.
        Returns:
            - batches       List, yields batches of n objects taken from the iterable.
    """

    # Get the length of the iterable
    length = len(iterable)

    # Start a loop over the iterable
    for index in range(0, length, n):

        # Create a new iterable by slicing the original
        yield iterable[index : min(index + n, length)]


def getContent(
    element: TypeVar("Element"), path: str, default: str = None, separator: str = "\n"
) -> str:
    """ Internal helper method that retrieves the text content of an
        XML element.
        Parameters:
            - element   Element, the XML element to parse.
            - path      Str, Nested path in the XML element.
            - default   Str, default value to return when no text is found.
        Returns:
            - text      Str, text in the XML node.
    """

    # Find the path in the element
    result = element.findall(path)

    # Return the default if there is no such element
    if result is None or len(result) == 0:
        return default

    # Extract the text and return it
    else:
        return separator.join([sub.text for sub in result if sub.text is not None])