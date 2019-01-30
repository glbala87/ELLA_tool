import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import isExpanded from '../store/modules/views/workflows/alleleSidebar/computed/isExpanded'
import getAlleleState from '../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getSelectedInterpretation from '../store/modules/views/workflows/computed/getSelectedInterpretation'
import getManuallyAddedAlleleIds from '../store/modules/views/workflows/interpretation/computed/getManuallyAddedAlleleIds'
import template from './alleleSidebar.ngtmpl.html'

const showQuickClassificationBtn = Compute(
    state`views.workflows.selectedComponent`,
    (selectedComponent) => {
        return selectedComponent === 'Classification'
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

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {
            analysisId: state`views.workflows.data.analysis.id`,
            selectedGenepanel: state`views.workflows.selectedGenepanel`,
            orderBy: state`views.workflows.alleleSidebar.orderBy`,
            selectedInterpretation: getSelectedInterpretation,
            selectedInterpretationId: state`views.workflows.interpretation.selectedId`,
            manuallyAddedAlleleIds: getManuallyAddedAlleleIds,
            excludedAlleleIds: state`views.workflows.interpretation.data.filteredAlleleIds.excluded_allele_ids`,
            showQuickClassificationBtn,
            expanded: isExpanded,
            isTogglable,
            isToggled,
            readOnly: isReadOnly,
            toggleExpanded: signal`views.workflows.alleleSidebar.toggleExpanded`,
            addExcludedAllelesClicked: signal`modals.addExcludedAlleles.addExcludedAllelesClicked`,
            filterConfigs,
            filterconfigChanged: signal`views.workflows.alleleSidebar.filterconfigChanged`,
            selectedFilterConfig: state`views.workflows.interpretation.data.filterConfig`
        },
        'AlleleSidebar',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                $scope.$watch(
                    () => {
                        return $ctrl.selectedFilterConfig
                    },
                    () => {
                        console.log($ctrl.selectedFilterConfig.filterconfig.filters)
                    }
                )

                Object.assign($ctrl, {
                    getExcludedAlleleCount: () => {
                        return Object.values($ctrl.excludedAlleleIds)
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
                    }
                })
            }
        ]
    )
})
