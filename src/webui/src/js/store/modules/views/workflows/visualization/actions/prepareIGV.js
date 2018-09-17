import thenBy from 'thenby'

const getAvailableTracks = (analysis, alleles) => {
    let tracks = []

    tracks.push({
        id: 'genepanel',
        name: 'Genepanel',
        type: 'annotation',
        url: `/api/v1/igv/genepanel/${analysis.genepanel.name}/${analysis.genepanel.version}/`,
        format: 'bed',
        indexed: false,
        displayMode: 'EXPANDED',
        order: 10,
        show: false,
        height: 60
    })

    tracks.push({
        id: 'variants',
        name: 'Variants',
        url: `/api/v1/igv/variants/${analysis.id}/?allele_ids=${Object.keys(alleles).join(',')}`,
        format: 'vcf',
        indexed: false,
        order: 11,
        show: true,
        visibilityWindow: Number.MAX_VALUE
    })

    return tracks
}

export default async function prepareIGV({ state, http }) {
    const igvReferenceConfig = state.get('app.config.igv.reference')
    state.set('views.workflows.visualization.igv.reference', {
        id: 'hg19',
        fastaURL: igvReferenceConfig.fastaURL,
        cytobandURL: igvReferenceConfig.cytobandURL
    })

    const analysis = state.get('views.workflows.data.analysis')
    const alleles = state.get('views.workflows.data.alleles')

    const result = await http.get(`igv/tracks/${analysis.id}`)
    const tracks = {
        global: [],
        user: [],
        analysis: []
    }
    for (const t of getAvailableTracks(analysis, alleles)) {
        tracks.global.push({
            selected: 'show' in t ? t.show : true,
            id: t.id,
            config: t
        })
    }
    for (const [category, categoryTracks] of Object.entries(result.result)) {
        for (const track of categoryTracks) {
            tracks[category].push({
                id: track.id,
                selected: 'show' in track ? track.show : true,
                config: track
            })
        }
        tracks[category].sort(thenBy((t) => t.config.order || 99999))
    }
    state.set('views.workflows.visualization.tracks', tracks)
}
