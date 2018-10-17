/**
 * Parses identifer like 12-1231-4435-A-G and fetches
 * the corresponding allele from backend as {result}
 */
function getAlleleByIdentifier({ http, path, props, state }) {
    let parts = props.alleleIdentifier.split('-')
    if (parts.length !== 4) {
        throw Error("Variant selector doesn't contain 4 items")
    }
    let [chromosome, vcf_pos, vcf_ref, vcf_alt] = parts
    let query = {
        chromosome,
        vcf_pos,
        vcf_ref,
        vcf_alt
    }

    return http
        .get(`alleles/`, {
            q: JSON.stringify(query)
        })
        .then((response) => {
            let alleles = response.result
            return path.success({ result: alleles[0] })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}

export default getAlleleByIdentifier
