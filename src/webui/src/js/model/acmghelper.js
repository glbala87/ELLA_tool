/* jshint esnext: true */

export class ACMGHelper {
    /**
     * Returns the base ACMG code, without strength applier.
     *
     * @param {String} codeStr
     */
    static getCodeBase(codeStr) {
        if (codeStr.startsWith('REQ')) {
            return codeStr
        }
        const codeParts = codeStr.split('x')
        if (codeParts.length > 2) {
            throw Error(`Too many 'x' present in ${codeStr}`)
        }
        return codeParts[codeParts.length - 1]
    }

    static isModifiedStrength(codeStr) {
        return !codeStr.startsWith('REQ') && codeStr.includes('x')
    }

    /**
     * Returns the current strength for the input code
     *
     * @param {*} code_str Full internal code, e.g. BPxBA1 or PVS1
     * @param {*} config App config
     * @returns {String} ACMG code strength (e.g. BS, PVS etc) or null
     */
    static getCodeStrength(code_str, config) {
        let codeStrength = null
        for (let strengths of Object.values(config.acmg.codes)) {
            for (let s of strengths) {
                if (code_str.startsWith(s)) {
                    codeStrength = s
                }
            }
            if (codeStrength) {
                break
            }
        }
        return codeStrength
    }

    static _upgradeDowngradeCode(codeStr, config, upgrade = true) {
        const base = this.getCodeBase(codeStr)
        const codeStrength = this.getCodeStrength(codeStr, config)
        const codeType = this.getCodeType(codeStr)

        if (codeType === 'other') {
            return codeStr
        }

        // If code is benign, upgrading the code should mean 'more benign' and vice versa
        if (codeType === 'benign') {
            upgrade = !upgrade
        }
        const configStrengths = config.acmg.codes[codeType]
        const strengthIdx = configStrengths.indexOf(codeStrength)
        const wouldOverflow = upgrade
            ? strengthIdx === 0
            : strengthIdx >= configStrengths.length - 1

        let newCode = null

        if (!wouldOverflow) {
            const newStrength = upgrade
                ? configStrengths[strengthIdx - 1]
                : configStrengths[strengthIdx + 1]

            // If new strength is same as base strength we just return base
            // in order to avoid BSxBS1
            const baseStrength = this.getCodeStrength(base, config)
            if (newStrength === baseStrength) {
                newCode = base
            } else {
                newCode = `${newStrength}x${base}`
            }
        } else {
            newCode = codeStr
        }

        return newCode
    }

    static upgradeCodeObj(code, config) {
        code.code = this._upgradeDowngradeCode(code.code, config, true)
        return code
    }

    static canUpgradeCodeObj(code, config) {
        return code.code !== this._upgradeDowngradeCode(code.code, config, true)
    }

    static downgradeCodeObj(code, config) {
        code.code = this._upgradeDowngradeCode(code.code, config, false)
        return code
    }

    static canDowngradeCodeObj(code, config) {
        return code.code !== this._upgradeDowngradeCode(code.code, config, false)
    }

    static getCodeType(codeStr) {
        let base = this.getCodeBase(codeStr)
        if (base.startsWith('B')) {
            return 'benign'
        } else if (base.startsWith('P')) {
            return 'pathogenic'
        } else {
            return 'other'
        }
    }
}
