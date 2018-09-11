import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { Compute } from 'cerebral'
import template from './alleleSidebar.ngtmpl.html'
import isReadOnly from '../store/modules/views/workflows/computed/isReadOnly'
import isExpanded from '../store/modules/views/workflows/alleleSidebar/computed/isExpanded'
import getVerificationStatus from '../store/modules/views/workflows/interpretation/computed/getVerificationStatus'
import getAlleleState from '../store/modules/views/workflows/interpretation/computed/getAlleleState'
import getClassification from '../store/modules/views/workflows/alleleSidebar/computed/getClassification'

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
    state`views.workflows.data.alleles`,
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

app.component('alleleSidebar', {
    templateUrl: 'alleleSidebar.ngtmpl.html',
    controller: connect(
        {
            analysisId: state`views.workflows.data.analysis.id`,
            orderBy: state`views.workflows.alleleSidebar.orderBy`,
            selectedInterpretation: state`views.workflows.interpretation.selected`,
            showQuickClassificationBtn,
            expanded: isExpanded,
            isTogglable,
            isToggled,
            readOnly: isReadOnly,
            toggleExpanded: signal`views.workflows.alleleSidebar.toggleExpanded`,
            addExcludedAllelesClicked: signal`modals.addExcludedAlleles.addExcludedAllelesClicked`
        },
        'AlleleSidebar',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getExcludedAlleleCount: () => {
                        if ($ctrl.selectedInterpretation) {
                            return Object.values($ctrl.selectedInterpretation.excluded_allele_ids)
                                .map((excluded_group) => excluded_group.length)
                                .reduce((total_length, length) => total_length + length)
                        }
                    }
                })
            }
        ]
    )
})
