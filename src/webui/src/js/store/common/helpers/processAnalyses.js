export default function processAnalyses(analyses) {
    for (let analysis of analyses) {
        analysis.links = getLinks(analysis)
    }
}

function getLinks(analysis) {
    let links = {}
    links.workflow = `/workflows/analyses/${analysis.id}/`

    return links
}
