import thenBy from 'thenby'

export default async function prepareIgv({ state, http }) {
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
        global: [
            {
                id: 'genepanel',
                selected: false,
                config: {
                    name: 'Genepanel',
                    type: 'annotation',
                    url: `/api/v1/igv/genepanel/${analysis.genepanel.name}/${
                        analysis.genepanel.version
                    }/`,
                    format: 'bed',
                    indexed: false,
                    displayMode: 'EXPANDED',
                    order: 10,
                    height: 60
                }
            },
            {
                id: 'classifications',
                selected: false,
                config: {
                    name: 'Classifications',
                    url: '/api/v1/igv/classifications/',
                    format: 'bed',
                    indexed: false,
                    order: 11,
                    visibilityWindow: Number.MAX_VALUE
                }
            }
        ],
        user: [],
        analysis: [
            {
                id: 'variants',
                selected: true,
                config: {
                    name: 'Variants',
                    url: `/api/v1/igv/variants/${analysis.id}/?allele_ids=${Object.keys(
                        alleles
                    ).join(',')}`,
                    format: 'vcf',
                    indexed: false,
                    order: 12,
                    visibilityWindow: Number.MAX_VALUE
                }
            }
        ]
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
