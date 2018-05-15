export default function filterAndFlattenGenepanel(source, flattenedDest, query) {
    return function filterAndFlattenGenepanel({ state }) {
        const genepanel = state.get(source)
        if (!genepanel) {
            return []
        }
        const filter = state.get(query)
        let filtered = {}
        if (filter && filter.length) {
            for (const [key, g] of Object.entries(genepanel.genes)) {
                // Filter either on gene name or on any transcript name
                const filteredTranscripts = g.transcripts.filter((t) =>
                    t.transcript_name.toLowerCase().includes(filter.toLowerCase())
                )
                if (g.hgnc_symbol.toLowerCase().includes(filter.toLowerCase())) {
                    if (filteredTranscripts.length) {
                        filtered[key] = Object.assign({}, g, { transcripts: filteredTranscripts })
                    } else {
                        // If not transcripts were matched, but we match the gene, include all
                        filtered[key] = Object.assign({}, g)
                    }
                } else {
                    if (filteredTranscripts.length) {
                        filtered[key] = Object.assign({}, g, { transcripts: filteredTranscripts })
                    }
                }
            }
        } else {
            filtered = genepanel.genes
        }

        // Create flattened list for UI
        const flattened = []
        for (const g of Object.values(filtered)) {
            const inheritance = Array.from(new Set(g.phenotypes.map((p) => p.inheritance))).join(
                ','
            )
            for (const t of g.transcripts) {
                flattened.push({
                    hgnc_id: g.hgnc_id,
                    hgnc_symbol: g.hgnc_symbol,
                    transcript_name: t.transcript_name,
                    inheritance: inheritance
                })
            }
        }
        flattened.sort(firstBy('hgnc_symbol').thenBy('transcript_name'))
        state.set(flattenedDest, flattened)
    }
}
