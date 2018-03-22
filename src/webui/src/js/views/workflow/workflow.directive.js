/* jshint esnext: true */

import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { compute } from 'cerebral'

import isReadOnly from '../../store/modules/views/workflows/computed/isReadOnly'

app.component('workflow', {
    templateUrl: 'ngtmpl/workflow.ngtmpl.html',
    controller: connect(
        {
            selectedComponent: state`views.workflows.selectedComponent`,
            components: state`views.workflows.components`,
            analysis: state`views.workflows.data.analysis`,
            allele: state`views.workflows.data.allele`,
            historyInterpretations: state`views.workflows.historyInterpretations`,
            interpretations: state`views.workflows.data.interpretations`,
            selectedInterpretation: state`views.workflows.interpretation.selected`,
            isOngoing: state`views.workflows.interpretation.isOngoing`,
            alleles: state`views.workflows.data.alleles`,
            loaded: state`views.workflows.loaded`,
            readOnly: isReadOnly
        },
        'Workflow',
        [
            '$scope',
            '$filter',
            function($scope, $filter) {
                Object.assign($scope.$ctrl, {
                    showHistory,
                    formatHistoryOption,
                    getExcludedAlleleCount,
                    showComponentDropdown
                })

                function getExcludedAlleleCount() {
                    if ($scope.$ctrl.selectedInterpretation) {
                        return Object.values(
                            $scope.$ctrl.selectedInterpretation.excluded_allele_ids
                        )
                            .map(excluded_group => excluded_group.length)
                            .reduce((total_length, length) => total_length + length)
                    }
                }

                function showHistory() {
                    return $scope.$ctrl.isOngoing && $scope.$ctrl.historyInterpretations.length
                }

                function showComponentDropdown() {
                    return Boolean($scope.$ctrl.components.length > 1)
                }

                function formatHistoryOption(interpretation) {
                    if (interpretation.current) {
                        return 'Current data'
                    }
                    let interpretation_idx =
                        $scope.$ctrl.interpretations.indexOf(interpretation) + 1
                    let interpretation_date = $filter('date')(
                        interpretation.date_last_update,
                        'dd-MM-yyyy HH:mm'
                    )
                    return `${interpretation_idx} • ${interpretation.user.first_name} ${
                        interpretation.user.last_name
                    } • ${interpretation_date}`
                }
            }
        ]
    )
})
