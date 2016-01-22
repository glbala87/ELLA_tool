from vardb.datamodel import sample

from api import schemas
from api.util.util import paginate, rest_filter
from api.v1.resource import Resource


class AnalysisListResource(Resource):

    @paginate
    @rest_filter
    def get(self, session, rest_filter=None, page=None, num_per_page=None):
        return self.list_query(session, sample.Analysis, schemas.AnalysisSchema())
