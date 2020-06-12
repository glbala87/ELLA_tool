export function getInheritanceCodes(hgncId, genepanel) {
    const phenotypes = genepanel.phenotypes.filter((p) => p.gene.hgnc_id === hgncId)
    if (phenotypes) {
        const codes = phenotypes.map((ph) => ph.inheritance).filter((i) => i && i.length > 0) // remove empty
        const uniqueCodes = new Set(codes)
        return Array.from(uniqueCodes.values()).sort()
    } else {
        return []
    }
}

export function formatInheritance(hgncId, genepanel) {
    return getInheritanceCodes(hgncId, genepanel).join('/')
}

export function findGeneConfigOverride(hgncId, acmgConfig) {
    if (acmgConfig && acmgConfig.genes && hgncId in acmgConfig.genes) {
        return acmgConfig.genes[hgncId]
    } else {
        return {}
    }
}

/**
 * Returns the OMIM entry ID for the gene as found in the transcripts file,
 * @param  {String} geneSymbol Gene symbol
 * @return {String}            Entry ID like 113705
 */
export function getOmimEntryId(hgncId, genepanel) {
    const transcripts = genepanel.transcripts.filter((p) => p.gene.hgnc_id === hgncId)
    // all have the same gene and thus omim entry
    return transcripts && transcripts.length > 0 ? transcripts[0].gene.omim_entry_id : ''
}
