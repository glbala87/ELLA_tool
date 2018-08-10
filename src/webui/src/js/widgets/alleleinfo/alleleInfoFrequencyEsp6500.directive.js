/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import template from './alleleInfoFrequencyEsp6500.ngtmpl.html'

@Directive({
    selector: 'allele-info-frequency-esp6500',
    scope: {
        allele: '='
    },
    template
})
@Inject()
export class AlleleInfoFrequencyEsp6500 {
    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true
        }
    }

    hasContent() {
        return 'esp6500' in this.allele.annotation.frequencies
    }
}
