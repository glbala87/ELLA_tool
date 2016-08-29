/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'acmg',
    scope: {
        code: '=',  // Single code or Array of (same) codes
        commentModel: '=?',
        editable: '=?',  // Defaults to false
        onToggle: '&?',
        toggleText: '@?',
        addRequiredForCode: '&?' // Callback when clicking on code in "required for" section
    },
    templateUrl: 'ngtmpl/acmg.ngtmpl.html'
})
@Inject('Config')
export class AcmgController {

    constructor(Config) {
        this.config = Config.getConfig();
        this.popover = {
            templateUrl: 'ngtmpl/acmgPopover.ngtmpl.html'
        };
        this.matches = this.getMatches();
    }

    toggle() {
        if (this.onToggle && this.isEditable()) {
            this.onToggle({code: this.code});
        }
    }

    isEditable() {
        return this.editable !== undefined ? this.editable : false;
    }

    isMultiple() {
        return Array.isArray(this.code);
    }

    getCodeForDisplay() {
        if (this.isMultiple()) {
            return this.code[0];  // If multiple codes, they should all be the same
        }
        return this.code;
    }

    getPlaceholder() {
        if (this.isEditable()) {
            return 'ACMG-COMMENT';
        }
    }

    _getMatch(code) {
        if (code.source === 'user') {
            return 'Added by user';
        }
        if (Array.isArray(code.match)) {
            return code.match.join(', ');
        }
        return code.match;
    }


    _getOperator(code) {
        return this.config.acmg.formatting.operators[code.op];
    }

    _getSource(code) {
        if (code.source) {
            return code.source.split('.').slice(1).join('->');
        }
        return 'N/A';
    }

    getMatches() {
        let codes = this.isMultiple() ? this.code : [this.code];
        return codes.map(c => {
            return {
                source: this._getSource(c),
                match: this._getMatch(c),
                op: this._getOperator(c)
            };
        });
    }

    getACMGclass(code) {
        if (code === undefined) {
            code = this.getCodeForDisplay().code;
        }
        if (code) {
            return code.substring(0, 2).toLowerCase();
        }
    }


    getCriteria() {
        if (this.getCodeForDisplay().code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.getCodeForDisplay().code].criteria;
        }
    }

    getShortCriteria() {
        if (this.getCodeForDisplay().code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.getCodeForDisplay().code].short_criteria;
        }
    }

    getRequiredFor() {
        if (this.getCodeForDisplay().code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.getCodeForDisplay().code].sources;
        }
    }

    getNotes() {
        if (this.getCodeForDisplay().code in this.config.acmg.explanation &&
            'notes' in this.config.acmg.explanation[this.getCodeForDisplay().code]) {
            return this.config.acmg.explanation[this.getCodeForDisplay().code].notes;
        }
    }

    clickAddRequiredForCode(code) {
        if (this.addRequiredForCode) {
            this.addRequiredForCode({code: code});
        }
    }

}
