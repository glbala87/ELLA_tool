#!/bin/bash -ue


echo "Downloading IGV.js data to $1"

pushd $1 > /dev/null
echo "Downloading human_g1k_v37_decoy.fasta.gz"
curl -C - -O -# http://igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta.gz
echo "Downloading human_g1k_v37_decoy.fasta.fai.gz"
curl -O -# http://igv.broadinstitute.org/genomes/seq/1kg_v37/human_g1k_v37_decoy.fasta.fai

echo "Downloading gencode.v18.collapsed.bed"
curl -# -O igv.broadinstitute.org/annotations/hg19/genes/gencode.v18.collapsed.bed
echo "Downloading gencode.v18.collapsed.bed.idx"
curl -# -O igv.broadinstitute.org/annotations/hg19/genes/gencode.v18.collapsed.bed.idx

echo "Downloading cytoBand.txt.gz"
curl -# -O hgdownload.cse.ucsc.edu/goldenpath/hg19/database/cytoBandIdeo.txt.gz


echo "Decompressing all files..."
gunzip *.gz

# Modify .fai file
# awk -F'\t' -v OFS='\t' '{gsub(" .*", "" , $1); print }' human_g1k_v37_decoy.fasta.fai > tmp.fai
# mv tmp.fai human_g1k_v37_decoy.fasta.fai

# Modify cytoband file
sed 's/chr//g' cytoBandIdeo.txt > cytoBand.txt

echo "All done!"

popd > /dev/null