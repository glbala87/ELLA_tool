/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    scope: {
        analyses: '=',
        newTarget: '=' // Open links in new target
    },
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
})
@Inject('$scope',
        'Config',
        'User')
class AnalysisListWidget {

    constructor($scope,
                Config,
                User) {

        this.config = Config.getConfig();
        this.user = User;

        $scope.$watchCollection(
            () => this.analyses,
            () => this.sortItems()
        );
        this.sorted_analyses = [];
    }

    getEndAction(interpretation) {
        let OPTIONS = {
            'Mark review': 'Marked for review',
            'Finalize': 'Finalized'
        }
        if (interpretation.end_action) {
            return ' ' + OPTIONS[interpretation.end_action] + ' • '
        }
        return ''
    }

    sortItems() {
        if (!this.analyses.length) { return; }
        this.sorted_analyses = this.analyses.slice(0);
        this.sorted_analyses.sort(
            firstBy(a => a.priority, -1)
            .thenBy(a => a.deposit_date)
        );
    }


    isAnalysisDone(analysis) {
        return analysis.interpretations.length &&
               analysis.interpretations.every(
                   i => i.status === 'Done'
               );
    }

    getPriorityText(analysis) {
        if (analysis.priority > 1) {
            return this.config.analysis.priority.display[analysis.priority];
        }
    }


    getReviewComment(analysis) {
        return analysis.interpretations[analysis.interpretations.length-1].review_comment;
    }
}

export default AnalysisListWidget;
