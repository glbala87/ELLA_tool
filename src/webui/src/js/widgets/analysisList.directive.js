/* jshint esnext: true */

import {Directive} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    bindToController: {
        analyses: '='
    },
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
})
class AnalysisListWidget {}

export default AnalysisListWidget;
