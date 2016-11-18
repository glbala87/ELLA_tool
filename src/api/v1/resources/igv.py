import os
import mimetypes
from flask import request, Response, send_file

from api import ApiError
from api.config import config

from vardb.datamodel import sample

from api.v1.resource import Resource


def get_range(request):

    range_header = request.headers.get('Range', None)

    if range_header is None:
        return None, None

    if ',' in range_header:
        raise RuntimeError("Multiple ranges not supported.")

    if range_header:
        range = range_header.split('bytes=', 1)[1].split('-', 1)

        start = int(range[0])
        if not range[1] == '':
            end = int(range[1])
        else:
            end = None
    elif 'start' in request.args:
        # Try GET params instead
        start = int(request.args.get('start'))
        end = int(request.args.get('end'))
    else:
        start = end = None
    return start, end


def get_partial_response(path, start, end):
    size = os.path.getsize(path)
    data = None
    with open(path, 'rb') as f:
        f.seek(start)
        if end:
            data = f.read(end - start + 1)
        else:
            data = f.read()

    print len(data)
    rv = Response(
        data,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True
    )
    if end:
        if end - start + 1 > size:
            end = size - start - 1
        rv.headers.add('Content-Length', '{0}'.format(end - start + 1, size))
        rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, end, size))
    else:
        rv.headers.add('Content-Length', '{0}'.format(size))
        rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(start, size - 1, size))
    return rv


class IgvResource(Resource):

    def get(self, session, filename):

        if 'IGV_DATA' not in os.environ:
            raise ApiError("Missing IGV data location (env: $IGV_DATA).")

        if filename not in config['igv']['valid_resource_files']:
            raise ApiError("File is not in list of permitted accessible files.")

        final_path = os.path.join(os.environ['IGV_DATA'], filename)

        start, end = get_range(request)
        if start is None:
            return send_file(final_path)
        else:
            return get_partial_response(final_path, start, end)


class BamResource(Resource):
    """
    We serve the file through python to have control
    over the access of the bam files.

    TODO: Add access control and logging when in place.
    """

    def get(self, session, analysis_id, sample_id):

        serve_bai = False
        if request.args.get('index'):
            serve_bai = True

        if 'ANALYSES_PATH' not in os.environ:
            raise ApiError("Missing env ANALYSES_PATH. Cannot serve BAM files.")

        # Get analysis and sample names
        analysis_name = session.query(sample.Analysis.name).filter(
            sample.Analysis.id == analysis_id
        ).scalar()

        sample_name = session.query(sample.Sample.identifier).filter(
            sample.Sample.id == sample_id
        ).scalar()

        if serve_bai:
            path = os.path.join(os.environ['ANALYSES_PATH'], analysis_name, sample_name + '.bai')
        else:
            path = os.path.join(os.environ['ANALYSES_PATH'], analysis_name, sample_name + '.bam')

        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)


class VcfResource(Resource):
    """
    We serve the file through python to have control
    over the access of the vcf files.

    TODO: Add access control and logging when in place.
    """

    def get(self, session, analysis_id):

        if 'ANALYSES_PATH' not in os.environ:
            raise ApiError("Missing env ANALYSES_PATH. Cannot serve BAM files.")

        serve_idx = False
        if request.args.get('index'):
            serve_idx = True

        # Get analysis and sample names
        analysis_name = session.query(sample.Analysis.name).filter(
            sample.Analysis.id == analysis_id
        ).scalar()

        if serve_idx:
            path = os.path.join(os.environ['ANALYSES_PATH'], analysis_name, analysis_name + '.vcf.idx')
        else:
            path = os.path.join(os.environ['ANALYSES_PATH'], analysis_name, analysis_name + '.vcf')

        start, end = get_range(request)

        if start is None:
            return send_file(path)
        else:
            return get_partial_response(path, start, end)
