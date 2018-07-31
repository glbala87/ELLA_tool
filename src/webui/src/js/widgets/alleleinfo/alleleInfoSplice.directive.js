/* jshint esnext: true */

import { Directive, Inject } from '../../ng-decorators'
import template from './alleleInfoSplice.ngtmpl.html'

@Directive({
    selector: 'allele-info-splice',
    scope: {
        allele: '='
    },
    template
})
@Inject()
export class AlleleInfoSplice {
    constructor() {
        if (!this.hasContent()) {
            this.collapsed = true
        }
    }

    hasContent() {
        return this.allele.annotation.filtered.some((t) => 'splice' in t)
    }
}
