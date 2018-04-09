/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allele-list',
    scope: {
        alleleItems: '=', // [{genepanel: {}, allele: Allele}, ...]
        newTarget: '=', // Open links in new target
        sort: '=?' // Whether to sort in client
    },
    templateUrl: 'ngtmpl/alleleList.ngtmpl.html',
})
@Inject('$scope',
        'Config',
        'Sidebar',
        'User',
        'Analysis',
        'InterpretationResource',
        'InterpretationOverrideModal',
        'toastr')
class AlleleListWidget {

    constructor($scope,
                Config,
                Sidebar,
                User,
                InterpretationResource,
                InterpretationOverrideModal,
                toastr) {
        this.config = Config.getConfig();
        this.user = User;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;
        this.toastr = toastr;
        this.sort = 'sort' in this ? this.sort : true;

        $scope.$watchCollection(
            () => this.alleleItems,
            () => this.sortItems()
        );
        this.sorted_items = [];
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

    getClassificationText(allele) {
        if ('allele_assessment' in allele) {
            return `CLASS ${allele.allele_assessment.classification}`
        }
        return 'NEW'
    }

    sortItems() {
        if (!this.alleleItems) { return; }
        this.sorted_items = this.alleleItems.slice();
        if (this.sort) {
            this.sorted_items.sort(
                firstBy(a => a.highest_analysis_priority, -1)
                .thenBy(a => {
                    // Ignore seconds/milliseconds when sorting
                    let d = new Date(a.oldest_analysis);
                    d.setSeconds(0,0);
                    return d.toISOString();
                })
                .thenBy(a => a.allele.annotation.filtered[0].symbol)
                .thenBy(a => {
                    if (a.allele.annotation.filtered[0].strand > 0) {
                        return a.allele.start_position;
                    }
                    return -a.allele.start_position;
                })
            );
        }
    }

    getPriorityText(item) {
        if (item.highest_analysis_priority > 1) {
            return this.config.analysis.priority.display[item.highest_analysis_priority];
        }
    }

    getReviewComment(item) {
        if (item.interpretations.length) {
            let last_interpretation = item.interpretations[item.interpretations.length-1];
            if ('review_comment' in last_interpretation) {
                return last_interpretation.review_comment;
            }
        }
    }

    getItemUrl(item) {
        return item.allele.getWorkflowUrl(item.genepanel);
    }
}

export default AlleleListWidget;
