/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-external-other',
    scope: {
        allele: '=',
        collapsed: '=?'
    },
    templateUrl: 'ngtmpl/alleleInfoExternalOther.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoExternalOther {

    constructor(Config) {
        this.config = Config.getConfig();

        if (!this.hasContent()) {
            this.collapsed = true;
        }
    }

    hasContent() {
        return this.config.custom_annotation.external.some(group => {
            return 'external' in this.allele.annotation &&
                   group.key in this.allele.annotation.external
        });
    }
}
