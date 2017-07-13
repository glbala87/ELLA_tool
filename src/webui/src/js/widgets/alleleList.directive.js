/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'allele-list',
    scope: {
        alleleItems: '=', // [{genepanel: {}, allele: Allele}, ...]
        onSelect: '&?' // Selection callback. Used to clear search
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

        $scope.$watchCollection(
            () => this.alleleItems,
            () => this.sortItems()
        );
        this.sorted_items = [];
    }


    sortItems() {
        if (!this.alleleItems) { return; }
        this.sorted_items = this.alleleItems.slice(0);
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
        let allele = item.allele;
        return item.allele.getWorkflowUrl(item.genepanel);
    }
}

export default AlleleListWidget;
