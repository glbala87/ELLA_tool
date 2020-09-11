#!/usr/bin/env python

import urllib.request
from contextlib import closing, contextmanager
import xml.etree.ElementTree as ET
import logging
import json
import time
from .pubmed_parser import PubMedParser

"""
This module can query the PubMed article database based on PubMed article IDs
trough the Entrez API
The references can be dumped to a file that can be imported into ELLA using the CLI.
"""
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@contextmanager
def output(filename):
    try:
        if filename is not None:
            f = open(filename, "w")
        else:
            f = sys.stdout
        yield f
    finally:
        f.close()


class PubMedFetcher(object):
    BASE_URL_ENTREZ = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    BASE_DB = "pubmed"
    MAX_QUERY = 200  # Entrez can process so many IDs per query
    MIN_TIME_BETWEEN_QUERY = 0.1  # To avoid Entrez blacklisting
    WAIT_TIME = 30  # When Entrez gives faulty string, wait some seconds

    def control_query_frequency(self, time_previous_query, wait_time=0):
        """
        :param time_previous_query: Time of previous call to the function
        :param wait_time: Pause program wait_time seconds
        :return : Ensure that there are less than 3 queries per second
        """
        # When Entrez returns fawlty xml string, we manually request long pause
        if wait_time > 0.0:
            log.info(("Entrez may be blocking us. Waiting %d s" % wait_time))
            time.sleep(wait_time)

        # If last query to Entrez was less than MIN_TIME_BETWEEN_QUERY s ago
        time_diff = time.time() - time_previous_query
        if time_diff < self.MIN_TIME_BETWEEN_QUERY:
            postpone_query = self.MIN_TIME_BETWEEN_QUERY - time_diff
            log.info(("Entrez may be blocking us. Waiting %d s" % postpone_query))
            time.sleep(postpone_query)

        return time.time()

    def query_entrez(self, pmid):
        """
        :param pmid: One or more PubMed IDs
        :return : XML entries of PubMed database as string
        """
        url_pattern = "{base_url}efetch.fcgi?db={db}&id={pmid}&retmode=xml"

        if not hasattr(pmid, "__iter__"):  # If pmid is not a list
            pmid = [pmid]

        pmid = list(map(str, pmid))  # In case pmid are not strings

        pmid_parsed = ",".join(pmid)

        if pmid.__len__() > self.MAX_QUERY:
            raise IndexError("Max number of pmids in query is %d" % self.MAX_QUERY)

        q_url = url_pattern.format(base_url=self.BASE_URL_ENTREZ, db=self.BASE_DB, pmid=pmid_parsed)
        log.debug("Query %s" % q_url)

        try:
            with closing(urllib.request.urlopen(q_url)) as q:
                xml_raw = q.read()
        except IOError as e:
            raise IOError("Error while reading Entrez database %s: %s" % (q_url, e))

        return xml_raw

    def import_pmids(self, pmid_filename):
        """
        :param pmid_filename: File with tab or line separated pmids
        """
        try:
            with open(pmid_filename, "r") as f:
                pmids = f.read()
        except IOError as e:
            raise IOError("Error wile reading %s: %s" % (pmid_filename, e))

        return pmids.split()

    def get_references_from_file(self, pmid_file, outfile=None):
        """
        :param pmid_file: File with tab or line separated PubMed IDs
        :param outfile: Save references file (defaults to stdout)
        """

        pmids = self.import_pmids(pmid_file)

        return self.get_references(pmids, outfile)

    def get_references(self, pmids, outfile=None):
        """
        :param pmids: PubMed IDs (either one pmid or list of pmids)
        :param outfile: Save references to file (default stdout)
        """

        assert isinstance(pmids, list)

        n_refs = len(pmids)

        # Ensure that only MAX_QUERY ids are included per query
        max_query = self.MAX_QUERY
        n_partial_queries = int(n_refs % max_query > 0)
        n_queries = n_refs // max_query + n_partial_queries

        # Initialize time of previous query
        t_prev_query = time.time()
        time.sleep(self.MIN_TIME_BETWEEN_QUERY)

        with output(outfile) as out:
            for i_query in range(n_queries):
                log.info(("Processing query number %s of %s" % (i_query + 1, n_queries)))
                # Query sub-set of all pmids
                pmid_range = list(
                    range(max_query * i_query, min(max_query * (i_query + 1), n_refs))
                )

                pmid_selection = [pmids[i_sel] for i_sel in pmid_range]
                t_prev_query = self.control_query_frequency(t_prev_query)

                for count in range(10):
                    try:
                        references = self.get_references_core(pmid_selection)
                    except RuntimeError as e1:
                        # Entrez occationally returns unparsable string
                        # due to too many queries. Wait, and try again
                        r_err = "Attempt %s: Bad string from Entrez %s"
                        log.error(r_err % (count + 1, e1))
                        t_prev_query = self.control_query_frequency(
                            t_prev_query, wait_time=self.WAIT_TIME
                        )
                    except IOError as e2:
                        # Entrez occationally has some problems with SSL
                        # Try again
                        r_err = "Attempt %s: IOError from Entrez %s"
                        log.error(r_err % (count + 1, e2))
                        t_prev_query = self.control_query_frequency(
                            t_prev_query, wait_time=self.WAIT_TIME
                        )
                    else:
                        break
                for ref in references:
                    json.dump(ref, out, indent=None)
                    out.write("\n")

    def get_references_core(self, pmids):
        """
        :param pmids: Pubmed IDs (Either one or a list)
        :return : List of references as dictionaries
        """
        try:
            xml_raw = self.query_entrez(pmids)
        except IOError as e:
            raise IOError(e)

        try:
            pubmed_article_set = ET.fromstring(xml_raw)
        except ET.ParseError as e:
            raise RuntimeError("ET cannot parse string from Entrez: %s" % e)

        # Log a warning for non-existing Pubmed entries
        self.check_for_non_existence_of_pmids(pubmed_article_set, pmids)

        references = []
        pmparser = PubMedParser()
        for pubmed_article in pubmed_article_set.findall("./*"):
            pubmed_xml = ET.tostring(pubmed_article).decode()
            reference = pmparser.from_xml_string(pubmed_xml)
            references.append(reference)

        return references

    def check_for_non_existence_of_pmids(self, xml_tree, pmids):
        """
        :param xml_tree: xml tree structure on PubmedArticleSet format
        :param pmids: List of pmids that are supposed to be in xml_tree
        """
        pmids = list(map(str, pmids))  # In case pmids are not strings

        xml_pmids = [xml_pmid.text for xml_pmid in xml_tree.findall(".//PMID")]

        pmids_not_in_db = list(set(pmids) - set(xml_pmids))
        if len(pmids_not_in_db):
            log.warning(f"Pubmed IDs ignored: {pmids_not_in_db}")


if __name__ == "__main__":
    import sys

    PubMedFetcher().get_references_from_file(sys.argv[1])
