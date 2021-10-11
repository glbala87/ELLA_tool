import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import getAlleleState from '../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getEditorReferences from '../store/modules/views/workflows/interpretation/computed/getEditorReferences'
import getSelectedInterpretation from '../store/modules/views/workflows/computed/getSelectedInterpretation'
import getManuallyAddedAlleleIds from '../store/modules/views/workflows/interpretation/computed/getManuallyAddedAlleleIds'
import template from './alleleSidebar.ngtmpl.html' // eslint-disable-line no-unused-vars

const showControls = Compute(state`views.workflows.selectedComponent`, (selectedComponent) => {
    return selectedComponent === 'Classification'
})

const constrainSize = Compute(
    state`views.workflows.alleleSidebar.classificationType`,
    (classificationType) => {
        return classificationType !== 'quick'
    }
)

const classificationType = Compute(
    state`views.workflows.selectedComponent`,
    state`views.workflows.alleleSidebar.classificationType`,
    (selectedComponent, stateClassificationType) => {
        return selectedComponent === 'Report' ? 'report' : stateClassificationType
    }
)

const isTogglable = Compute(state`views.workflows.selectedComponent`, (selectedComponent, get) => {
    if (!selectedComponent) {
        return false
    }
    return selectedComponent === 'Report'
})

const isToggled = Compute(
    state`views.workflows.interpretation.data.alleles`,
    state`views.workflows.selectedComponent`,
    (alleles, selectedComponent, get) => {
        const result = {}
        if (!alleles) {
            return result
        }
        for (const alleleId of Object.keys(alleles)) {
            if (selectedComponent !== 'Report') {
                result[alleleId] = false
                continue
            }
            const alleleState = get(getAlleleState(alleleId))
            result[alleleId] = alleleState.report.included
        }
        return result
    }
)

const filterConfigs = Compute(
    state`views.workflows.data.filterconfigs`,
    state`views.workflows.interpretation.state.filterconfigId`,
    (availableFilterconfigs, selectedFilterconfigId, get) => {
        return availableFilterconfigs
    }
)

const getExcludedAlleleCountsByCallerType = (excludedAlleleIds, callerType) => {
    return Compute(
        excludedAlleleIds,
        callerType,

        (excludedAlleleIds, callerType) => {
            if (!excludedAlleleIds || !callerType) {
                return
            }
            return excludedAlleleIds[callerType]
        }
    )
}

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            analysisId: state`views.workflows.data.analysis.id`,
            callerTypeSelected: state`views.workflows.alleleSidebar.callerTypeSelected`,
            callerTypes: state`views.workflows.alleleSidebar.callerTypes`,
            classificationTypes: state`views.workflows.alleleSidebar.classificationTypes`,
            constrainSize,
            selectedClassificationType: state`views.workflows.alleleSidebar.classificationType`,
            classificationType, // effective classification type, see Compute
            showControls,
            excludedAlleleCounts: getExcludedAlleleCountsByCallerType(
                state`views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids_by_caller_type`,
                state`views.workflows.alleleSidebar.callerTypeSelected`
            ),
            selectedGenepanel: state`views.workflows.selectedGenepanel`,
            indicationsComment: state`views.workflows.interpretation.state.report.indicationscomment`,
            commentTemplates: state`app.commentTemplates`,
            orderBy: state`views.workflows.alleleSidebar.orderBy`,
            selectedInterpretation: getSelectedInterpretation,
            selectedInterpretationId: state`views.workflows.interpretation.selectedId`,
            manuallyAddedAlleleIds: getManuallyAddedAlleleIds,
            excludedAlleleIds: state`views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids`,
            selectedFilterConfig: state`views.workflows.interpretation.data.filterConfig`,
            isTogglable,
            isToggled,
            readOnly: isReadOnly,
            showAddExcludedAllelesClicked: signal`views.workflows.modals.addExcludedAlleles.showAddExcludedAllelesClicked`,
            filterConfigs,
            filterconfigChanged: signal`views.workflows.alleleSidebar.filterconfigChanged`,
            classificationTypeChanged: signal`views.workflows.alleleSidebar.classificationTypeChanged`,
            indicationsCommentChanged: signal`views.workflows.interpretation.indicationsCommentChanged`,
            editorReferences: getEditorReferences('report'),
            callerTypeSelectedChanged: signal`views.workflows.alleleSidebar.callerTypeSelectedChanged`
        },
        'AlleleSidebar',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getExcludedAlleleCount: () => {
                        return Object.values($ctrl.excludedAlleleCounts)
                            .map((excluded_group) => excluded_group.length)
                            .reduce((total_length, length) => total_length + length)
                    },
                    isHistoricData: () => {
                        return (
                            !($ctrl.selectedInterpretationId === 'current') &&
                            $ctrl.selectedInterpretation.status === 'Done'
                        )
                    },
                    getFilterConfigs: () => {
                        if ($ctrl.isHistoricData()) {
                            return [$ctrl.selectedFilterConfig]
                        } else {
                            return $ctrl.filterConfigs
                        }
                    },
                    getReportIndicationsTemplates() {
                        return $ctrl.commentTemplates['reportIndications']
                    },
                    getSidebarConfig() {
                        return $ctrl.config.analysis.sidebar[$ctrl.classificationType]
                    }
                })
            }
        ]
    )
})
