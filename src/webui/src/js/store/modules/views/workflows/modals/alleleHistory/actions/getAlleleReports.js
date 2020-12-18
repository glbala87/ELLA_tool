import thenBy from 'thenby'

export default function getAlleleReports({ props, http, path }) {
    const { alleleId } = props

    const params = {
        q: JSON.stringify({ allele_id: alleleId })
    }
    return http
        .get('allelereports/', params)
        .then((response) => {
            const result = response.result.sort(thenBy((a) => a.date_created, -1))
            return path.success({ result })
        })
        .catch((error) => {
            return path.error({ result: error })
        })
}
