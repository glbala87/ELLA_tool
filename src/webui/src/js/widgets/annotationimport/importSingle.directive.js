/* jshint esnext: true */

import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import { ImportData } from '../../model/importdata'
import app from '../../ng-decorators'
import { timeString } from '../../util'
import template from './importSingle.ngtmpl.html' // eslint-disable-line no-unused-vars

app.component('importsingle', {
    bindings: {
        index: '<',
        jobData: '=' // Needs to be passed, otherwise it will initalize with 'undefined' if fetched through the connect-function
    },
    templateUrl: 'importSingle.ngtmpl.html',
    controller: connect(
        {
            defaultImportGenepanel: state`app.user.group.default_import_genepanel`,
            genepanels: state`app.user.group.genepanels`,
            priorityDisplay: state`app.config.analysis.priority.display`
        },
        'importsingle',
        [
            '$scope',
            'cerebral',
            ($scope, cerebral) => {
                const $ctrl = $scope.$ctrl

                $ctrl.analysisResource = (q, per_page) => {
                    return cerebral.controller.module.providers.http.definition.get(
                        `analyses/?q=${encodeURIComponent(JSON.stringify(q))}&per_page=${per_page}`
                    )
                }

                $ctrl.analysisResource({ name: { $ilike: `%NA12878%` } }, 2).then((result) => {
                    console.log(result)
                })
                $ctrl.analysisResource({ name: { $ilike: `%%` } }, 2).then((result) => {
                    console.log(result)
                })
                $ctrl.analysisResource({ name: { $ilike: `%%` } }, 20).then((result) => {
                    console.log(result)
                })

                $ctrl.editMode = true

                $ctrl.importData = new ImportData($ctrl.jobData)
                $ctrl.warnings = {
                    noGenotype: {
                        text:
                            'No genotype found for some or all variants. Can only import as independent variants.',
                        active: !$ctrl.importData.genotypeAvailable(),
                        show: () => {
                            return true
                        }
                    },
                    multipleAnalyses: {
                        text: 'Multiple analyses matching filename',
                        active: false,
                        show: () => {
                            return $ctrl.importData.isAnalysisMode()
                        }
                    },
                    analysisNameMatch: {
                        text:
                            'The analysis name matches one or more existing analysis names. Do you really want to create a new analysis? If not, please choose "Append" instead.`',
                        active: false,
                        show: () => {
                            return $ctrl.importData.isCreateNewAnalysisType()
                        }
                    },
                    analysisStarted: {
                        text: null,
                        active: false,
                        show: () => {
                            return $ctrl.importData.isAppendToAnalysisType()
                        }
                    }
                }

                $scope.$watch(
                    () => $ctrl.importData.importSelection.analysisName,
                    () => {
                        console.log('finding existing analyses')
                        $ctrl.findExistingAnalysis()
                    }
                )

                $scope.$watch(
                    () => $ctrl.importData.importSelection.analysis,
                    () => $ctrl.checkAnalysisStatus()
                )

                Object.assign($ctrl, {
                    toggleEditMode: () => {
                        $ctrl.editMode = !$ctrl.editMode
                    },
                    setDefaultChoices: () => {
                        // If some or all variants miss genotype, we can not import this to an analysis.
                        // Set default mode to variants.
                        if ($ctrl.warnings.noGenotype.active) {
                            $ctrl.importData.importSelection.mode = 'Variants'
                        } else {
                            $ctrl.importData.importSelection.mode = 'Analysis'
                        }

                        $ctrl.importData.importSelection.genepanel = $ctrl.defaultImportGenepanel
                            ? $ctrl.defaultImportGenepanel
                            : null
                        let fileNameBase = $ctrl.importData.getFileNameBase()

                        // Search for matching analysis
                        if (fileNameBase.length > 3) {
                            var p = $ctrl.analysisResource(
                                { name: { $ilike: `%${fileNameBase}%` } },
                                2
                            )
                        } else {
                            var p = new Promise((resolve) => {
                                resolve([])
                            })
                        }
                        console.log(p)

                        $ctrl.importData.importSelection.analysisName = fileNameBase
                        p.then((matchingAnalyses) => {
                            console.log(matchingAnalyses)
                            if (matchingAnalyses.length === 1) {
                                $ctrl.importData.importSelection.type = 'Append'
                                $ctrl.importData.importSelection.analysis = matchingAnalyses[0]
                            } else {
                                $ctrl.warnings.multipleAnalyses.active = matchingAnalyses.length > 1
                                $ctrl.importData.importSelection.type = 'Create'
                            }
                        })
                    },

                    getSummary: () => {
                        let summary = {}
                        if ($ctrl.importData.isVariantMode()) {
                            summary['mode'] = 'Independent variants'
                            summary['gene panel'] = $ctrl.importData.importSelection.genepanel
                                ? `${$ctrl.importData.importSelection.genepanel.name} ${$ctrl.importData.importSelection.genepanel.version}`
                                : ''
                        } else if ($ctrl.importData.isCreateNewAnalysisType()) {
                            summary['mode'] = 'Create new analysis'
                            summary['analysis name'] = $ctrl.importData.importSelection.analysisName
                            summary['gene panel'] = $ctrl.importData.importSelection.genepanel
                                ? `${$ctrl.importData.importSelection.genepanel.name} ${$ctrl.importData.importSelection.genepanel.version}`
                                : ''
                        } else if ($ctrl.importData.isAppendToAnalysisType()) {
                            summary['mode'] = 'Append to analysis'
                            summary['analysis'] = $ctrl.importData.importSelection.analysis
                                ? $ctrl.importData.importSelection.analysis.name
                                : ''
                        }

                        summary['technology'] = $ctrl.importData.importSelection.technology

                        return summary
                    },

                    updateAnalysisOptions: (text) => {
                        return $ctrl
                            .analysisResource({ name: { $ilike: `%${text}%` } }, 20)
                            .then((analyses) => {
                                console.log(analyses.result)
                                $ctrl.analyses = analyses.result
                                return $ctrl.analyses
                            })
                    },

                    showWarning: (warning) => {
                        return warning.active && warning.show()
                    },

                    /*
                     * Check if selected analysis is started
                     */
                    _analysisInReview: (statuses) => {
                        return (
                            statuses.length > 1 &&
                            statuses[statuses.length - 1] === 'Not started' &&
                            statuses[statuses.length - 2] === 'Done'
                        )
                    },

                    _analysisOngoing: (statuses) => {
                        return statuses[statuses.length - 1] === 'Ongoing'
                    },

                    _analysisDone: (statuses) => {
                        return statuses[statuses.length - 1] === 'Done'
                    },

                    analysisIsStarted: () => {
                        if (!$ctrl.importData.importSelection.analysis) return false
                        else {
                            let statuses = $ctrl.importData.importSelection.analysis.interpretations.map(
                                (i) => i.status
                            )
                            return (
                                $ctrl._analysisDone(statuses) ||
                                $ctrl._analysisOngoing(statuses) ||
                                $ctrl._analysisInReview(statuses)
                            )
                        }
                    },

                    checkAnalysisStatus: () => {
                        if (!$ctrl.analysisIsStarted()) {
                            $ctrl.warnings.analysisStarted.active = false
                            $ctrl.warnings.analysisStarted.text = null
                            return
                        }
                        let last_interpretation =
                            $ctrl.importData.importSelection.analysis.interpretations[
                                $ctrl.importData.importSelection.analysis.interpretations.length - 1
                            ]
                        let statuses = $ctrl.importData.importSelection.analysis.interpretations.map(
                            (i) => i.status
                        )
                        let s = 'Analysis is '
                        if ($ctrl._analysisDone(statuses)) {
                            s += 'finalized. Appending to this analyses will reopen it.'
                        } else if ($ctrl._analysisOngoing(statuses)) {
                            s += 'ongoing.'
                        } else if ($ctrl._analysisInReview(statuses)) {
                            s += 'in review.'
                        }

                        s += ' ('
                        if (last_interpretation.user) {
                            s += `${last_interpretation.user.abbrev_name}, `
                        }
                        s += `${timeString(last_interpretation.date_last_update)})`

                        $ctrl.warnings.analysisStarted.active = true
                        $ctrl.warnings.analysisStarted.text = s
                    },

                    /*
                     * Check if there exists an analysis with a similar name
                     */
                    findExistingAnalysis: () => {
                        // Don't match if typed in analysis name is less than 5
                        if (
                            !$ctrl.importData.importSelection.analysisName ||
                            $ctrl.importData.importSelection.analysisName.length < 5
                        ) {
                            $ctrl.warnings.analysisNameMatch.active = false
                            return
                        }
                        let p_name = $ctrl.analysisResource(
                            {
                                name: {
                                    $ilike: `%${$ctrl.importData.importSelection.analysisName}%`
                                }
                            },
                            2
                        )

                        // Extract longest substring of digits
                        let subnumber = ''
                        let re = /\d+/g
                        let m = null
                        do {
                            m = re.exec($ctrl.importData.importSelection.analysisName)
                            if (m && m[0].length > subnumber.length) {
                                subnumber = m[0]
                            }
                        } while (m)

                        // Don't match on subnumber if length < 5
                        subnumber = '' + subnumber
                        if (subnumber.length < 5) {
                            var p_number = new Promise((resolve) => {
                                resolve({ result: [] })
                            })
                        } else {
                            var p_number = $ctrl.analysisResource(
                                { name: { $like: `%${subnumber}%` } },
                                2
                            )
                        }

                        // Try to match against existing analyses, based on either full string or subnumber
                        Promise.all([p_name, p_number]).then((result) => {
                            const matchingName = result[0].result
                            const matchingNumber = result[1].result

                            $ctrl.warnings.analysisNameMatch.active =
                                matchingName.length > 0 || matchingNumber.length > 0
                        })
                    },
                    getImportButtonText: () => {
                        return $ctrl.editMode ? 'Import' : 'Import triggered'
                    }
                })
                $ctrl.setDefaultChoices()
            }
        ]
    )
})
