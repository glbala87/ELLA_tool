# Copyright (c) 2015, Andrew Pashkin
# Modifications: Copyright (c) 2016, Svein Tore Koksrud Seljebotn
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of apispec_restful nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function
import re
import traceback
from textwrap import dedent

import yaml


def path_from_resource(spec, api, resource, **kwargs):
    """Extracts swagger spec from `resource` methods."""
    from apispec import Path
    assert resource is not None

    for endpoint, view in api.app.view_functions.iteritems():
        if getattr(view, 'view_class', None) == resource:
            break
    else:
        raise RuntimeError

    for rule in api.app.url_map.iter_rules():
        if rule.endpoint == endpoint:
            break
    else:
        raise RuntimeError

    path = re.sub(r'<(?:[^:<>]+:)?([^<>]+)>', r'{\1}', rule.rule)

    operations = {}
    for method in map(str.lower, resource.methods):
        docstring = getattr(resource, method.lower()).__doc__
        operations[method] = {}
        if docstring:
            if '---' in docstring:
                desc, doc = docstring.split('---', 1)
                desc = dedent(desc)
                doc = dedent(doc)
                operations[method]['description'] = desc
                try:
                    operations[method].update(yaml.load(doc))
                except Exception:
                    print("Error while parsing docstring for resource {}:".format(path))
                    traceback.print_exc()
            else:
                operations[method]['description'] = dedent(docstring)

    return Path(path=path, operations=operations)


def setup(spec):
    spec.register_path_helper(path_from_resource)
