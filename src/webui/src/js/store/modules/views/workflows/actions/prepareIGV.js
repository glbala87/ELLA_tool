const getAvailableTracks = (analysis, alleles) => {
    let tracks = []

    tracks.push({
        name: 'Gencode',
        url: 'api/v1/igv/gencode.v18.collapsed.bed',
        indexed: true,
        displayMode: 'EXPANDED'
    })

    tracks.push({
        name: 'Genepanel',
        type: 'annotation',
        url: `/api/v1/igv/genepanel/${analysis.genepanel.name}/${
            analysis.genepanel.version
        }/`,
        format: 'bed',
        indexed: false,
        displayMode: 'EXPANDED',
        height: 60
    })

    tracks.push({
        name: 'Variants',
        url: `/api/v1/igv/variants/${analysis.id}/${
            analysis.samples[0].id
        }/?q=${encodeURIComponent(
            JSON.stringify({ allele_ids: Object.keys(alleles) })
        )}`,
        format: 'vcf',
        indexed: false,
        visibilityWindow: Number.MAX_VALUE
    })

    return tracks
}

function prepareIGV({state, http}) {
    const igvReferenceConfig = state.get('app.config.igv.reference')
    state.set('views.workflows.igv.reference', {
        id: 'hg19',
        fastaURL: igvReferenceConfig.fastaURL,
        cytobandURL: igvReferenceConfig.cytobandURL
    })

    const analysis = state.get('views.workflows.data.analysis')
    const alleles = state.get('views.workflows.data.alleles')

    http.get(`igv/tracks/${analysis.id}`).then((response) => {
        let availableTracks = getAvailableTracks(analysis, alleles)
        for (let t of response.result) {
            availableTracks.push(t)
        }
        let tracks = []
        for (let trackConfig of availableTracks) {
            tracks.push({
                show: true,
                config: trackConfig
            })
        }

        state.set('views.workflows.igv.tracks', tracks)
    })

}
export default prepareIGV
