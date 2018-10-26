function _filterCollectionByGene(collection, geneSymbol) {
    if (collection) {
        return collection.filter((entry) => entry.gene.hgnc_symbol == geneSymbol)
    } else {
        return null
    }
}

export function phenotypesBy(geneSymbol, genepanel) {
    return _filterCollectionByGene(genepanel.phenotypes, geneSymbol)
}

export function transcriptsBy(geneSymbol, genepanel) {
    return _filterCollectionByGene(genepanel.transcripts, geneSymbol)
}

export function getInheritanceCodes(geneSymbol, genepanel) {
    let phenotypes = phenotypesBy(geneSymbol, genepanel)
    if (phenotypes) {
        let codes = phenotypes.map((ph) => ph.inheritance).filter((i) => i && i.length > 0) // remove empty
        let uniqueCodes = new Set(codes)
        return Array.from(uniqueCodes.values())
            .sort()
            .join('/')
    } else {
        return ''
    }
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
export function getOmimEntryId(geneSymbol, genepanel) {
    let transcripts = transcriptsBy(geneSymbol, genepanel)
    // all have the same gene and thus omim entry
    return transcripts && transcripts.length > 0 ? transcripts[0].gene.omim_entry_id : ''
}

export function formatInheritance(genepanel, acmgConfig, geneSymbol, hgncId) {
    let config = findGeneConfigOverride(hgncId, acmgConfig)
    if (config && 'inheritance' in config) {
        return config['inheritance']
    }

    let phenotypes = phenotypesBy(geneSymbol, genepanel)
    if (phenotypes) {
        let codes = phenotypes.map((ph) => ph.inheritance).filter((i) => i && i.length > 0) // remove empty
        let uniqueCodes = new Set(codes)
        return Array.from(uniqueCodes.values())
            .sort()
            .join('/')
    } else {
        return ''
    }
}
