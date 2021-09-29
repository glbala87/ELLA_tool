/* jshint esnext: true */

import { Directive, Inject } from '../ng-decorators'
import { ACMGHelper } from '../model/acmghelper'
import acmgTemplate from './acmg.ngtmpl.html'
import acmgPopover from './acmgPopover.ngtmpl.html'

const STRENGTHS_CLINGEN = {
    benign: {
        BNW: 'Not weighted',
        BP: 'Supportive',
        BS: 'Strong',
        BA: 'Stand-alone'
    },
    pathogenic: {
        PNW: 'Not weighted',
        PP: 'Supportive',
        PM: 'Moderate',
        PS: 'Strong',
        PVS: 'Very_strong'
    }
}

@Directive({
    selector: 'acmg',
    scope: {
        code: '=', // Single code or Array of (same) codes
        templates: '=',
        references: '=?',
        commentModel: '=?',
        editable: '=?', // Defaults to false
        directreqs: '=?', // Defaults to false
        collapsed: '=?',
        isUpgradable: '=?',
        isDowngradable: '=?',
        onToggle: '&?',
        onUpdate: '&?', // when comment changes or upgrade/downgrade
        toggleText: '@?',
        addRequiredForCode: '&?' // Callback when clicking on code in "required for" section
    },
    template: acmgTemplate
})
@Inject('Config', '$scope')
export class AcmgController {
    constructor(Config, $scope) {
        this.config = Config.getConfig()
        this.popover = {
            templateUrl: 'acmgPopover.ngtmpl.html'
        }

        $scope.$watch(
            () => this.code,
            () => {
                this.matches = this.getMatches()
            }
        )
    }

    toggle() {
        if (this.onToggle && this.isEditable()) {
            this.onToggle({ code: this.code })
        }
    }

    formatCode(codeStr) {
        if (ACMGHelper.isModifiedStrength(codeStr)) {
            const strength = ACMGHelper.getCodeStrength(codeStr, this.config)
            const base = ACMGHelper.getCodeBase(codeStr)
            const codeType = ACMGHelper.getCodeType(codeStr)
            return `${base} ${STRENGTHS_CLINGEN[codeType][strength].toUpperCase()}`
        }
        return codeStr
    }

    isEditable() {
        return this.editable !== undefined ? this.editable : false
    }

    isUpgradable() {
        if (Array.isArray(this.code)) {
            return false
        }
        return ACMGHelper.canUpgradeCodeObj(this.code, this.config)
    }

    isDowngradable() {
        if (Array.isArray(this.code)) {
            return false
        }
        return ACMGHelper.canDowngradeCodeObj(this.code, this.config)
    }

    isInACMGsection() {
        return this.editable !== undefined ? this.editable : false
    }

    isMultiple() {
        return Array.isArray(this.code)
    }

    isMoreThanOne() {
        return this.isMultiple() ? this.code.length > 1 : false
    }

    getCodeForDisplay() {
        if (this.isMultiple()) {
            return this.code[0] // If multiple codes, they should all be the same
        }
        return this.code
    }

    getCodeBase() {
        return ACMGHelper.getCodeBase(this.getCodeForDisplay().code)
    }

    getPlaceholder() {
        if (this.isEditable()) {
            return `${ACMGHelper.getCodeBase(this.getCodeForDisplay().code)}-COMMENT`
        }
    }

    _getMatch(code) {
        if (code.source === 'user') {
            return 'Added by user'
        }
        if (Array.isArray(code.match)) {
            return code.match.join(', ')
        }
        return code.match
    }

    _getOperator(code) {
        return this.config.acmg.formatting.operators[code.op]
    }

    _getSource(code) {
        if (code.source) {
            return code.source
                .split('.')
                .slice(1)
                .join('->')
        }
        return 'N/A'
    }

    upgradeCode() {
        ACMGHelper.upgradeCodeObj(this.code, this.config)
        if (this.onUpdate) {
            this.onUpdate()
        }
    }

    downgradeCode() {
        ACMGHelper.downgradeCodeObj(this.code, this.config)
        if (this.onUpdate) {
            this.onUpdate()
        }
    }

    getMatches() {
        let codes = this.isMultiple() ? this.code : [this.code]
        return codes.map((c) => {
            return {
                source: this._getSource(c),
                match: this._getMatch(c),
                op: this._getOperator(c)
            }
        })
    }

    getACMGclass(code) {
        if (code === undefined) {
            code = this.getCodeForDisplay().code
        }

        if (code) {
            if (ACMGHelper.getCodeType(code) === 'other') {
                return 'other'
            } else {
                return code.substring(0, 2).toLowerCase()
            }
        }
    }

    getCriteria() {
        if (this.getCodeBase() in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.getCodeBase()].criteria
        }
    }

    getShortCriteria() {
        if (this.getCodeBase() in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.getCodeBase()].short_criteria
        }
    }

    getRequiredFor() {
        if (this.getCodeForDisplay().code in this.config.acmg.explanation) {
            if (this.getCodeForDisplay().code.startsWith('REQ_GP')) {
                return []
            }
            return this.config.acmg.explanation[this.getCodeForDisplay().code].sources
        }
    }

    getNotes() {
        if (
            this.getCodeBase() in this.config.acmg.explanation &&
            'notes' in this.config.acmg.explanation[this.getCodeBase()]
        ) {
            return this.config.acmg.explanation[this.getCodeBase()].notes.split(/\n/)
        }
    }

    getInternalNotes() {
        if (
            this.getCodeBase() in this.config.acmg.explanation &&
            'internal_notes' in this.config.acmg.explanation[this.getCodeBase()]
        ) {
            return this.config.acmg.explanation[this.getCodeBase()].internal_notes.split(/\n/)
        }
    }

    clickAddRequiredForCode(code) {
        if (this.addRequiredForCode) {
            this.addRequiredForCode({ code: code })
        }
    }
}
