

from flask import request
from sqlalchemy.orm import joinedload, contains_eager
from flask.ext.restful import Resource as flask_resource
from vardb.datamodel import sample, genotype, assessment, allele, user, gene, annotation

from api import schemas, config, ApiError
from api.util.util import provide_session, paginate, rest_filter, request_json

from api.v1.resource import Resource


class SearchResource(Resource):

    def get(self, session):
        query = request.args.get('q')
        if not query:
            return {}


