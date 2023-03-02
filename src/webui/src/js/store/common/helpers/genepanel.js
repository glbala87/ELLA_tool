export function findGeneConfigOverride(hgncId, acmgConfig) {
    if (acmgConfig && acmgConfig.genes && hgncId in acmgConfig.genes) {
        return acmgConfig.genes[hgncId]
    } else {
        return {}
    }
}

