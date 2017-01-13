/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    scope: {
        analyses: '=',
        onSelect: '&?' // Selection callback. Used to clear search
    },
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
})
@Inject('Sidebar',
        'User',
        'Analysis',
        'InterpretationResource',
        'InterpretationOverrideModal',
        'toastr')
class AnalysisListWidget {

    constructor(Sidebar,
                User,
                Analysis,
                InterpretationResource,
                InterpretationOverrideModal,
                toastr) {
        this.location = location;
        this.user = User;
        this.analysisService = Analysis;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;
        this.toastr = toastr;
        this.previous = {}
    }

    isAnalysisDone(analysis) {
        return analysis.interpretations.length &&
               analysis.interpretations.every(
                   i => i.status === 'Done'
               );
    }

    getReviewComment(analysis) {
        return analysis.interpretations[analysis.interpretations.length-1].review_comment;
    }

    abbreviateUser(user) {
      if(Object.keys(user).length != 0) {
        return `${user.first_name.substring(0,1)}. ${user.last_name}`;
      } else {
        return "";
      }
    }
}

export default AnalysisListWidget;
