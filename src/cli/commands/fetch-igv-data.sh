#!/bin/bash -ue


echo "Downloading IGV.js data to $1"

pushd $1 > /dev/null
echo "Downloading human_g1k_v37_decoy.fasta.gz"
curl -C - -O -# http://igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta.gz
echo "Downloading human_g1k_v37_decoy.fasta.fai.gz"
curl -O -# http://igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta.fai

echo "Downloading cytoBand.txt.gz"
curl -# -O hgdownload.cse.ucsc.edu/goldenpath/hg19/database/cytoBandIdeo.txt.gz


echo "Decompressing all files..."
gunzip *.gz

# Modify cytoband file
sed 's/chr//g' cytoBandIdeo.txt > cytoBand.txt

echo "All done!"

popd > /dev/null
