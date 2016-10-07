import logging

"""
This module parses an PubmedArticle XML tree and returns the reference as
a Python dictionary
"""

log = logging.getLogger(__name__)

NOT_IN_PUBMED = "NOT IN PUBMED"


class PubMedParser(object):

    def parse_pubmed_article(self, pubmed_article):
        """
        :param pubmed_article: An XML tree of the PubmedArticle class
        """

        base_tree = "./MedlineCitation/Article/%s"

        pmid = self.get_field(pubmed_article, base_tree % "../PMID")
        log.debug('Processing %s' % pmid)

        base_tree_year = base_tree % "Journal/JournalIssue/PubDate/%s"
        try:
            year = self.get_field(pubmed_article, base_tree_year % "Year")
        except AttributeError:
            year = self.get_field(pubmed_article,
                                  base_tree_year % "MedlineDate")

        title = self.get_field(pubmed_article, base_tree % "ArticleTitle")

        base_tree_journal = base_tree % "Journal/%s"
        journal_patterns = {'journal_iso': "ISOAbbreviation",
                            'journal_title': "Title",
                            'volume': "JournalIssue/Volume",
                            'issue': "JournalIssue/Issue",
                            'pages': "../Pagination/MedlinePgn"}
        journal = self.format_journal(pubmed_article,
                                      base_tree_journal, journal_patterns)

        author_patterns = {'author': "./Author",
                           'last_name': "./LastName",
                           'initials': "./Initials",
                           'collective_name': "./CollectiveName"}
        author_list = pubmed_article.find(base_tree % "AuthorList")
        authors = self.format_authors(author_list, author_patterns)

        abstract_parts = pubmed_article.findall(base_tree %
                                                "Abstract/AbstractText")
        abstract = self.format_abstract(abstract_parts)

        reference = {'pmid': pmid, 'authors': authors, 'title': title,
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

    def format_journal(self, pubmed_article, base_tree, patterns):
        """
        :param journal_parts: dict containing elements of a journal reference
        :return : formatted journal reference
        """

        try:
            title = self.get_field(pubmed_article,
                                   base_tree % patterns['journal_iso'])
        except AttributeError:
            title = self.get_field(pubmed_article,
                                   base_tree % patterns['journal_title'])

        journal_pattern = u"{journal_title}: ".format(journal_title=title)

        try:
            volume = self.get_field(pubmed_article,
                                    base_tree % patterns['volume'])
        except AttributeError:
            pass
        else:
            journal_pattern += u"{volume}".format(volume=volume)

        try:
            issue = self.get_field(pubmed_article,
                                   base_tree % patterns['issue'])
        except AttributeError:
            pass
        else:
            journal_pattern += u"({issue})".format(issue=issue)

        try:
            pages = self.get_field(pubmed_article,
                                   base_tree % patterns['pages'])
        except (AttributeError, TypeError):
            journal_pattern += u"."
            pass
        else:
            journal_pattern += u", {pages}.".format(pages=pages)

        return journal_pattern

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
