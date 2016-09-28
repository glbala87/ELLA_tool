import urllib
from contextlib import closing
import xml.etree.ElementTree as ET
import logging
import json
import argparse
import time
import os.path as path
from pubmed_parser import PubMedParser

"""
This module can query the PubMed article database based on PubMed article IDs
trough the Entrez API
The references can be dumped to a '.json'-file that can be used by E||A
"""
log = logging.getLogger(__name__)


class PubMedFetcher(object):
    BASE_URL_ENTREZ = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    BASE_DB = "pubmed"
    MAX_QUERY = 200  # Entrez can process so many IDs per query
    MIN_TIME_BETWEEN_QUERY = 0.5  # To avoid Entrez blacklisting
    WAIT_TIME = 30  # When Entrez gives faulty string, wait some seconds

    def control_query_frequency(self, time_previous_query, wait_time=0):
        """
        :param time_previous_query: Time of previous call to the function
        :param wait_time: Pause program wait_time seconds
        :return : Ensure that there are less than 3 queries per second
        """
        # When Entrez returns fawlty xml string, we manually request long pause
        if wait_time > 0.0:
            print('Entrez may be blocking us. Waiting %d s' % wait_time)
            time.sleep(wait_time)

        # If last query to Entrez was less than MIN_TIME_BETWEEN_QUERY s ago
        time_diff = time.time() - time_previous_query
        if time_diff < self.MIN_TIME_BETWEEN_QUERY:
            postpone_query = self.MIN_TIME_BETWEEN_QUERY-time_diff
            print('Entrez may be blocking us. Waiting %d s' % postpone_query)
            time.sleep(postpone_query)

        return time.time()

    def query_entrez(self, pmid):
        """
        :param pmid: One or more PubMed IDs
        :return xml_raw: XML entries of PubMed database as string
        """
        url_pattern = "{base_url}efetch.fcgi?db={db}&id={pmid}&retmode=xml"

        if not hasattr(pmid, '__iter__'):  # If pmid is not a list
            pmid = [pmid]

        pmid = map(str, pmid)  # In case pmid are not strings

        pmid_parsed = ",".join(pmid)

        if pmid.__len__() > self.MAX_QUERY:
            raise IndexError('Max number of pmids in query is %d' %
                             self.MAX_QUERY)

        q_url = url_pattern.format(base_url=self.BASE_URL_ENTREZ,
                                   db=self.BASE_DB,
                                   pmid=pmid_parsed)
        log.debug("Query %s" % q_url)

        try:
            with closing(urllib.urlopen(q_url)) as q:
                xml_raw = q.read()
        except IOError as e:
            raise IOError('Error while reading Entrez database %s: %s' %
                          (q_url, e))

        return xml_raw

    def dump_references(self, references, json_file, replace_file=False):
        """
        :param references: list of reference dictionaries
        :param json_file: Filename on format '*.json'
        :param replace_file: write or append file
        'return : Each reference is printed after each other.
        """
        if replace_file:
            file_mode = 'w+'
        else:  # Add new references to file
            file_mode = 'a+'

        with open(json_file, file_mode) as f:
            for ref in references:
                json.dump(ref, f, indent=None)
                f.write('\n')

    def print_references(self, references):
        """
        :param references: list of reference dictionaries
        :return : Prints the references nicely to screen
        """
        print_pattern = u"\n{title}\n{authors}\n{journal}\n{year}\n{URL}"
        print_pattern_abstract = u"\n{abstract}"
        for ref in references:
            print(print_pattern.format(**ref))
            print(print_pattern_abstract.format(**ref))

    def import_pmids(self, pmid_filename):
        """
        :param pmid_filename: File with tab or line separated pmids
        """
        try:
            with open(pmid_filename, 'r') as f:
                pmids = f.read()
        except IOError as e:
            raise IOError("Error wile reading %s: %s" % (pmid_filename, e))

        return pmids.split()

    def get_references_from_file(self, pmid_file='pubmed_ids_all.txt',
                                 dump_json=False,
                                 replace_json=False,
                                 print_verbose=True,
                                 json_file='default_references.json',
                                 return_references=False):
        """
        :param pmid_file: File with tab or line separated PubMed IDs
        :param dump_json: Save references to file
        :param replace_json: Replace or append file current content
        :param print_verbose: Print references to screen
        :param json_file: Save references to '*.json' file
        :param return_references: Return list of refs
        :return : Return list of refs if return_references is 'True'
        """
        pmids = self.import_pmids(pmid_file)

        return self.get_references(pmid=pmids, dump_json=dump_json,
                                   replace_json=replace_json,
                                   print_verbose=print_verbose,
                                   json_file=json_file,
                                   return_references=return_references)

    def get_references(self, pmid=[],
                       dump_json=False,
                       replace_json=False,
                       print_verbose=True,
                       json_file='default_references.json',
                       return_references=False):
        """
        :param pmid: PubMed IDs (either one pmid or list of pmids)
        :param dump_json: Save references to file
        :param replace_json: Replace or append file current content
        :param print_verbose: Print references to screen
        :param json_file: Save references to '*.json' file
        :param return_references: Return list of refs
        :return : Return list of refs if return_references is 'True'
        """
        if not hasattr(pmid, '__iter__'):  # Ensure iterable pmid
            pmid = [pmid]

        n_refs = pmid.__len__()

        all_references = []  # Always return empty reference list

        # Ensure that only MAX_QUERY ids are included per query
        max_query = self.MAX_QUERY
        n_partial_queries = int(n_refs % max_query > 0)
        n_queries = n_refs / max_query + n_partial_queries

        # Initialize time of previous query
        t_prev_query = time.time()
        time.sleep(self.MIN_TIME_BETWEEN_QUERY)

        for i_query in range(n_queries):
            print('Processing query number %s of %s' % (i_query+1, n_queries))
            # Query sub-set of all pmids
            pmid_range = range(max_query*i_query,
                               min(max_query*(i_query+1), n_refs))

            pmid_selection = [pmid[i_sel] for i_sel in pmid_range]
            t_prev_query = self.control_query_frequency(t_prev_query)

            for count in range(10):
                try:
                    references = self.get_references_core(pmid_selection)
                except RuntimeError as e1:
                    # Entrez occationally returns unparsable string
                    # due to too many queries. Wait, and try again
                    r_err = "Attempt %s: Bad string from Entrez %s"
                    log.error(r_err % (count+1, e1))
                    t_prev_query = self.control_query_frequency(t_prev_query,
                                                                wait_time=self.WAIT_TIME)
                else:
                    break

            if dump_json:
                self.dump_references(references, json_file,
                                     replace_file=replace_json)
                replace_json = False  # Ensure new refs are appended
            if print_verbose:
                self.print_references(references)
            if return_references:
                all_references.append(references)

        # if return_references is 'True', otherwise empty
        return all_references

    def get_references_core(self, pmid):
        """
        :param pmid: Pubmed IDs (Either one or a list)
        :return references: List of reference dictionaries
        """
        try:
            xml_raw = self.query_entrez(pmid)
        except IOError as e:
            raise IOError(e)

        try:
            pubmed_article_set = ET.fromstring(xml_raw)
        except ET.ParseError as e:
            raise RuntimeError('ET cannot parse string from Entrez: %s' % e)

        # Log a warning for non-existing Pubmed entries
        self.check_for_non_existence_of_pmid(pubmed_article_set, pmid)

        references = []
        pmparser = PubMedParser()
        for pubmed_article in pubmed_article_set.findall("./PubmedArticle"):
            reference = pmparser.parse_pubmed_article(pubmed_article)
            references.append(reference)

        return references

    def check_for_non_existence_of_pmid(self, xml_tree, pmids):
        """
        :param xml_tree: xml tree structure on PubmedArticleSet format
        :param pmids: List of pmids that are supposed to be in xml_tree
        """
        if not hasattr(pmids, '__iter__'):
            pmids = [pmids]

        pmids = map(str, pmids)  # In case pmids are not strings

        xml_pmids = [xml_pmid.text for xml_pmid in
                     xml_tree.findall("./PubmedArticle/MedlineCitation/PMID")]

        pmids_not_in_db = list(set(pmids)-set(xml_pmids))
        if len(pmids_not_in_db):
            w_msg = 'Pubmed IDs %s silently ignored.'
            log.warning(w_msg % ', '.join(pmids_not_in_db))


def main(sys_args):
    """
    :param sys_args: Command line arguments
    :return pm: instance of PubMedHandler
    :return references: list of references (currently empty)
    :return args: Namespace of parsed command line arguments
    """
    LOG_FILENAME = path.join(path.dirname(__file__), 'log/fetcher.log')
    logging.basicConfig(filename=LOG_FILENAME, filemode='w',
                        level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Get references for PubMed IDs")
    parser.add_argument('-i', '--pmid_file', type=str,
                        default=argparse.SUPPRESS,
                        help='file containing PubMed IDs')
    parser.add_argument('-o', '--json_file', type=str, nargs='?',
                        const='references.json',
                        default='references.json',
                        help='file to dump references')
    parser.add_argument('-p', '--pmid', type=str, nargs='*',
                        default=argparse.SUPPRESS,
                        help='PubMed IDs from command line')
    parser.add_argument('-v', '--print_verbose', action='store_true',
                        help='Prints references to screen [Default: False]')
    parser.add_argument('-d', '--dump_json', action='store_true',
                        help='Prints references to json file [Default: False]')
    parser.add_argument('-r', '--replace_json', action='store_true',
                        help='Replace .json file [Default: False]')
    args = parser.parse_args()

    logging.debug("Argparse arguments: %s" % vars(args))

    pm = PubMedFetcher()
    if hasattr(args, 'pmid_file'):
        references = pm.get_references_from_file(**vars(args))
    elif hasattr(args, 'pmid'):
        references = pm.get_references(**vars(args))
    else:
        references = []
    return (pm, references, args)

if __name__ == "__main__":
    import sys
    pm, references, args = main(sys.argv)
