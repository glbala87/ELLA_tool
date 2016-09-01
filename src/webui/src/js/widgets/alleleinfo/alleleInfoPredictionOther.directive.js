/* jshint esnext: true */

import {Directive, Inject} from '../../ng-decorators';

@Directive({
    selector: 'allele-info-prediction-other',
    scope: {
        allele: '=',
        cbOptions: '='
    },
    templateUrl: 'ngtmpl/alleleInfoPredictionOther.ngtmpl.html'
})
@Inject('Config')
export class AlleleInfoPredictionOther {

    constructor(Config) {
        this.config = Config.getConfig();

        this.cbOptions.title = 'Other';
        this.checkForContent();
    }

    checkForContent() {
        if (!this.hasContent()) {
            this.cbOptions.disabled = true;
            this.cbOptions.collapsed = true;
        };
    }

    hasContent() {
        return this.config.custom_annotation.prediction.some(group => {
            return 'prediction' in this.allele.annotation &&
                   group.key in this.allele.annotation.prediction
        });
    }
}
