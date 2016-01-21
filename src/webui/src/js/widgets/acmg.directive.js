/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'acmg',
    scope: {
        codes: '=',
        selector: '@'
    },
    templateUrl: 'ngtmpl/acmg.ngtmpl.html'
})
@Inject('Config')
export class AcmgController {


    constructor(Config) {
        this.config = Config.getConfig();
    }

    getSource(code) {
        return code.source.split('.').slice(1).join('->');
    }

    getACMGclass(code) {
        return code.code.substring(0, 2).toLowerCase();
    }

    getOperator(code) {
        return this.config.acmg.formatting.operators[code.op];
    }

    getValue(code) {
        return code.value.join(',');
    }

    getCodes() {
        if (this.selector) {
            if (this.codes) {
                return this.codes.filter(c => {
                    return c.source === this.selector;
                });
            }
            else {
                return [];
            }
        }
        else {
            return this.codes;
        }
    }

}
