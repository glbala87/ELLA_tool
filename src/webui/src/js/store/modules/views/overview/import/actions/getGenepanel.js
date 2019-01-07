export default function getGenepanel({ http, path, props }) {
    const { genepanelName, genepanelVersion } = props
    return http
        .get(`genepanels/${genepanelName}/${genepanelVersion}/`)
        .then((response) => {
            // Convert genepanel to using Object for faster lookups

            const mappedGenes = {}
            for (const gene of response.result.genes) {
                mappedGenes[gene.hgnc_id] = gene
            }
            response.result.genes = mappedGenes
            return path.success({ result: response.result })
        })
        .catch((error) => {
            console.log(error)
            return path.error(error)
        })
}
