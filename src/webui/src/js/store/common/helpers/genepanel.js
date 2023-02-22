function getInheritanceCodes(hgncId, genepanel) {
    if (!genepanel.transcripts) {
        return []
    }
    const transcripts = genepanel.transcripts.filter((tx) => tx.gene.hgnc_id == hgncId)
    if (transcripts) {
        const codes = transcripts.map((tx) => tx.inheritance).filter(Boolean)
        const uniqueCodes = new Set(codes)
        return Array.from(uniqueCodes.values()).sort()
    } else {
        return []
    }
}

function formatInheritance(inheritanceCodes) {
    return inheritanceCodes.join('/')
}

export function formatGenepanelInheritance(hgncId, genepanel) {
    // Gene panel inheritance is defined as collection of transcript inheritance modes.
    const transcriptInheritanceCodes = getInheritanceCodes(hgncId, genepanel)
    if (transcriptInheritanceCodes.length) {
        return formatInheritance(transcriptInheritanceCodes)
    }

    return ''
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
