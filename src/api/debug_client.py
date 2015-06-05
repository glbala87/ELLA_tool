import requests
import json

def url_add(url, params):
    p = list()
    for k, v in params.iteritems():
        p.append(str(k)+'='+str(v))
    url += '?' + '&'.join(p)
    return url


# url = "http://localhost:5000/api/v1/samples/BRCA_S2?embed=genotypes.allele"
# url = "http://localhost:5000/api/v1/samples/BRCA_S2?embed=genotypes.allele.annotation,genotypes.secondallele.annotation"
url = url_add("http://localhost:5000/api/v1/references/", {
    'page': 1,
    'num_per_page': 10,
    'embed': ':id:authors',
    'q': json.dumps({'id': [74341, 74342, 74343, 74344, 74345, 74346, 74347, 74348, 74349, 74350]})})
r = requests.get(url)
print url

print r.text

