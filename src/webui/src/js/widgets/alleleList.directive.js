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
        'Sidebar',
        'User',
        'Analysis',
        'InterpretationResource',
        'InterpretationOverrideModal',
        'toastr')
class AlleleListWidget {

    constructor($scope,
                Sidebar,
                User,
                InterpretationResource,
                InterpretationOverrideModal,
                toastr) {
        this.location = location;
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
            firstBy(a => a.allele.annotation.filtered[0].SYMBOL)
            .thenBy(a => a.allele.annotation.filtered[0].HGVSc_short)
        );
    }


    /**
     * Checks whether current user is working on an analysis.
     */
    isCurrentUser(analysis) {
        return this.user.getCurrentUserId() === analysis.getInterpretationUser().id;
    }

    userAlreadyAnalyzed(analysis) {
        let current_user_id = this.user.getCurrentUserId();
        return analysis.interpretations.filter(
            i => i.user &&
                 i.user.id === current_user_id &&
                 i.status !== 'Ongoing'  // Exempt if in progress by user
        ).length > 0;
    }

    isAnalysisDone(analysis) {
        return analysis.interpretations.length &&
               analysis.interpretations.every(
                   i => i.status === 'Done'
               );
    }

    openAnalysis(analysis) {
        if (this.onSelect) {
            this.onSelect(analysis);
        }
        this.analysisService.openAnalysis(analysis.id);
    }

    overrideAnalysis(analysis) {
        this.analysisService.override(
            analysis.id,
        ).then(() => {
            this.openAnalysis(analysis);
        });
    }

    abbreviateUser(user) {
      if(Object.keys(user).length != 0) {
        return `${user.first_name.substring(0,1)}. ${user.last_name}`;
      } else {
        return "";
      }
    }

    clickAnalysis(analysis) {
        if (this.isAnalysisDone(analysis)) {
            this.toastr.error("Sorry, opening a finished analysis is not implemented yet.", null, 5000);
            return;
        }

        let iuser = analysis.getInterpretationUser();
        if (iuser &&
            iuser.id !== this.user.getCurrentUserId()) {
            this.interpretationOverrideModal.show().then(result => {
                if (result) {
                    this.overrideAnalysis(analysis);
                }
            });
        }
        else {
            this.openAnalysis(analysis);
        }
    }

    getStateMessage(analysis) {
        if (!analysis) {
            return "Analysis is null";
        }
        if (analysis.getInterpretationState() === 'Not started' &&
            analysis.interpretations.length > 1) {
            return 'Needs review';
        }
        return analysis.getInterpretationState();
    }

    getAlleleUrl(allele) {
        return `/variants/${allele.genome_reference}/${allele.chromosome}-${allele.start_position}-${allele.open_end_position}-${allele.change_from}-${allele.change_to}`;
    }
}

export default AlleleListWidget;
