import thenBy from 'thenby'

export default function getSortedAlleleAssessments({ http, path, props }) {
    const { alleleId } = props

    return http
        .get(`alleleassessments/`, { q: JSON.stringify({ allele_id: alleleId }) })
        .then((response) => {
            return path.success({ result: response.result.sort(thenBy('date_created', -1)) })
        })
        .catch((response) => {
            return path.error({ result: response.result })
        })
}
