import thenBy from 'thenby'

export default function getAlleleAssessments({ props, http, path }) {
    const { alleleId } = props

    // let q = JSON.stringify({
    //     allele_id: allele_id
    // })
    // let r = this.resource(`${this.base}/alleleassessments/?q=${encodeURIComponent(q)}`)
    // let alleleassessments = r.query(() => {
    //     resolve(alleleassessments.sort(thenBy((a) => a.date_created, -1)))
    // }, reject)
    const params = {
        q: JSON.stringify({ allele_id: alleleId })
    }
    return http
        .get('alleleassessments/', params)
        .then((response) => {
            const result = response.result.sort(thenBy((a) => a.date_created, -1))
            console.log(result)
            return path.success({ result })
        })
        .catch((error) => {
            console.error(error)
            return path.error({ result: response.result })
        })
}
