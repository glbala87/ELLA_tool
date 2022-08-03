# Gene panels

::: warning NOTE
This documentation is a work in progress and may be incomplete.
:::

Everything in ELLA revolves around gene panels, and they're an essential part of the configuration.
Note that a gene panel doesn't have to be a targeted panel in the traditional sense, but can
include all genes in the exome if desired.

A gene panel includes, among other things, the following:

- A list of transcripts, with associated gene name/id and transcript + exon coordinates
- A list of phenotypes, with associated inheritance pattern

To add a new gene panel, run the following command:

```bash
ella-cli deposit genepanel --folder <path to gene panel directory>
```

Note that `<PanelName>_<version>.transcripts.csv` and `<PanelName>_<version>.phenotypes.csv` files are required.

- Examples are available in the testdata: [alleles/ella-testdata:testdata/clinicalGenePanels](https://gitlab.com/alleles/ella-testdata/-/tree/main/testdata/clinicalGenePanels)
- An authoritative collection of gene panels is also available: [alleles/genepanel-store](https://gitlab.com/alleles/genepanel-store)
