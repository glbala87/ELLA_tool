/* jshint esnext: true */

import { connect } from '@cerebral/angularjs'
import { Compute } from 'cerebral'
import { state, props } from 'cerebral/tags'
import { ImportData, isSelectionComplete } from '../../model/importdata'
import app from '../../ng-decorators'
import { timeString } from '../../util'
import template from './importSingle.ngtmpl.html' // eslint-disable-line no-unused-vars
const genotypeAvailable = (importkey) => {
    return Compute(importkey, state`views.overview.import.jobData`, (importkey, jobData) => {
        console.log('checking genotype available')
        if (jobData === undefined) {
            return false
        }
        console.log('checking genotype available: jobData defined')

        const thisJobData = jobData[importkey]
        for (let i in thisJobData.parsedInput.variantDataLines) {
            if (
                thisJobData.selection.include[i] &&
                !thisJobData.parsedInput.variantDataLines[i].hasGenotype
            ) {
                console.log(i)
                console.log(thisJobData.parsedInput.variantDataLines[i])
                console.log(thisJobData.selection.include[i])
                return false
            }
        }

        return true
    })
}

app.component('importsingle', {
    bindings: {
        importkey: '='
        // jobData: '=' // Needs to be passed, otherwise it will for some reason be 'undefined' in connect if fetched through the connect-function
    },
    templateUrl: 'importSingle.ngtmpl.html',
    controller: connect(
        {
            jobData: state`views.overview.import.jobData.${props`importkey`}`,
            defaultImportGenepanel: state`app.user.group.default_import_genepanel`,
            genepanels: state`app.user.group.genepanels`,
            priorityDisplay: state`app.config.analysis.priority.display`,
            genotypeAvailable: genotypeAvailable(props`importkey`),
            isSelectionComplete: isSelectionComplete(props`importKey`)
            // isAnalysisMode,
            // isCreateNewAnalysisType,
            // isAppendToAnalysisType
        },
        'importsingle',
        [
            '$scope',
            'cerebral',
            ($scope, cerebral) => {
                const $ctrl = $scope.$ctrl
                console.log('importkey', $ctrl.importkey)

                $ctrl.analysisResource = (q, per_page) => {
                    return cerebral.controller.module.providers.http.definition.get(
                        `analyses/?q=${encodeURIComponent(JSON.stringify(q))}&per_page=${per_page}`
                    )
                }

                $ctrl.editMode = true
                // return

                // $scope.$watch(
                //     () => $ctrl.jobData.selection.analysisName,
                //     () => {
                //         $ctrl.findExistingAnalysis()
                //     }
                // )

                // $scope.$watch(
                //     () => $ctrl.jobData.selection.analysis,
                //     () => $ctrl.checkAnalysisStatus()
                // )

                Object.assign($ctrl, {
                    isAnalysisType: () => {
                        return $ctrl.jobData && $ctrl.jobData.selection.type === 'Analysis'
                    },

                    isCreateNewAnalysisType: () => {
                        return $ctrl.isAnalysisType() && $ctrl.jobData.selection.mode === 'Create'
                    },

                    isAppendToAnalysisType: () => {
                        return $ctrl.isAnalysisType() && $ctrl.jobData.selection.mode === 'Append'
                    },

                    isVariantType: () => {
                        return $ctrl.jobData && $ctrl.jobData.selection.type === 'Variants'
                    },

                    toggleEditMode: () => {
                        $ctrl.editMode = !$ctrl.editMode
                    },

                    setDefaultChoices: () => {
                        return
                        // If some or all variants miss genotype, we can not import this to an analysis.
                        // Set default mode to variants.
                        // if ($ctrl.warnings.noGenotype.active) {
                        //     $ctrl.jobData.selection.mode = 'Variants'
                        // } else {
                        //     $ctrl.jobData.selection.mode = 'Analysis'
                        // }

                        $ctrl.jobData.selection.genepanel = $ctrl.defaultImportGenepanel
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

                        $ctrl.jobData.selection.analysisName = fileNameBase
                        p.then((matchingAnalyses) => {
                            console.log(matchingAnalyses)
                            if (matchingAnalyses.length === 1) {
                                $ctrl.jobData.selection.type = 'Append'
                                $ctrl.jobData.selection.analysis = matchingAnalyses[0]
                            } else {
                                $ctrl.warnings.multipleAnalyses.active = matchingAnalyses.length > 1
                                $ctrl.jobData.selection.type = 'Create'
                            }
                        })
                    },

                    getSummary: () => {
                        if (!$ctrl.jobData) {
                            return {}
                        }
                        let summary = {}
                        if ($ctrl.jobData.selection.type === 'Variants') {
                            summary['mode'] = 'Independent variants'
                            summary['gene panel'] = $ctrl.jobData.selection.genepanel
                                ? `${$ctrl.jobData.selection.genepanel.name} ${$ctrl.jobData.selection.genepanel.version}`
                                : ''
                        } else {
                            // type === 'Analysis'
                            if ($ctrl.jobData.selection.mode === 'Create') {
                                summary['mode'] = 'Create new analysis'
                                summary['analysis name'] = $ctrl.jobData.selection.analysisName
                                summary['gene panel'] = $ctrl.jobData.selection.genepanel
                                    ? `${$ctrl.jobData.selection.genepanel.name} ${$ctrl.jobData.selection.genepanel.version}`
                                    : ''
                            } else {
                                // mode === 'Append'
                                summary['mode'] = 'Append to analysis'
                                summary['analysis'] = $ctrl.jobData.selection.analysis
                                    ? $ctrl.jobData.selection.analysis.name
                                    : ''
                            }
                        }

                        summary['technology'] = $ctrl.jobData.selection.technology

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
                    warnings: () => {
                        const warnings = []
                        if (!$ctrl.genotypeAvailable) {
                            warnings.push(
                                'No genotype found for some or all variants. Can only import as independent variants.'
                            )
                        }

                        if ($ctrl.isCreateNewAnalysisType && $ctrl.findExistingAnalysis()) {
                            warnings.push(
                                'The analysis name matches one or more existing analysis names. Do you really want to create a new analysis? If not, please choose "Append" instead.`'
                            )
                        }

                        if ($ctrl.isAnalysisType() && false) {
                            //$ctrl.matchingAnalyses.length > 1) {
                            warnings.push('Multiple analyses matching filename')
                        }

                        // $ctrl.warnings = () => {
                        //     return {
                        //         noGenotype: {
                        //             text:
                        //                 'No genotype found for some or all variants. Can only import as independent variants.',
                        //             active: () => !$ctrl.genotypeAvailable,
                        //             show: () => {
                        //                 return true
                        //             }
                        //         },
                        //         multipleAnalyses: {
                        //             text: 'Multiple analyses matching filename',
                        //             active: () => false,
                        //             show: () => {
                        //                 return $ctrl.isAnalysisMode()
                        //             }
                        //         },
                        //         analysisNameMatch: {
                        //             text:
                        //                 'The analysis name matches one or more existing analysis names. Do you really want to create a new analysis? If not, please choose "Append" instead.`',
                        //             active: () => false,
                        //             show: () => {
                        //                 return $ctrl.isCreateNewAnalysisType()
                        //             }
                        //         },
                        //         analysisStarted: {
                        //             text: null,
                        //             active: () => false,
                        //             show: () => {
                        //                 return $ctrl.isAppendToAnalysisType()
                        //             }
                        //         }
                        //     }
                        // }
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
                        if (!$ctrl.jobData.selection.analysis) return false
                        else {
                            let statuses = $ctrl.jobData.selection.analysis.interpretations.map(
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
                            $ctrl.jobData.selection.analysis.interpretations[
                                $ctrl.jobData.selection.analysis.interpretations.length - 1
                            ]
                        let statuses = $ctrl.jobData.selection.analysis.interpretations.map(
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
                            !$ctrl.jobData.selection.analysisName ||
                            $ctrl.jobData.selection.analysisName.length < 5
                        ) {
                            return false
                        }
                        let p_name = $ctrl.analysisResource(
                            {
                                name: {
                                    $ilike: `%${$ctrl.jobData.selection.analysisName}%`
                                }
                            },
                            2
                        )

                        // Extract longest substring of digits
                        let subnumber = ''
                        let re = /\d+/g
                        let m = null
                        do {
                            m = re.exec($ctrl.jobData.selection.analysisName)
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
                        return Promise.all([p_name, p_number]).then((result) => {
                            const matchingName = result[0].result
                            const matchingNumber = result[1].result

                            return matchingName.length > 0 || matchingNumber.length > 0
                        })
                    },
                    getImportButtonText: () => {
                        return $ctrl.editMode ? 'Import' : 'Import triggered'
                    }
                    // Import selection
                })
                $ctrl.setDefaultChoices()
            }
        ]
    )
})
