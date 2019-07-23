import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { signal, state, props } from 'cerebral/tags'
import template from './importList.ngtmpl.html'

app.component('importList', {
    templateUrl: 'importList.ngtmpl.html',
    bindings: {
        storePath: '<' // Path to import jobs in store
    },
    controller: connect(
        {
            jobs: state`${props`storePath`}`,
            resetImportJobClicked: signal`views.overview.import.resetImportJobClicked`
        },
        'ImportList',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    getJobDisplayType(job) {
                        if (job.sample_id) {
                            return 'Create new analysis from sample'
                        } else if (
                            job.mode === 'Analysis' &&
                            job.properties.create_or_append === 'Create'
                        ) {
                            return 'Create new analysis'
                        } else if (
                            job.mode === 'Analysis' &&
                            job.properties.create_or_append === 'Append'
                        ) {
                            return 'Append to analysis'
                        } else if (job.mode === 'Variants') {
                            return 'Independent variants'
                        }
                    },
                    getJobDisplayDetail(job) {
                        if (job.sample_id) {
                            return `${job.sample_id} (${job.genepanel_name}_${
                                job.genepanel_version
                            })`
                        } else if (
                            job.mode === 'Analysis' &&
                            job.properties.create_or_append === 'Create'
                        ) {
                            return `${job.properties.analysis_name} (${job.genepanel_name}_${
                                job.genepanel_version
                            })`
                        } else if (
                            job.mode === 'Analysis' &&
                            job.properties.create_or_append === 'Append'
                        ) {
                            return `${job.properties.analysis_name}`
                        } else if (job.mode === 'Variants') {
                            return `${job.genepanel_name}_${job.genepanel_version}`
                        }
                    }
                })
            }
        ]
    )
})
