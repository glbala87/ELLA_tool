#!/usr/bin/env python3

import http.client
import logging
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from contextlib import closing, contextmanager
from pathlib import Path
from typing import List, Optional

from .pubmed_parser import NewReference, PubMedParser

"""
This module can query the PubMed article database based on PubMed article IDs
trough the Entrez API
The references can be dumped to a file that can be imported into ELLA using the CLI.
"""
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


@contextmanager
def output(filename: Optional[Path]):
    try:
        if filename:
            f = filename.open("w")
        else:
            f = sys.stdout  # type: ignore
        yield f
    finally:
        f.close()


class PubMedFetcher:
    BASE_URL_ENTREZ = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    BASE_DB = "pubmed"
    MAX_QUERY = 200  # Entrez can process so many IDs per query
    MIN_TIME_BETWEEN_QUERY = 0.1  # To avoid Entrez blacklisting
    WAIT_TIME = 30  # When Entrez gives faulty string, wait some seconds

    def control_query_frequency(self, time_previous_query: float, wait_time: float = 0):
        """
        :param time_previous_query: Time of previous call to the function
        :param wait_time: Pause program wait_time seconds
        :return : Ensure that there are less than 3 queries per second
        """
        # When Entrez returns fawlty xml string, we manually request long pause
        if wait_time <= 0:
            time_diff = time.time() - time_previous_query
            if time_diff < self.MIN_TIME_BETWEEN_QUERY:
                wait_time = self.MIN_TIME_BETWEEN_QUERY - time_diff

        if wait_time > 0:
            log.info(f"Entrez may be blocking us. Waiting {wait_time}s")
            time.sleep(wait_time)

        return time.time()

    def query_entrez(self, pmid: List[str]):
        """
        :param pmid: One or more PubMed IDs
        :return : XML entries of PubMed database as string
        """

        if len(pmid) > self.MAX_QUERY:
            raise IndexError(
                f"Max number of pmids in query is {self.MAX_QUERY}, but received {len(pmid)}"
            )

        pmid_parsed = ",".join(pmid)
        q_url = f"{self.BASE_URL_ENTREZ}/efetch.fcgi?db={self.BASE_DB}&id={pmid_parsed}&retmode=xml"
        log.debug(f"Query {q_url}")

        try:
            with closing(urllib.request.urlopen(q_url)) as q:
                xml_raw = q.read()
        except IOError as e:
            raise IOError(f"Error while reading Entrez database {q_url}: {e}")

        return xml_raw

    def get_references_from_file(self, pmid_file: Path, outfile: Optional[Path] = None):
        """
        :param pmid_file: File with tab or line separated PubMed IDs
        :param outfile: Save references file (defaults to stdout)
        """
        pmids = pmid_file.read_text().split()

        return self.get_references(pmids, outfile)

    def get_references(self, pmids: List[str], outfile: Optional[Path]):
        """
        :param pmids: PubMed IDs (list of one or more pmids)
        :param outfile: Save references to file (default stdout)
        """

        # Ensure that only MAX_QUERY ids are included per query
        n_refs = len(pmids)
        n_queries, leftover = divmod(n_refs, self.MAX_QUERY)
        if leftover:
            n_queries += 1

        # Initialize time of previous query
        t_prev_query = time.time()
        time.sleep(self.MIN_TIME_BETWEEN_QUERY)

        with output(outfile) as out:
            for i_query in range(n_queries):
                log.info(f"Processing query number {i_query+1} of {n_queries}")
                # Query sub-set of all pmids
                pmid_start = i_query * self.MAX_QUERY
                pmid_end = min(pmid_start + self.MAX_QUERY, n_refs)
                pmid_selection = pmids[pmid_start:pmid_end]
                t_prev_query = self.control_query_frequency(t_prev_query)

                references: List[NewReference] = []
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
                    except http.client.IncompleteRead as e3:
                        # Entrez occationally has some problems with incomplete reads
                        # Try again
                        r_err = "Attempt %s: IncompleteRead from Entrez %s"
                        log.error(r_err % (count + 1, e3))
                        t_prev_query = self.control_query_frequency(
                            t_prev_query, wait_time=self.WAIT_TIME
                        )
                    else:
                        break

                for ref in references:
                    out.write(ref.json(indent=None, exclude_none=True) + "\n")

    def get_references_core(self, pmids: List[str]) -> List[NewReference]:
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
    input_file = Path(sys.argv[1])
    PubMedFetcher().get_references_from_file(input_file)
