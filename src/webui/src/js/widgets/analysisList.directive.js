/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    scope: {
        analyses: '=',
        newTarget: '=', // Open links in new target
        sort: '=?' // Whether to sort in client
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
        this.sort = 'sort' in this ? this.sort : true;
    }

    getEndAction(interpretation) {
        let end_action = `${interpretation.workflow_status} ${interpretation.finalized ? ' (Finalized) ' : ' '}`
        if (interpretation.user) {
            return end_action + ' • '
        }
        else {
            return end_action
        }
    }

    sortItems() {
        if (!this.analyses.length) { return; }
        this.sorted_analyses = this.analyses.slice(0);
        if (this.sort) {
            this.sorted_analyses.sort(
                firstBy(a => a.priority, -1)
                .thenBy(a => a.deposit_date)
            );
        }
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
