import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from api.util.types import StrEnum

"""
This module parses an PubmedArticle XML tree and returns the reference as
a Python dictionary
"""


class NewReference(BaseModel):
    authors: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    abstract: Optional[str] = None
    pubmed_id: int
    published: bool = True
    year: Optional[int] = None


log = logging.getLogger(__name__)

NOT_IN_PUBMED = None
STYLE_TAG_RE = re.compile("</?[ibu]>")


class AuthorPatterns(StrEnum):
    AUTHOR = "./Author"
    LAST_NAME = "./LastName"
    INITIALS = "./Initials"
    COLLECTIVE_NAME = "./CollectiveName"


class PublisherPatterns(StrEnum):
    PUBLISHER_NAME = "PublisherName"
    PUBLISHER_LOCATION = "PublisherLocation"


class JournalPatterns(StrEnum):
    JOURNAL_ISO = "ISOAbbreviation"
    JOURNAL_TITLE = "Title"
    VOLUME = "JournalIssue/Volume"
    ISSUE = "JournalIssue/Issue"
    PAGES = "../Pagination/MedlinePgn"


XML_PATTERNS = Union[AuthorPatterns, PublisherPatterns, JournalPatterns]


class PubMedParser(object):
    def parse(self, data: str):
        if self.is_pubmed_xml(data):
            return self.from_xml_string(data)
        else:
            return self.from_medline(data)

    def is_pubmed_xml(self, data: str):
        try:
            ET.fromstring(data)
            return True
        except ET.ParseError:
            return False

    def from_xml_string(self, pubmed_xml: str):
        # Strip out basic formatting tags from xml
        pubmed_xml = re.sub(STYLE_TAG_RE, "", pubmed_xml)

        return self.parse_pubmed_article(ET.fromstring(pubmed_xml))

    def from_medline(self, medline_text: str) -> NewReference:
        # Regex pattern:
        # Identify all keys - values, like "TI - Some text here"
        # Text is word wrapped from PUBMED, so we need to match line breaks within
        # a value. For that we use a non-greedy match-all ([\s\S]*?).
        # The lookahead pattern (?=\n[A-Z]*\s*-|$) stop the match-all
        # at either the next key, or at the end of the whole data string.
        pattern = r"([A-Z]+)\s*-\s*([\s\S]*?)(?=\n[A-Z]*\s*-|$)"
        matches = re.findall(pattern, medline_text)
        pubmed_data: Dict[str, Any] = {}

        for key, value in matches:
            # Input is word wrapped, convert back to single-line.
            value = re.sub(r"\n\s*", "", value)
            # If multiple values, use list
            if key in pubmed_data:
                if isinstance(pubmed_data[key], list):
                    pubmed_data[key].append(value)
                else:
                    pubmed_data[key] = [pubmed_data[key], value]
            else:
                pubmed_data[key] = value

        reference_type = pubmed_data["PT"]

        reference = NewReference(pubmed_id=int(pubmed_data["PMID"]))

        authors = pubmed_data.get("AU")
        if authors is None:
            reference.authors = "N/A"
        elif len(authors) > 2:
            reference.authors = authors[0] + " et al."
        else:
            reference.authors = " & ".join(authors)

        reference.abstract = pubmed_data.get("AB", "")

        if not isinstance(reference_type, list):
            reference_type = [reference_type]

        reference_type = set(reference_type)
        if reference_type & set(
            [
                "Case Reports",
                "Congress",
                "Editorial",
                "Introductory Journal Article",
                "Journal Article",
                "Letter",
                "News",
                "Published Erratum",
                "Retraction of Publication",
            ]
        ):
            reference.title = pubmed_data["TI"]
            journal = pubmed_data.get("TA")
            if not journal:
                journal = pubmed_data["JT"]
            volume = pubmed_data.get("VI", "")
            issue = pubmed_data.get("IP", "")
            page = pubmed_data.get("PG", "")

            reference.journal = "{journal}: {volume}{issue}, {page}".format(
                journal=journal,
                volume=volume if volume else "",
                issue="({})".format(issue) if issue else "",
                page=page,
            )
        elif "Book Chapter" in reference_type:
            reference.title = pubmed_data["TI"]
            book_title: str = pubmed_data["BTI"]
            publisher: Optional[str] = pubmed_data.get("PB")
            reference.journal = book_title
            if publisher:
                reference.journal += f", {publisher}"
        elif "Book" in reference_type:
            reference.title = pubmed_data["BTI"]
            reference.journal = pubmed_data.get("PB", "")
        else:
            raise RuntimeError(f"Unknown reference type {reference_type}")

        if reference.journal:
            reference.journal = reference.journal.rstrip(":, ")
        year: str = pubmed_data["DP"]
        reference.year = int(year.split(" ", 1)[0])
        return reference

    def parse_pubmed_article(self, pubmed_article: ET.Element):
        """
        :param pubmed_article: An XML tree of the PubmedArticle
                               or PubmedBookArticle class
        """
        if pubmed_article.tag == "PubmedArticle":
            base_tree = "./MedlineCitation/Article/%s"
            base_tree_year = base_tree % "Journal/JournalIssue/PubDate/%s"
            base_tree_abstract = base_tree
        elif pubmed_article.tag == "PubmedBookArticle":
            base_tree = "./BookDocument/Book/%s"
            base_tree_year = base_tree % "PubDate/%s"
            base_tree_abstract = base_tree % "../%s"
        else:
            raise RuntimeError("Unknown Pubmed tag: %s" % pubmed_article.tag)

        # Get field: pubmed_id
        pmid = int(self.get_field(pubmed_article, base_tree % "../PMID"))
        log.debug(f"Processing {pmid}")

        # Get field: year
        try:
            year = self.get_field(pubmed_article, base_tree_year % "Year")
        except AttributeError:
            year = self.get_field(pubmed_article, base_tree_year % "MedlineDate")
            log.debug("Set MedlineDate as year: %s" % year)

        # Get field: title
        if pubmed_article.tag == "PubmedArticle":
            title = self.get_field(pubmed_article, base_tree % "ArticleTitle")
        else:
            title_book = self.get_field(pubmed_article, base_tree % "BookTitle")
            # Determine if title is the title of article in book or book_title:
            try:
                title = self.get_field(pubmed_article, base_tree % "../ArticleTitle")
            except AttributeError:
                title = title_book
                title_book = None

        # Get field: authors
        author_list = pubmed_article.find(base_tree % "AuthorList")
        authors = self.format_authors(author_list)

        # For books: Allow for fact that authors may turn out to be editors
        if pubmed_article.tag == "PubmedBookArticle":
            editors = None
            if author_list is not None and author_list.attrib["Type"] == "editors":
                editors = authors
                # Finding the actual authors:
                author_list = pubmed_article.find(base_tree % "../AuthorList")
                authors = self.format_authors(author_list)

        # Get field: journal
        if pubmed_article.tag == "PubmedArticle":
            base_tree_journal = base_tree % "Journal/%s"
            journal = self.format_journal(pubmed_article, base_tree_journal)
        else:
            base_tree_publisher = base_tree % "Publisher/%s"
            book_info = {"title_book": title_book, "editors": editors}
            journal = self.format_book(pubmed_article, base_tree_publisher, **book_info)

        # Get field: abstract
        abstract_parts = pubmed_article.findall(base_tree_abstract % "Abstract/AbstractText")
        abstract = self.format_abstract(abstract_parts)

        reference = NewReference(
            pubmed_id=pmid,
            authors=authors,
            title=title,
            year=year,
            journal=journal,
            abstract=abstract,
        )
        return reference

    def get_field(self, pubmed_article: ET.Element, pattern: str):
        """
        :param pubmed_article: An XML tree of the PubmedArticle class
        :param pattern: XPath search string
        :return : PubmedArticle field
        """
        article_field = pubmed_article.find(pattern)

        if article_field is None or not getattr(article_field, "text", None):
            att_err = f"Field '{pattern}' was not found"
            log.debug(att_err)
            raise AttributeError(att_err)

        if article_field.text is None:
            err_str = f"Field '{pattern}' was NoneType but expected string"
            log.warning(err_str)
            raise TypeError(err_str)
        elif article_field.text == "":
            log.debug(f"Field '{pattern}' was empty string")

        return article_field.text

    def format_journal(self, pubmed_article: ET.Element, base_tree_journal: str):
        """
        :param pubmed_article: xml tree of PubmedArticle type
        :param base_tree_journal: path in xml tree to locate journal fields
        :param patterns: dict containing elements of a journal
        :return : formatted journal reference
        """

        try:
            title = self.get_field(pubmed_article, base_tree_journal % JournalPatterns.JOURNAL_ISO)
        except AttributeError:
            title = self.get_field(
                pubmed_article, base_tree_journal % JournalPatterns.JOURNAL_TITLE
            )

        journal_pattern = "{journal_title}: ".format(journal_title=title)

        try:
            volume = self.get_field(pubmed_article, base_tree_journal % JournalPatterns.VOLUME)
        except AttributeError:
            pass
        else:
            journal_pattern += "{volume}".format(volume=volume)

        try:
            issue = self.get_field(pubmed_article, base_tree_journal % JournalPatterns.ISSUE)
        except AttributeError:
            pass
        else:
            journal_pattern += "({issue})".format(issue=issue)

        try:
            pages = self.get_field(pubmed_article, base_tree_journal % JournalPatterns.PAGES)
        except (AttributeError, TypeError):
            journal_pattern += "."
            pass
        else:
            journal_pattern += ", {pages}.".format(pages=pages)

        return journal_pattern

    def format_book(
        self,
        pubmed_article: ET.Element,
        base_tree_publisher: str,
        editors: Optional[str] = None,
        title_book: Optional[str] = None,
    ):
        """
        :param pubmed_article: xml tree of PubmedArticle type
        :param base_tree_publisher: path in xml tree to locate publisher fields
        :param patterns: dict containing elements of a publisher
        :param editors: Formatted string of editors
        :param title_book: Book title of article collection
        :return : formatted book reference, same fields as article reference
        """
        # Determine if article is a book or in collection
        if any([editors, title_book]):
            book_pattern_start = "In: "
        else:
            book_pattern_start = ""

        book_pattern = []
        if editors:
            if " & " in editors or "et al" in editors:
                editor_pattern = "{editors} (eds)."
            else:
                editor_pattern = "{editors} (ed)."
            book_pattern += [editor_pattern.format(editors=editors)]
        if title_book:
            book_pattern += ["{title}".format(title=title_book)]

        # Get publisher name and location
        try:
            publisher_name = self.get_field(
                pubmed_article,
                base_tree_publisher % PublisherPatterns.PUBLISHER_NAME,
            )
        except AttributeError:
            pass
        else:
            book_pattern += ["{name}".format(name=publisher_name)]

        try:
            publisher_location = self.get_field(
                pubmed_article,
                base_tree_publisher % PublisherPatterns.PUBLISHER_LOCATION,
            )
        except AttributeError:
            pass
        else:
            book_pattern += ["{location}".format(location=publisher_location)]

        return book_pattern_start + ", ".join(book_pattern) + "."

    def format_abstract(self, abstract_parts: List[ET.Element]) -> Optional[str]:
        """
        :param abstract_parts: Abstract as list (e.g. Method, Result etc.)
        :return : Abstract formatted as one body UTF-8
        """
        abstract: str = ""
        for abstract_part in abstract_parts:
            if abstract_part is None:
                log.debug(f"Abstract part is NoneType: {abstract_parts!r}")
            elif getattr(abstract_part, "text", None) is None:
                log.debug(f"Abstract text is NoneType: {abstract_parts!r}")
            else:
                assert abstract_part.text
                abstract += abstract_part.text + "\n"

        if not abstract.strip():
            log.debug("Abstract text is empty")
            return NOT_IN_PUBMED

        return abstract.strip()

    def format_authors(self, author_list: Optional[ET.Element]) -> Optional[str]:
        """
        :param author_list: List of authors
        :param patterns: Patterns to search in author_list
        :return : Authors formatted as one string
        """
        if not author_list:
            log.warning("No authors found in XML")
            return NOT_IN_PUBMED

        try:
            authors = author_list.findall(AuthorPatterns.AUTHOR)
            n_authors = len(authors)
        except AttributeError as e:
            log.warning(f"No authors found: {e}")
            return NOT_IN_PUBMED

        authors_to_format = []
        for i_author, author in enumerate(authors, 1):
            try:
                name = self.get_field(author, AuthorPatterns.LAST_NAME)
            except AttributeError:
                log.debug("Author #%s is collective name" % (i_author + 1))
                name = self.get_field(author, AuthorPatterns.COLLECTIVE_NAME)

            author_formatted = "{last_name}".format(last_name=name)

            try:
                initials = self.get_field(author, AuthorPatterns.INITIALS)
                author_formatted += " {initials}".format(initials=initials)
            except AttributeError:
                log.debug("Author #%s has no initials" % (i_author + 1))

            authors_to_format.append(author_formatted)

        authors_formatted = " & ".join(authors_to_format)

        if n_authors > 2:
            authors_formatted += " et al."

        return authors_formatted
