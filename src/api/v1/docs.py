import json

from api.v1.resource import Resource
from apispec import APISpec
from flask import Flask
from flask_restful import Api
from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema

title = "Ella API"
version = "1.0"
desc = """
#### **Use only with permission.**


## General concepts:

### Filtering:

Some list resources support basic filtering capabilities using the `q` query parameter.
You can supply a URI encoded JSON string containing the properties you want to filter.
Note that filtering on nested properties are not supported.

Examples:

```
q={"id":[1,3,5],"date_superceeded":null}
q={"classification":4}
```

### Pagination:

Some resources support pagination. In order to paginate a resource, you can add the following query parameters:

- `page=` - Which page number to return.
- `per_page=` - How many items to return per page. Max value is 50.

Pagination information is returned as part of the HTTP header. The following headers are added:

- `Total-Count` - Total number of items available. If a filter is given, it's after filter is applied.
- `Total-Pages` - Total number of pages available. This is equals to ceil(Total-Count / Per-Page).
- `Page` - The page number of the response.
- `Per-Page` - How many items are returned per page.

"""


class ApiV1Docs:
    def __init__(self, app: Flask, api: Api):
        self.app = app
        self.api = api
        self.specs = self._create_spec()

    def _create_spec(self):
        """
        Creates an APISpec spec object, with support for
        flask restful resources and marshmallow schemas.
        """
        spec = APISpec(
            title=title,
            version=version,
            info=dict(description=desc),
            plugins=["apispec.ext.marshmallow", "api.v1.apispec_restful"],
        )
        return spec

    def _attach_swagger_ui(self, swagger_base_url: str, api_url: str):
        swagger_ui = get_swaggerui_blueprint(swagger_base_url, api_url)
        self.app.register_blueprint(swagger_ui, url_prefix=swagger_base_url)

    def init_api_docs(self, docs_url: str, specs_url: str):
        self._attach_swagger_ui(docs_url, specs_url)

        # Create closure so the inner function can access the specs object
        # without it needing to be passed to it
        def serve_spec_closure():
            specs = self.specs

            def serve_spec():
                return json.dumps(specs.to_dict())

            return serve_spec

        self.app.add_url_rule(specs_url, "v1_spec", serve_spec_closure())

    def add_schema(self, schema_name: str, schema: Schema):
        """
        Adds Marshmallow schema to specs.
        """
        self.specs.definition(schema_name, schema=schema)

    def add_resource(self, path: str, resource: Resource):
        """
        Adds 'flask restful' resource to paths in spec.
        """
        self.specs.add_path(path, api=self.api, resource=resource)
