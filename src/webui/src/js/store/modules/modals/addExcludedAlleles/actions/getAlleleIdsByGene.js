export default function getAlleleIdsByGene({ http, path, props }) {
    const alleleIds = props.alleleIds

    if (!alleleIds.length) {
        return path.success({ result: [] })
    }

    return http
        .get(`alleles/by-gene/?allele_ids=${alleleIds.join(',')}`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
