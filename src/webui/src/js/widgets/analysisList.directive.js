/* jshint esnext: true */

import {Directive, Inject} from '../ng-decorators';

@Directive({
    selector: 'analysis-list',
    bindToController: {
        analyses: '='
    },
    templateUrl: 'ngtmpl/analysisList.ngtmpl.html',
})
@Inject('$location', 'User', 'InterpretationResource', 'InterpretationOverrideModal')
class AnalysisListWidget {

    constructor(location, User, InterpretationResource, InterpretationOverrideModal) {
        this.location = location;
        this.user = User;
        this.interpretationResource = InterpretationResource;
        this.interpretationOverrideModal = InterpretationOverrideModal;
    }

    /**
     * Checks whether current user is working on an analysis.
     */
    isCurrentUser(analysis) {
        return this.user.getCurrentUserId() === analysis.getInterpretationUser().id;
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
}

export default AnalysisListWidget;
