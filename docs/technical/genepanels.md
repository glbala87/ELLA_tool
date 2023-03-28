# Gene panels

Everything in ELLA revolves around gene panels, and they're an essential part of the configuration.
Note that a gene panel doesn't have to be a targeted panel in the traditional sense, but can include
all genes in the exome if desired.

For details on how gene panels suitable for ELLA should be made, see the [README](https://gitlab.com/alleles/genepanel-builder/-/blob/dev/README.md) in the separate repository [Genepanel builder](https://gitlab.com/alleles/genepanel-builder).

To add a new gene panel, run the following command:

```bash
ella-cli deposit genepanel --folder <path to gene panel directory>
```

See [Genepanel store](https://gitlab.com/alleles/genepanel-store) repository `src/vardb/testdata/clinicalGenePanels/` for examples of complete gene panels. 
