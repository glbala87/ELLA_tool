import app from '../../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state } from 'cerebral/tags'
import { Compute } from 'cerebral'

import shouldShowSidebar from '../../store/modules/views/workflows/alleleSidebar/computed/shouldShowSidebar'
import template from './interpretation.ngtmpl.html'

app.component('interpretation', {
    templateUrl: 'interpretation.ngtmpl.html',
    controller: connect(
        {
            config: state`app.config`,
            sectionKeys: state`views.workflows.components.${state`views.workflows.selectedComponent`}.sectionKeys`,
            selectedComponent: state`views.workflows.selectedComponent`,
            showSidebar: shouldShowSidebar,
            selectedClassificationType: state`views.workflows.alleleSidebar.classificationType`,
            selectedAllele: state`views.workflows.selectedAllele`,
            hasAlleles: Compute(state`views.workflows.interpretation.data.alleles`, (alleles) => {
                if (!alleles) {
                    return
                }
                return Object.keys(alleles).length
            })
        },
        'Interpretation',
        [
            '$scope',
            '$element',
            ($scope, $element) => {
                const $ctrl = $scope.$ctrl
                $ctrl.offsetTop = '0px'
                // Offset top is dynamic due to changing nav bar height.
                // Needs to be set correctly on max-height of child elements to make scrollbar correct.
                $scope.$watch(
                    () => {
                        // The two variables that can change the navbar height are selected
                        // component and selected allele
                        return `${$ctrl.selectedComponent},${$ctrl.selectedAllele}`
                    },
                    () => {
                        // We need to wait until Angular/browser is done with it's digest/rendering
                        // so that the UI is updated with new height
                        // (yes, it's not pretty, but it works)
                        setTimeout(() => {
                            $scope.$applyAsync(() => {
                                $ctrl.offsetTop = $element.prop('offsetTop')
                            })
                        }, 0)
                    }
                )
            }
        ]
    )
})
