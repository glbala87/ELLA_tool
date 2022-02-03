function getTranscriptInheritanceCodes(hgncId, genepanel) {
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

function getPhenotypeInheritanceCodes(hgncId, genepanel) {
    if (!genepanel.phenotypes) {
        return []
    }
    const phenotypes = genepanel.phenotypes.filter((p) => p.gene.hgnc_id === hgncId)
    if (phenotypes) {
        const codes = phenotypes.map((ph) => ph.inheritance).filter((i) => i && i.length > 0) // remove empty
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
    // Gene panel inheritance is defined as collection of transcript inheritance.
    // If no transcript inheritance is given, then fall back to phenotype inheritance codes
    const transcriptInheritanceCodes = getTranscriptInheritanceCodes(hgncId, genepanel)
    if (transcriptInheritanceCodes.length) {
        return formatInheritance(transcriptInheritanceCodes)
    }

    const phenotypeInheritanceCodes = getPhenotypeInheritanceCodes(hgncId, genepanel)
    if (phenotypeInheritanceCodes.length) {
        return formatInheritance(phenotypeInheritanceCodes)
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
