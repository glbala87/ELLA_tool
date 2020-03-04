#!/bin/bash -ue

echo "Downloading mappings between HGNC IDs and gene names to $1"

pushd $1

today=$(date +'%Y/%m/%d %H:%M')


# HGNC ID -> Approved HGNC symbol
APPROVED_SYMBOLS=$(tempfile)
curl --fail "https://www.genenames.org/cgi-bin/download/custom?col=gd_hgnc_id&col=gd_app_sym&status=Approved&hgnc_dbtag=on&order_by=gd_hgnc_id&format=text&submit=submit" \
    | awk -v FS="[\t, ]+" -v OFS="\t" 'NR>1 {split($1, hgnc_id, ":"); $1=hgnc_id[2]; {print $2"\t"$1"\t1"}}' > $APPROVED_SYMBOLS # Add 1 (approved) to last column

# HGNC ID -> Previously approved symbols
# There are duplicate entries (some symbols have been approved for multiple HGNC ids), remove these duplicates
PREVIOUS_SYMBOLS=$(tempfile)
DUPLICATED_PREVIOUS_SYMBOLS=$(tempfile)
UNIQUE_PREVIOUS_SYMBOLS=$(tempfile)
curl --fail "https://www.genenames.org/cgi-bin/download/custom?col=gd_hgnc_id&col=gd_prev_sym&status=Approved&status=Entry%20Withdrawn&hgnc_dbtag=on&order_by=gd_hgnc_id&format=text&submit=submit" \
    | awk -v FS="[\t, ]+" -v OFS="\t" 'NR>1 {split($1, hgnc_id, ":"); $1=hgnc_id[2]; for (i=2; i<=NF; i++) {if ($i != "") {print $i"\t"$1"\t0"}}}' | sort > $PREVIOUS_SYMBOLS # Add 0 (not approved) to last column

cut -f1 $PREVIOUS_SYMBOLS | sort -k1,1 | uniq -d > $DUPLICATED_PREVIOUS_SYMBOLS
grep -v -w -f $DUPLICATED_PREVIOUS_SYMBOLS $PREVIOUS_SYMBOLS > $UNIQUE_PREVIOUS_SYMBOLS

# Concatenate approved and previous symbols.
(echo -e "##Generated on ${today}\n#Symbol\tHGNC_id\tApproved" && cat $APPROVED_SYMBOLS $UNIQUE_PREVIOUS_SYMBOLS | sort -k1,1 -k3,3r) | gzip -f > hgnc_symbols_id.txt.gz


curl --fail "https://www.genenames.org/cgi-bin/download/custom?col=gd_hgnc_id&col=gd_pub_ensembl_id&col=gd_pub_eg_id&status=Approved&status=Entry%20Withdrawn&hgnc_dbtag=on&order_by=gd_app_sym_sort&format=text&submit=submit" \
    | grep -oP "(?<=HGNC:).*" | gzip -f > hgnc_ncbi_ensembl_geneids.txt.gz
