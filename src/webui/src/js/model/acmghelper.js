/* jshint esnext: true */

export class ACMGHelper {
    /**
     * Returns the base ACMG code, without strength applier.
     *
     * @param {String} code_str
     */
    static getCodeBase(code_str) {
        if (code_str.includes('x')) {
            return code_str.split('x', 2)[1]
        }
        return code_str
    }

    static _upgradeDowngradeCode(code_str, config, upgrade = true) {
        let code_strength, base
        if (code_str.includes('x')) {
            ;[code_strength, base] = code_str.split('x', 2)
        }

        // If code is benign, upgrading the code should mean 'more benign' and vice versa
        if (this._extractCodeType(code_str) === 'benign') {
            upgrade = !upgrade
        }

        for (let strengths of Object.values(config.acmg.codes)) {
            // If strength is given (i.e. the code is not already upgraded/downgraded)
            // we need to find the strength of the base.
            if (code_strength === undefined) {
                base = code_str
                for (let s of strengths) {
                    if (code_str.startsWith(s)) {
                        code_strength = s
                    }
                }
            }

            let strength_idx = strengths.indexOf(code_strength)
            if (strength_idx < 0) {
                // If strength not part of set, try next one
                continue
            }

            // Check whether we can upgrade code, or if it would overflow
            let overflow = upgrade ? strength_idx === 0 : strength_idx >= strengths.length - 1
            if (!overflow) {
                let new_strength = upgrade
                    ? strengths[strength_idx - 1]
                    : strengths[strength_idx + 1]
                // If new strength is same as base we just return base
                if (base.startsWith(new_strength)) {
                    return base
                }
                return `${new_strength}x${base}`
            }
            // If overflowing, return input
            return code_str
        }
        return code_str
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

    static _extractCodeType(code_str) {
        let base = this.getCodeBase(code_str)
        if (base.startsWith('B')) {
            return 'benign'
        } else {
            return 'pathogenic'
        }
    }
}
