import json
from flask import request
from api import session


def schema(cls):
    def embed(func):
        def inner(*args, **kwargs):
            """
            A bit messy code. It converts embed=:id:identifier,genotypes:id:homozygous,genotypes.allele to:
            {'embed': {u'genotypes': {'embed': {u'allele': {'embed': {}}},
                          'fields': [u'id', u'homozygous']}},
            'fields': [u'id', u'identifier']}
            for use in EmbedSchema, which uses the structure to nest and include specified fields.
            """
            embed = {'embed': {}}  # Holds track of schemas to embed (nest) and fields to include
            relations = request.args.get('embed')
            if relations:
                relations = relations.split(',')
                for relation in relations:
                    r = relation.split('.')
                    current_level = embed
                    for part in r:
                        fields = None
                        if ':' in part:
                            p = part.split(':')
                            part = p[0]
                            fields = p[1:]
                        if part and part not in current_level['embed']:
                            current_level['embed'][part] = {
                                'embed': {}
                            }
                            if fields:
                                current_level['embed'][part]['fields'] = fields
                        else:
                            if part and fields:
                                current_level['embed'][part]['fields'] = current_level['embed'][part].get('fields', []) + fields
                            elif not part and fields:
                                current_level['fields'] = fields
                        if part:
                            current_level = current_level['embed'][part]

            schema = cls(embed=embed)

            return func(*args, schema=schema, **kwargs)
        return inner
    return embed


def error(msg, code):
    return {
        'error': msg,
        'status': code
    }, code


def rest_filter(func):

    def inner(*args, **kwargs):
        q = request.args.get('q')
        rest_filter = None
        if q:
            rest_filter = json.loads(q)
        return func(*args, rest_filter=rest_filter, **kwargs)

    return inner


def provide_session(func):
    def inner(*args, **kwargs):
        try:
            return func(session, *args, **kwargs)
        except Exception:
            session.rollback()
            session.remove()
            raise
        finally:
            session.remove()

    return inner


def paginate(func):

    def inner(*args, **kwargs):
        page = request.args.get('page')
        if page is None:
            page = 1
        else:
            page = int(page)
        num_per_page = request.args.get('num_per_page')
        if num_per_page is None:
            num_per_page = 20
        else:
            num_per_page = int(num_per_page)
        return func(*args, page=page, num_per_page=num_per_page, **kwargs)
    return inner
