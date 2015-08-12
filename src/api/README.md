# REST API


## Usage

### Filtering

The API supports basic filtering using the `q` parameter. The filter data must be a JSON serialized string, specifying the fields and values to filter by. Filtering is only supported on the root of the document, not on nested fields. For example, you're not allowed to filter on `genotypes.allele.id: 123`.

All fields are ANDed together. OR is not yet supported.

**Example:**
```
/api/v1/references/?q={"id": [74341, 74342, 74343, 74344, 74345, 74346, 74347, 74348, 74349, 74350]}
```

### Embed

You can specify what fields to embed and/or include using the `embed` parameter.

To embed a model into the requested resource, you simply specify it. For nested documents, you can specify them using a `.` inbetween.

You can also specify what fields to include, both for the root document and for nested documents. To specify fields, list them with each field starting with `:`, like: `:id:name`.

If you want to both embed and specify fields to include on nested documents, you must do it separately.

**Example:**

Following query includes:

* id and identifier on sample (root).
* id and heterozygous on genotypes (child).
* whole documents of allele nested under genotypes, and annotation nested under allele.

```
api/v1/samples/BRCA_S2?embed=:id:identifier,genotypes:id:heterozygous,genotypes.allele.annotation"
```

### Pagination

You can paginate some resources using the `num_per_page` and `page` parameters.

Total number of pages are not yet returned, but will be added to the header later.

**Example:**
```
/api/v1/samples/?num_per_page=10&page=3
```


## Resources

TODO
