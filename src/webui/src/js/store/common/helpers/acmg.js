/* jshint esnext: true */
import thenBy from 'thenby'

export function sortCodeStrByTypeStrength(codes, config) {
    const result = {
        pathogenic: [],
        benign: []
    }
    for (let t of ['benign', 'pathogenic']) {
        // Map codes to group (benign/pathogenic)
        for (let c of codes) {
            if (config.acmg.codes[t].some((e) => c.startsWith(e))) {
                result[t].push(c)
            }
        }

        // Sort the codes
        result[t].sort((a, b) => {
            // Find the difference in index between the codes
            let aIdx = config.acmg.codes[t].findIndex((elem) => a.startsWith(elem))
            let bIdx = config.acmg.codes[t].findIndex((elem) => b.startsWith(elem))

            // If same prefix, sort on text itself
            if (aIdx === bIdx) {
                return a.localeCompare(b)
            }
            if (t === 'benign') {
                return bIdx - aIdx
            } else {
                return aIdx - bIdx
            }
        })
    }
    return result
}

export function sortCodesByTypeStrength(codes, config) {
    const codeStrs = codes.map((c) => c.code)
    const sortedStrs = sortCodeStrByTypeStrength(codeStrs, config)
    const sortedCodes = {
        pathogenic: [],
        benign: []
    }
    for (const category of ['pathogenic', 'benign']) {
        for (const c of codes) {
            if (sortedStrs[category].includes(c.code)) {
                sortedCodes[category].push(c)
            }
        }
    }
    for (const category of ['pathogenic', 'benign']) {
        sortedCodes[category].sort(thenBy((x) => sortedStrs[category].indexOf(x.code)))
    }

    return sortedCodes
}

export function containsCodeBase(codes, codeStrToCheck) {
    return codes.map((c) => getCodeBase(c.code)).includes(getCodeBase(codeStrToCheck))
}

export function getCodeBase(code) {
    if (code.includes('x')) {
        return code.split('x', 2)[1]
    }
    return code
}

export function extractCodeType(code) {
    let base = getCodeBase(code)
    if (base.startsWith('B')) {
        return 'benign'
    } else {
        return 'pathogenic'
    }
}

export function upgradeDowngradeCode(code, config, upgrade = true) {
    let codeStrength, base
    if (code.includes('x')) {
        ;[codeStrength, base] = code.split('x', 2)
    }

    // If code is benign, upgrading the code should mean 'more benign' and vice versa
    if (extractCodeType(code) === 'benign') {
        upgrade = !upgrade
    }

    for (let strengths of Object.values(config.acmg.codes)) {
        // If strength is given (i.e. the code is not already upgraded/downgraded)
        // we need to find the strength of the base.
        if (codeStrength === undefined) {
            base = code
            for (let s of strengths) {
                if (code.startsWith(s)) {
                    codeStrength = s
                }
            }
        }

        let strengthIdx = strengths.indexOf(codeStrength)
        if (strengthIdx < 0) {
            // If strength not part of set, try next one
            continue
        }

        // Check whether we can upgrade code, or if it would overflow
        let overflow = upgrade ? strengthIdx === 0 : strengthIdx >= strengths.length - 1
        if (!overflow) {
            let new_strength = upgrade ? strengths[strengthIdx - 1] : strengths[strengthIdx + 1]
            // If new strength is same as base we just return base
            if (base.startsWith(new_strength)) {
                return base
            }
            return `${new_strength}x${base}`
        }
        // If overflowing, return input
        return code
    }
    return code
}

export function getAcmgCandidates(config) {
    const candidates = Object.keys(config.acmg.explanation).filter(
        (code) => !code.startsWith('REQ')
    )

    return sortCodeStrByTypeStrength(candidates, config)
}
