from flask import send_file
from io import BytesIO

from api.util.util import authenticate, logger

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
            description: Binary .xls file
        """

        excel_file_obj = BytesIO()

        export_sanger_variants.export_variants(session, excel_file_obj=excel_file_obj)
        excel_file_obj.seek(0)
        return send_file(
            excel_file_obj,
            as_attachment=True,
            attachment_filename='non-started-analyses-variants.xls',
            mimetype='application/vnd.ms-excel'
        )
