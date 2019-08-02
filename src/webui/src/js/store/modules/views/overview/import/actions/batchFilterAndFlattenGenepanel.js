import thenBy from 'thenby'

export default function batchFilterAndFlattenGenepanel({ state }) {
    const genepanel = state.get('views.overview.import.data.genepanel')
    const filter = state.get('views.overview.import.custom.candidates.filterBatch')
    if (!genepanel) {
        return
    }

    // First split filter on separators (space/linebreak, comma and semicolon)

    let filtered = {}
    const missing = []
    if (filter && filter.length) {
        const splittedFilter = filter
            .split(/[\s,;]+/)
            .map((s) => s.replace(/\s/g, ''))
            .filter((s) => s.length > 0)

        for (const toFind of splittedFilter) {
            let found = false
            for (const [key, g] of Object.entries(genepanel.genes)) {
                // Filter either on gene name or hgnc id
                // Don't use parseInt(), as a (hypothetical) gene name
                // starting with a number would match an id
                // (e.g. 2GENE would match hgnc id 2)
                if (
                    toFind.toLowerCase() === g.hgnc_symbol.toLowerCase() ||
                    Number(toFind) === g.hgnc_id
                ) {
                    filtered[key] = Object.assign({}, g)
                    found = true
                }
                if (found) {
                    break
                }
            }
            if (!found) {
                missing.push(toFind)
            }
        }
    } else {
        filtered = genepanel.genes
    }

    // Create flattened list for UI
    const flattened = []
    for (const g of Object.values(filtered)) {
        const inheritance = Array.from(new Set(g.phenotypes.map((p) => p.inheritance))).join(',')
        for (const t of g.transcripts) {
            flattened.push({
                hgnc_id: g.hgnc_id,
                hgnc_symbol: g.hgnc_symbol,
                transcript_name: t.transcript_name,
                inheritance: inheritance
            })
        }
    }
    flattened.sort(thenBy('hgnc_symbol').thenBy('transcript_name'))

    state.set('views.overview.import.custom.candidates.missingBatch', missing)
    state.set('views.overview.import.custom.candidates.filterBatch', missing.join('\n'))
    state.set('views.overview.import.custom.candidates.filteredFlattened', flattened)
    state.set('views.overview.import.custom.candidates.filterBatchProcessed', true)
}
