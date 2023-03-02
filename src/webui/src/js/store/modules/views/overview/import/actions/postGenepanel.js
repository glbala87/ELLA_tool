export default function postGenepanel({ props, http, path }) {
    const { genepanel, usergroups } = props

    // Restructure to backend format
    const payload = {
        name: genepanel.name,
        version: genepanel.version,
        usergroups: usergroups
    }
    payload.genes = Object.values(genepanel.genes).map((g) => {
        return {
            hgnc_id: g.hgnc_id,
            transcripts: g.transcripts.map((t) => {
                return {
                    id: t.id
                }
            }),
            phenotypes: g.phenotypes.map((p) => {
                return {
                    id: p.id
                }
            }),
            inheritance: g.inheritance
        }
    })
    return http
        .post('genepanels/', payload)
        .then((response) => {
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.error(error)
            return path.error(error)
        })
}
