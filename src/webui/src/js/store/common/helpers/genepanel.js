function extractInheritance(obj) {
    if ('inheritance' in obj) {
        return obj.inheritance || ''
    }
}

export function getConfigInheritanceCodes(transcripts) {
    if (!transcripts) {
        return []
    }
    const codes = transcripts.map((tx) => extractInheritance(tx)).filter((i) => i && i.length > 0) // remove empty
    const uniqueCodes = new Set(codes)
    return Array.from(uniqueCodes.values()).sort()
}

export function getOtherInheritanceCodes(phenotypes) {
    if (!phenotypes) {
        return []
    }
    const codes = phenotypes.map((ph) => extractInheritance(ph)).filter((i) => i && i.length > 0) // remove empty
    const uniqueCodes = new Set(codes)
    return Array.from(uniqueCodes.values()).sort()
}

export function formatInheritance(phenotypes, transcripts) {
    var formattedInheritance = ''
    if (transcripts) {
        formattedInheritance = getConfigInheritanceCodes(transcripts).join('/')
    }
    if (!formattedInheritance && phenotypes) {
        formattedInheritance = getOtherInheritanceCodes(phenotypes).join('/')
        if (formattedInheritance) {
            formattedInheritance = formattedInheritance + '*'
        }
    }
    return formattedInheritance
}

export function formatPhenotypes(phenotypes, transcripts) {
    const formattedInheritance = formatInheritance(phenotypes, transcripts)
    const formattedPhenotypes = phenotypes
        .filter((p) => p.description)
        .map(
            (p) =>
                (p.inheritance &&
                formattedInheritance &&
                formattedInheritance.substring(formattedInheritance.length - 1) == '*'
                    ? '*'
                    : '') +
                p.description +
                '(' +
                (p.inheritance || '?') +
                ')'
        )
    return formattedPhenotypes
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
export function getOmimEntryId(hgncId, genes) {
    const transcripts = genes.filter((g) => g.hgnc_id === hgncId).transcripts
    // all these are transcripts of the same gene and have the same omim entry
    return transcripts && transcripts.length > 0 ? transcripts[0].gene.omim_entry_id : ''
}
