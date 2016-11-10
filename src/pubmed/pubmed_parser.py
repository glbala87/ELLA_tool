import logging
import xml.etree.ElementTree as ET

"""
This module parses an PubmedArticle XML tree and returns the reference as
a Python dictionary
"""

log = logging.getLogger(__name__)

NOT_IN_PUBMED = "NOT IN PUBMED"


class PubMedParser(object):

    def from_xml_string(self, pubmed_xml):
        return self.parse_pubmed_article(ET.fromstring(pubmed_xml))

    def parse_pubmed_article(self, pubmed_article):
        """
        :param pubmed_article: An XML tree of the PubmedArticle
                               or PubmedBookArticle class
        """

        if pubmed_article.tag == 'PubmedArticle':
            base_tree = "./MedlineCitation/Article/%s"
            base_tree_year = base_tree % "Journal/JournalIssue/PubDate/%s"
            base_tree_abstract = base_tree
        elif pubmed_article.tag == 'PubmedBookArticle':
            base_tree = "./BookDocument/Book/%s"
            base_tree_year = base_tree % "PubDate/%s"
            base_tree_abstract = base_tree % "../%s"
        else:
            raise RuntimeError("Unknown Pubmed tag: %s" % pubmed_article.tag)

        # Get field: pubmed_id
        pmid = int(self.get_field(pubmed_article, base_tree % "../PMID"))
        log.debug('Processing %s' % str(pmid))

        # Get field: year
        try:
            year = self.get_field(pubmed_article, base_tree_year % "Year")
        except AttributeError:
            year = self.get_field(pubmed_article,
                                  base_tree_year % "MedlineDate")
            log.debug('Set MedlineDate as year: %s' % year)

        # Get field: title
        if pubmed_article.tag == 'PubmedArticle':
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
        author_patterns = {'author': "./Author",
                           'last_name': "./LastName",
                           'initials': "./Initials",
                           'collective_name': "./CollectiveName"}
        author_list = pubmed_article.find(base_tree % "AuthorList")
        authors = self.format_authors(author_list, author_patterns)

        # For books: Allow for fact that authors may turn out to be editors
        if pubmed_article.tag == 'PubmedBookArticle':
            editors = None
            if author_list is not None and author_list.attrib['Type'] == 'editors':
                editors = authors
                # Finding the actual authors:
                author_list = pubmed_article.find(base_tree % "../AuthorList")
                authors = self.format_authors(author_list, author_patterns)

        # Get field: journal
        if pubmed_article.tag == 'PubmedArticle':
            base_tree_journal = base_tree % "Journal/%s"
            journal_patterns = {'journal_iso': "ISOAbbreviation",
                                'journal_title': "Title",
                                'volume': "JournalIssue/Volume",
                                'issue': "JournalIssue/Issue",
                                'pages': "../Pagination/MedlinePgn"}
            journal = self.format_journal(pubmed_article,
                                          base_tree_journal, journal_patterns)
        else:
            base_tree_publisher = base_tree % "Publisher/%s"
            publisher_patterns = {'publisher_name': 'PublisherName',
                                  'publisher_location': 'PublisherLocation'}
            book_info = {'title_book': title_book,
                         'editors': editors}
            journal = self.format_book(pubmed_article, base_tree_publisher,
                                       publisher_patterns, **book_info)

        # Get field: abstract
        abstract_parts = pubmed_article.findall(base_tree_abstract %
                                                "Abstract/AbstractText")
        abstract = self.format_abstract(abstract_parts)

        reference = {'pubmed_id': pmid, 'authors': authors, 'title': title,
                     'year': year, 'journal': journal, 'abstract': abstract}
        return self.remove_empty_keys(reference)

    def remove_empty_keys(self, reference):
        """
        :param reference: An reference as a dictionary
        :return : reference with empty keys removed
        """
        for key, value in reference.items():
            if value == NOT_IN_PUBMED:
                reference.pop(key, None)
        return reference

    def get_field(self, pubmed_article, pattern):
        """
        :param pubmed_article: An XML tree of the PubmedArticle class
        :param pattern: XPath search string
        :return : PubmedArticle field
        """
        article_field = pubmed_article.find(pattern)

        try:
            field_value = article_field.text
        except AttributeError as e:
            att_err = 'Field %s was not found: %s' % (pattern, e)
            log.debug(att_err)
            raise AttributeError(att_err)

        try:
            if len(field_value) == 0:
                len_err = 'Field %s was empty string' % pattern
                log.warning(len_err)
        except TypeError as e:
            type_err = 'Field %s was NoneType: %s' % (pattern, e)
            log.debug(type_err)
            raise TypeError(type_err)

        return field_value

    def format_journal(self, pubmed_article, base_tree_journal, patterns):
        """
        :param pubmed_article: xml tree of PubmedArticle type
        :param base_tree_journal: path in xml tree to locate journal fields
        :param patterns: dict containing elements of a journal
        :return : formatted journal reference
        """

        try:
            title = self.get_field(pubmed_article,
                                   base_tree_journal % patterns['journal_iso'])
        except AttributeError:
            title = self.get_field(pubmed_article,
                                   base_tree_journal % patterns['journal_title'])

        journal_pattern = u"{journal_title}: ".format(journal_title=title)

        try:
            volume = self.get_field(pubmed_article,
                                    base_tree_journal % patterns['volume'])
        except AttributeError:
            pass
        else:
            journal_pattern += u"{volume}".format(volume=volume)

        try:
            issue = self.get_field(pubmed_article,
                                   base_tree_journal % patterns['issue'])
        except AttributeError:
            pass
        else:
            journal_pattern += u"({issue})".format(issue=issue)

        try:
            pages = self.get_field(pubmed_article,
                                   base_tree_journal % patterns['pages'])
        except (AttributeError, TypeError):
            journal_pattern += u"."
            pass
        else:
            journal_pattern += u", {pages}.".format(pages=pages)

        return journal_pattern

    def format_book(self, pubmed_article, base_tree_publisher,
                    patterns, editors=None, title_book=None):
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
            book_pattern_start = u"In: "
        else:
            book_pattern_start = u""

        book_pattern = []
        if editors:
            if ' & ' in editors or 'et al' in editors:
                editor_pattern = u"{editors} (eds)."
            else:
                editor_pattern = u"{editors} (ed)."
            book_pattern += [editor_pattern.format(editors=editors)]
        if title_book:
            book_pattern += [u"{title}".format(title=title_book)]

        # Get publisher name and location
        try:
            publisher_name = self.get_field(pubmed_article,
                                            base_tree_publisher % patterns['publisher_name'])
        except AttributeError:
            pass
        else:
            book_pattern += [u"{name}".format(name=publisher_name)]

        try:
            publisher_location = self.get_field(pubmed_article,
                                                base_tree_publisher % patterns['publisher_location'])
        except AttributeError:
            pass
        else:
            book_pattern += [u"{location}".format(location=publisher_location)]

        return book_pattern_start + ", ".join(book_pattern) + u"."

    def format_abstract(self, abstract_parts):
        """
        :param abstract_parts: Abstract as list (e.g. Method, Result etc.)
        :return : Abstract formatted as one body UTF-8
        """
        abstract = u""
        for abstract_part in abstract_parts:
            try:
                abstract += abstract_part.text + "\n"
            except TypeError as e:
                log.debug("Abstract text is NoneType: %s" % e)
            except AttributeError as e:
                log.debug("Abstract part is NoneType: %s" % e)

        if len(abstract) == 0:
            log.debug("Abstract text is empty")
            abstract = NOT_IN_PUBMED

        return abstract.strip()

    def format_authors(self, author_list, patterns):
        """
        :param author_list: List of authors
        :param patterns: Patterns to search in author_list
        :return : Authors formatted as one string
        """

        try:
            authors = iter(author_list.findall(patterns['author']))
            n_authors = authors.__length_hint__()
        except AttributeError as e:
            log.warning("No authors found: %s" % e)
            return NOT_IN_PUBMED

        n_authors_to_format = 1 + int(n_authors == 2)
        authors_to_format = []

        for i_author in range(n_authors_to_format):
            author = authors.next()

            try:
                name = self.get_field(author, patterns['last_name'])
            except AttributeError:
                log.debug('Author #%s is collective name' % (i_author+1))
                name = self.get_field(author, patterns['collective_name'])

            author_formatted = u"{last_name}".format(last_name=name)

            try:
                initials = self.get_field(author, patterns['initials'])
                author_formatted += u" {initials}".format(initials=initials)
            except AttributeError:
                log.debug('Author #%s has no initials' % (i_author+1))

            authors_to_format.append(author_formatted)

        authors_formatted = " & ".join(authors_to_format)

        if n_authors > 2:
            authors_formatted += u" et al."

        return authors_formatted
