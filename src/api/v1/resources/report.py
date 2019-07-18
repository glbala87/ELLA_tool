import datetime
from flask import send_file
from io import BytesIO, StringIO
import lxml.etree
import lxml.html
from xmldiff import main, formatting

from api import ApiError
from api.util.util import authenticate, logger, request_json
from api.util import queries

from api.v1.resource import LogRequestResource
from vardb.export import export_sanger_variants


class NonStartedAnalysesVariants(LogRequestResource):
    @authenticate()
    @logger(hide_response=True)
    def get(self, session, user=None):
        """
        Returns a report of non-started analyses' variants in excel format.
        ---
        summary: Get nonstarted-analyses-variants report
        tags:
          - Report
        responses:
          200:
            description: Binary .xlsx file
        """

        excel_file_obj = BytesIO()
        gp_keys = [(g.name, g.version) for g in user.group.genepanels]

        filterconfigs = queries.get_valid_filter_configs(session, user.group_id)

        if filterconfigs.count() != 1:
            raise ApiError(
                "Unable to find single filter config appropriate for report filtering. Found {} filterconfigs.".format(
                    filterconfigs.count()
                )
            )

        filterconfig_id = filterconfigs.one().id
        export_sanger_variants.export_variants(session, gp_keys, filterconfig_id, excel_file_obj)
        excel_file_obj.seek(0)
        filename = "non-started-analyses-variants-{}.xlsx".format(
            datetime.datetime.now().strftime("%Y-%m-%d-%H_%M")
        )
        return send_file(
            excel_file_obj,
            as_attachment=True,
            attachment_filename=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            cache_timeout=-1,
        )


class Diff(LogRequestResource):
    @authenticate()
    @logger()
    @request_json(["old", "new"])
    def post(self, session, user=None, data=None):

        if not isinstance(data, list):
            wrapped_data = [data]
        else:
            wrapped_data = data

        diff_results = []
        for d in wrapped_data:
            # We need a single root element, so create a dummy <diff> element
            old = lxml.etree.tostring(lxml.html.fromstring(f'<diff>{d["old"]}</diff>'))
            new = lxml.etree.tostring(lxml.html.fromstring(f'<diff>{d["new"]}</diff>'))

            xml_formatter = formatting.XMLFormatter(
                text_tags=(
                    "p",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                    "li",
                    "font",
                    "span",
                    "div",
                    "img",
                ),
                formatting_tags=("b", "u", "i", "strike", "em", "super", "sup", "sub", "link", "a"),
                normalize=formatting.WS_BOTH,
            )
            result = main.diff_texts(old, new, formatter=xml_formatter)
            parsed_diff_xml = lxml.etree.parse(StringIO(result))
            namespaces = {"diff": "http://namespaces.shoobx.com/diff"}

            def process_elements_with_attribs(xpath_expr, diff_elem_name, remove_attrib_name):
                """
                Process elements with added diff attributes.

                Processes
                    <div diff:insert=""><span>Line 3</span><br/></div>
                Into
                    <div><ins><span >Line 3</span><br/></ins></div>

                """
                changed = parsed_diff_xml.xpath(xpath_expr, namespaces=namespaces)
                for c in changed:
                    new_elem = lxml.etree.Element(diff_elem_name)
                    # Remove the diff attribute
                    del c.attrib[remove_attrib_name]

                    # If elem as any content, we wrapt the content.
                    # e.g. <p>Something</p> -> <p><ins>Something</ins></p>
                    if c.text or list(c):
                        if c.text:
                            new_elem.text = c.text
                            c.text = None
                        new_elem.extend(list(c))
                        c.append(new_elem)
                    # If no content, wrap element itself.
                    # e.g. <img src=...> -> <ins><img src=...></ins>
                    else:
                        c.addprevious(new_elem)
                        new_elem.append(c)

            process_elements_with_attribs(
                "//*[@diff:insert]", "ins", f'{{{namespaces["diff"]}}}insert'
            )
            process_elements_with_attribs(
                "//*[@diff:delete]", "del", f'{{{namespaces["diff"]}}}delete'
            )

            def process_elements(xpath_expr, diff_elem_name):
                """
                Process pure diff elements, like <diff:insert> etc.

                Processes
                    <div>Line <diff:delete>2</diff:delete><diff:insert>4</diff:insert></div>
                Into
                    <div>Line <del>2</del><ins>4</ins></div>
                """
                changed = parsed_diff_xml.xpath(xpath_expr, namespaces=namespaces)
                for c in changed:
                    c.tag = diff_elem_name

            process_elements("//diff:insert", "ins")
            process_elements("//diff:delete", "del")

            diff_results.append({"result": lxml.etree.tostring(parsed_diff_xml).decode()})

        if isinstance(data, list):
            return diff_results
        else:
            assert len(diff_results) == 1
            return diff_results[0]
