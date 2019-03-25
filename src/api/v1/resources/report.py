import datetime
from flask import send_file
from io import BytesIO

from api import ApiError
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
