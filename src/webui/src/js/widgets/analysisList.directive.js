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
        // this.sidebar = Sidebar;
        this.user = User;
        this.analysisService = Analysis;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;
        this.toastr = toastr;
        this.previous = {}

        // this.setupSidebar();
    }

    // setupSidebar() {
    //     this.sidebar.setBackLink(null, null);
    //     this.sidebar.setTitle('Analyses List', false);
    //     this.sidebar.clearItems();
    // }

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

    idempoByDate() {
      let cur = this.analysesByDate();
      if(JSON.stringify(this.previous) != JSON.stringify(cur)) {
        this.previous = cur;
      }
      return this.previous;
    }

    analysesByDate() {
      // FIXME: Hi i'm an infinite loop in angular
      let byday = {};
      function groupday(value, index, array)
      {
        let d = value['deposit_date'].substring(0,10);
        byday[d]=byday[d]||[];
        byday[d].push(value);
      }
      this.analyses.forEach(groupday);
      return byday;
    }

    clickAnalysis(analysis) {
        if (this.isAnalysisDone(analysis)) {
            // this.toastr.error("Sorry, opening a finished analysis is not implemented yet.", null, 5000);
            this.toastr.warning("Opening a finished analysis in read-only mode", null, 600);
            this.openAnalysis(analysis);
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
}

export default AnalysisListWidget;
