/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state } from 'cerebral/tags'
import { Compute } from 'cerebral'
import { deepCopy } from '../../util'
import { sortCodesByTypeStrength } from '../../store/common/helpers/acmg'

import template from './alleleHistory.ngtmpl.html'

const combinedAssessmentsReport = Compute(
    state`views.workflows.modals.alleleHistory.data.alleleassessments`,
    state`views.workflows.modals.alleleHistory.data.allelereports`,
    (alleleAssessments, alleleReports) => {
        // Join allele reports and allele assessments created together. This is done by assuming that allele reports
        // and allele assessments created within 10 seconds of each other are created together.
        if (alleleAssessments === undefined || alleleReports == undefined) {
            return []
        }

        let summaryItems = []
        for (let aa of alleleAssessments) {
            summaryItems.push({ alleleAssessment: aa, alleleReport: null })
        }

        for (let ar of alleleReports) {
            // Find first item created before (or within 10 seconds) of allele report
            let idx = summaryItems.findIndex((item) => {
                let d1 = item.alleleAssessment
                    ? item.alleleAssessment.seconds_since_update
                    : item.alleleReport.seconds_since_update
                let d2 = ar.seconds_since_update

                return d2 < d1 + 10
            })

            let aa = summaryItems[idx].alleleAssessment
            if (Math.abs(aa.seconds_since_update - ar.seconds_since_update) < 10) {
                summaryItems[idx].alleleReport = ar
            } else {
                summaryItems.splice(idx, 0, { alleleAssessment: null, alleleReport: ar })
            }
        }

        return summaryItems
    }
)

const sortedAcmgCodes = Compute(
    state`views.workflows.modals.alleleHistory.selectedMode`,
    state`views.workflows.modals.alleleHistory.selected`,
    state`app.config`,
    (selectedMode, selected, config) => {
        if (selectedMode !== 'classification') {
            return []
        }

        if (!(selected && selected.evaluation.acmg)) {
            return []
        }

        const includedAcmgCopies = selected.evaluation.acmg.included.map((i) => deepCopy(i))
        // Order by pathogenicity and strength
        const sortedIncludedAcmgCopies = sortCodesByTypeStrength(includedAcmgCopies, config)
        return sortedIncludedAcmgCopies.pathogenic
            .concat(sortedIncludedAcmgCopies.benign)
            .concat(sortedIncludedAcmgCopies.other)
    }
)

app.component('alleleHistory', {
    templateUrl: 'alleleHistory.ngtmpl.html',
    controller: connect(
        {
            alleleAssessments: state`views.workflows.modals.alleleHistory.data.alleleassessments`,
            selectedMode: state`views.workflows.modals.alleleHistory.selectedMode`,
            selected: state`views.workflows.modals.alleleHistory.selected`,
            alleleReports: state`views.workflows.modals.alleleHistory.data.allelereports`,
            sortedAcmgCodes,
            summaryItems: combinedAssessmentsReport,
            selectedModeChanged: signal`views.workflows.modals.alleleHistory.selectedModeChanged`,
            selectedChanged: signal`views.workflows.modals.alleleHistory.selectedChanged`,
            dismissClicked: signal`views.workflows.modals.alleleHistory.dismissClicked`
        },
        'alleleHistory',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    close() {
                        $ctrl.dismissClicked()
                    },
                    formatDate(aa) {
                        return new Date(aa.date_created).toISOString().split('T')[0]
                    },
                    formatSelection(element) {
                        let selection = `${$ctrl.formatDate(element)}: `

                        if ($ctrl.selectedMode === 'classification') {
                            selection += `Class ${element.classification} by ${element.user.abbrev_name} on ${element.genepanel_name}_${element.genepanel_version}`
                        } else {
                            selection += `Report changed by ${element.user.abbrev_name}`
                        }
                        return selection
                    },
                    getDropdownItems() {
                        if ($ctrl.selectedMode === 'classification') {
                            return $ctrl.alleleAssessments
                        } else {
                            return $ctrl.alleleReports
                        }
                    }
                })
            }
        ]
    )
})
