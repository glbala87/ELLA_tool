/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'acmg',
    scope: {
        code: '=',
        commentModel: '=?',
        onToggle: '&?',
        toggleText: '@?'
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
    }

    toggle() {
        if (this.onToggle) {
            this.onToggle({code: this.code});
        }
    }

    getSource() {
        return this.code.source.split('.').slice(1).join('->');
    }

    getACMGclass() {
        if (this.code) {
            return this.code.code.substring(0, 2).toLowerCase();
        }
    }

    getOperator() {
        return this.config.acmg.formatting.operators[this.code.op];
    }

    getValue() {
        return this.code.value.join(', ');
    }

    getMatch() {
        if (this.code.source === 'user') {
            return 'Added by user';
        }
        if (Array.isArray(this.code.match)) {
            return this.code.match.join(', ');
        }
        return this.code.match;
    }

    getCriteria() {
        if (this.code.code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.code.code].criteria;
        }
    }

    getShortCriteria() {
        if (this.code.code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.code.code].short_criteria;
        }
    }

    getRequiredFor() {
        if (this.code.code in this.config.acmg.explanation) {
            return this.config.acmg.explanation[this.code.code].sources;
        }
    }

    getNotes() {
        if (this.code.code in this.config.acmg.explanation &&
            'notes' in this.config.acmg.explanation[this.code.code]) {
            return this.config.acmg.explanation[this.code.code].notes;
        }
    }

}
