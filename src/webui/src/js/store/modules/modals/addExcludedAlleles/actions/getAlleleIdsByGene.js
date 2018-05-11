export default function({ http, path, props }) {
    return http
        .get(`alleles/by-gene/?allele_ids=${props.alleleIds.join(',')}`)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
