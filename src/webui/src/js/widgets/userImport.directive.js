import app from '../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, signal, props } from 'cerebral/tags'
import { ImportData, getParsedInput, getSplitInput } from '../model/importdata'
import template from './userImport.ngtmpl.html' // eslint-disable-line no-unused-vars

const genotypeAvailable = Compute(state`views.overview.import.user.jobData`, (jobData, resolve) => {
    if (jobData === undefined) {
        return null
    }
    return jobData.map((jd) => {
        for (let i in jd.parsedInput.variantDataLines) {
            if (jd.selection.include[i] && !jd.parsedInput.variantDataLines[i].hasGenotype) {
                return false
            }
            return true
        }
    })
})

export const isSelectionComplete = Compute(state`views.overview.import.user.jobData`, (jobData) => {
    if (jobData === undefined) {
        return null
    }

    return jobData.map((jd) => {
        let a = jd.selection.type === 'Variants' && jd.selection.genepanel
        let b =
            jd.selection.type === 'Analysis' &&
            jd.selection.mode === 'Create' &&
            jd.selection.analysisName &&
            jd.selection.genepanel
        let c =
            jd.selection.type === 'Analysis' &&
            jd.selection.mode === 'Append' &&
            jd.selection.analysis
        let d = Object.values(jd.selection.include).filter((c) => c).length

        return Boolean((a || b || c) && d)
    })
})

const summary = Compute(state`views.overview.import.user.jobData`, (jobData) => {
    if (!jobData) {
        return null
    }
    return jobData.map((jd) => {
        const summary = {}
        if (jd.selection.type === 'Variants') {
            summary['mode'] = 'Independent variants'
            summary['gene panel'] = jd.selection.genepanel
                ? `${jd.selection.genepanel.name} ${jd.selection.genepanel.version}`
                : ''
        } else {
            // type === 'Analysis'
            if (jd.selection.mode === 'Create') {
                summary['mode'] = 'Create new analysis'
                summary['analysis name'] = jd.selection.analysisName
                summary['gene panel'] = jd.selection.genepanel
                    ? `${jd.selection.genepanel.name} ${jd.selection.genepanel.version}`
                    : ''
            } else {
                // mode === 'Append'
                summary['mode'] = 'Append to analysis'
                summary['analysis'] = jd.selection.analysis ? jd.selection.analysis.name : ''
            }
        }

        summary['technology'] = jd.selection.technology
        return summary
    })
})

const isOfTypeAndMode = (type, mode) => {
    return Compute(type, mode, state`views.overview.import.user.jobData`, (type, mode, jobData) => {
        return jobData.map((jd) => {
            if (mode) {
                return jd.selection.type === type && jd.selection.mode === mode
            } else {
                return jd.selection.type === type
            }
        })
    })
}

const warnings = Compute(state`views.overview.import.user.jobData`, (jobData, resolve) => {
    if (!jobData) {
        return null
    }
    const _genotypeAvailable = resolve(genotypeAvailable)
    return jobData.map((jd, i) => {
        let warnings = []
        let a = jd.selection.type === 'Variants' && jd.selection.genepanel
        let b =
            jd.selection.type === 'Analysis' &&
            jd.selection.mode === 'Create' &&
            jd.selection.analysisName &&
            jd.selection.genepanel
        let c =
            jd.selection.type === 'Analysis' &&
            jd.selection.mode === 'Append' &&
            jd.selection.analysis
        let d = Object.values(jd.selection.include).filter((c) => c).length

        const selectionComplete = Boolean((a || b || c) && d)
        if (!selectionComplete) {
            warnings.push('Selection is incomplete')
        }

        if (!_genotypeAvailable[i]) {
            warnings.push('Genotype(s) unavailable')
        }

        return warnings

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
    })
})

app.component('userImport', {
    templateUrl: 'userImport.ngtmpl.html',
    controller: connect(
        {
            jobData: state`views.overview.import.user.jobData`,
            defaultImportGenepanel: state`app.user.group.default_import_genepanel`,
            genepanels: state`app.user.group.genepanels`,
            priorityDisplay: state`app.config.analysis.priority.display`,
            genotypeAvailable,
            isSelectionComplete,
            isAnalysisType: isOfTypeAndMode('Analysis', null),
            isVariantType: isOfTypeAndMode('Variants', null),
            isCreateNewAnalysisType: isOfTypeAndMode('Analysis', 'Create'),
            isAppendToAnalysisType: isOfTypeAndMode('Analysis', 'Append'),
            warnings,
            summary,
            toggleCollapsed: signal`views.overview.import.user.toggleCollapsed`,
            jobDataChanged: signal`views.overview.import.user.jobDataChanged`,
            selectionChanged: signal`views.overview.import.user.selectionChanged`,
            updateAnalysisOptions: signal`views.overview.import.user.updateAnalysisOptions`
        },
        'UserImport',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
                    // Wrapper for updating analysis options
                    // selector 'remote' expects a promise returned
                    updateAnalysisOptionsWrapper: (index, search) => {
                        $ctrl.updateAnalysisOptions({ index, search })
                        return Promise.resolve([])
                    }
                })
            }
        ]
    )
})
