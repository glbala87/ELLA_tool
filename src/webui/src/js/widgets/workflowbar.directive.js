import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import { getAcmgCandidates } from '../store/common/helpers/acmg'
import template from './workflowbar.ngtmpl.html' // eslint-disable-line no-unused-vars
import acmgSelectiontemplate from './acmgSelectionPopover.ngtmpl.html'
import interpretationLogPopover from './interpretationLogPopover.ngtmpl.html'
import { deepCopy } from '../util'
import { ACMGHelper } from '../model/acmghelper'
import isAlleleAssessmentReused from '../store/modules/views/workflows/interpretation/computed/isAlleleAssessmentReused'

let acmgCandidates = Compute(state`app.config`, (config) => {
    return getAcmgCandidates(config)
})

const historyInterpretations = Compute(
    state`views.workflows.data.interpretations`,
    (interpretations) => {
        if (!interpretations || interpretations.length === 0) {
            return []
        }
        let doneInterpretations = interpretations.filter((i) => i.status === 'Done')
        if (doneInterpretations.length === 0) {
            return []
        }

        let last_interpretation = deepCopy(doneInterpretations[doneInterpretations.length - 1])
        last_interpretation.id = 'current'
        doneInterpretations.push(last_interpretation)
        return doneInterpretations
    }
)

app.component('workflowbar', {
    templateUrl: 'workflowbar.ngtmpl.html',
    controller: connect(
        {
            analysis: state`views.workflows.data.analysis`,
            commentTemplates: state`app.commentTemplates`,
            config: state`app.config`,
            workflowLoaded: state`views.workflows.loaded`,
            messageCount: state`views.workflows.worklog.messageCount`,
            workflowType: state`views.workflows.type`,
            selectedComponent: state`views.workflows.selectedComponent`,
            componentKeys: state`views.workflows.componentKeys`,
            historyInterpretations: historyInterpretations,
            interpretations: state`views.workflows.data.interpretations`,
            selectedInterpretationId: state`views.workflows.interpretation.selectedId`,
            selectedAlleleId: state`views.workflows.selectedAllele`,
            isOngoing: state`views.workflows.interpretation.isOngoing`,
            genepanels: state`views.workflows.data.genepanels`,
            selectedGenepanel: state`views.workflows.selectedGenepanel`,
            isCurrentAlleleReused: isAlleleAssessmentReused(state`views.workflows.selectedAllele`),
            readOnly: isReadOnly,
            acmgCandidates,
            componentChanged: signal`views.workflows.componentChanged`,
            collapseAllAlleleSectionboxClicked: signal`views.workflows.interpretation.collapseAllAlleleSectionboxClicked`,
            selectedInterpretationChanged: signal`views.workflows.selectedInterpretationChanged`,
            showGenepanelOverviewClicked: signal`views.workflows.modals.genepanelOverview.showGenepanelOverviewClicked`,
            copySelectedAlamutClicked: signal`views.workflows.copySelectedAlamutClicked`,
            selectedGenepanelChanged: signal`views.workflows.selectedGenepanelChanged`,
            addAcmgClicked: signal`views.workflows.interpretation.addAcmgClicked`,
            addReferencesClicked: signal`views.workflows.modals.addReferences.showAddReferencesClicked`,
            allele: state`views.workflows.allele`,
            alleles: state`views.workflows.interpretation.data.alleles`,
            showAnalysesForAlleleClicked: signal`search.modals.showAnalysesForAllele.showAnalysesForAlleleClicked`,
            callerTypes: state`views.workflows.alleleSidebar.callerTypes`,
            callerTypeSelected: state`views.workflows.alleleSidebar.callerTypeSelected`,
            callerTypeSelectedChanged: signal`views.workflows.alleleSidebar.callerTypeSelectedChanged`
        },
        'Workflow',
        [
            '$scope',
            '$filter',
            function($scope, $filter) {
                const $ctrl = $scope.$ctrl

                Object.assign($scope.$ctrl, {
                    formatHistoryOption: (interpretation) => {
                        if (interpretation.id === 'current') {
                            return 'Current data'
                        }
                        let interpretation_idx = $ctrl.interpretations.indexOf(interpretation) + 1
                        let interpretation_date = $filter('date')(
                            interpretation.date_last_update,
                            'yyyy-MM-dd'
                        )
                        return `${interpretation_idx} • ${interpretation.workflow_status}${
                            interpretation.finalized ? ' (Finalized)' : ''
                        } • ${interpretation.user.abbrev_name} • ${interpretation_date}`
                    },
                    showComponentDropdown: () => {
                        return Boolean($ctrl.components.length > 1)
                    },
                    showHistory: () => {
                        return (
                            !$ctrl.isOngoing &&
                            $ctrl.historyInterpretations &&
                            $ctrl.historyInterpretations.length
                        )
                    },
                    //
                    // Add ACMG popover
                    //
                    acmgPopover: {
                        categories: ['Pathogenic', 'Benign', 'Other'],
                        selectedCategory: 'Pathogenic',
                        getAcmgClass(code) {
                            if (ACMGHelper.getCodeType(code) === 'other') {
                                return 'other'
                            } else {
                                let acmgclass = code.substring(0, 2).toLowerCase()
                                return code.includes('x') ? `indented ${acmgclass}` : acmgclass
                            }
                        },
                        getExplanationForCode(code) {
                            return $ctrl.config.acmg.explanation[code]
                        },
                        stageAcmgCode(code) {
                            let existingComment = $ctrl.stagedAcmgCode
                                ? $ctrl.stagedAcmgCode.comment
                                : ''
                            $ctrl.stagedAcmgCode = {
                                code: code,
                                comment: existingComment,
                                source: 'user',
                                op: null,
                                match: null
                            }
                        },
                        addStagedAcmgCode() {
                            if ($ctrl.stagedAcmgCode) {
                                $ctrl.addAcmgClicked({
                                    alleleId: $ctrl.selectedAlleleId,
                                    code: $ctrl.stagedAcmgCode
                                })
                            }
                            $ctrl.stagedAcmgCode = null
                        },
                        getAcmgCommentTemplates() {
                            return $ctrl.commentTemplates['classificationAcmg']
                        }
                    }
                })
            }
        ]
    )
})
