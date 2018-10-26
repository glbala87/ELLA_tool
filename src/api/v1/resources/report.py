import datetime
from flask import send_file
from io import BytesIO

from api.util.util import authenticate, logger
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
        filter_config_id = queries.get_default_filter_config_id(user.id).scalar()
        export_sanger_variants.export_variants(
            session,
            gp_keys,
            filter_config_id,
            excel_file_obj
        )
        excel_file_obj.seek(0)
        filename = 'non-started-analyses-variants-{}.xlsx'.format(
            datetime.datetime.now().strftime("%Y-%m-%d-%H_%M")
        )
        return send_file(
            excel_file_obj,
            as_attachment=True,
            attachment_filename=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            cache_timeout=-1
        )
