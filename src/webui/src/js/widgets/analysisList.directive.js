/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    bindToController: {
        analyses: '='
    },
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
})
@Inject('$location',
        'Sidebar',
        'User',
        'InterpretationResource',
        'InterpretationOverrideModal')
class AnalysisListWidget {

    constructor(location, Sidebar, User, InterpretationResource, InterpretationOverrideModal) {
        this.location = location;
        this.sidebar = Sidebar;
        this.user = User;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;

        this.setupSidebar();
    }

    setupSidebar() {
        this.sidebar.setBackLink(null, null);
        this.sidebar.setTitle('Analyses List', false);
        this.sidebar.clearItems();
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
                 i.status === 'Done'
        ).length > 0;
    }

    openAnalysis(analysis) {
        this.location.path(`/interpretation/${analysis.getInterpretationId()}`);
    }

    overrideInterpretation(analysis, username) {
        this.interpretationResource.override(
            analysis.getInterpretationId(),
            username
        ).then(() => {
            this.openAnalysis(analysis);
        })
    }

    clickAnalysis(analysis) {
        if (this.userAlreadyAnalyzed(analysis)) {
            return;
        }
        let iuser = analysis.getInterpretationUser();
        if (iuser &&
            iuser.id !== this.user.getCurrentUserId()) {
            this.interpretationOverrideModal.show().then(result => {
                if (result) {
                    this.overrideInterpretation(
                        analysis,
                        this.user.getCurrentUserId()
                    );
                }
            })

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
