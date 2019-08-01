import app from '../../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import { UUID } from '../../util'
import { ImportData } from '../../model/importdata'
import template from './import.ngtmpl.html'

const addedCount = Compute(state`views.overview.import.custom.added.addedGenepanel`, (addedGenepanel) => {
    const counts = {
        transcripts: 0,
        genes: 0
    }
    if (!addedGenepanel) {
        return counts
    }
    for (let [key, value] of Object.entries(addedGenepanel.genes)) {
        counts.genes += 1
        counts.transcripts += value.transcripts.length
    }
    return counts
})

const displayGenepanelName = Compute(
    state`views.overview.import.customGenepanel`,
    state`views.overview.import.selectedGenepanel`,
    state`views.overview.import.custom.added.addedGenepanel`,
    (customGenepanel, selectedGenepanel, addedGenepanel) => {
        if (customGenepanel) {
            if (!addedGenepanel) {
                return ''
            }
            return `${addedGenepanel.name}_${addedGenepanel.version}`
        }
        if (!selectedGenepanel) {
            return ''
        }
        return `${selectedGenepanel.name}_${selectedGenepanel.version}`
    }
)

const canImport = Compute(
    state`views.overview.import.customGenepanel`,
    state`views.overview.import.selectedGenepanel`,
    state`views.overview.import.selectedSample`,
    state`views.overview.import.custom.added.addedGenepanel`,
    (customGenepanel, selectedGenepanel, selectedSample, addedGenepanel) => {
        if (!selectedSample) {
            return false
        }
        if (customGenepanel) {
            if (!addedGenepanel) {
                return false
            }
            return (
                addedGenepanel.name &&
                addedGenepanel.name !== '' &&
                Object.keys(addedGenepanel.genes).length
            )
        }
        return Boolean(selectedGenepanel)
    }
)

app.component('import', {
    templateUrl: 'import.ngtmpl.html',
    controller: connect(
        {
            canImport,
            addedCount,
            displayGenepanelName,
            activeImportJobs: state`views.overview.import.data.activeImportJobs`,
            importJobsHistory: state`views.overview.import.data.importJobsHistory`,
            importSourceType: state`views.overview.import.importSourceType`,
            customGenepanel: state`views.overview.import.customGenepanel`,
            selectedSample: state`views.overview.import.selectedSample`,
            samples: state`views.overview.import.data.samples`,
            selectedGenepanel: state`views.overview.import.selectedGenepanel`,
            genepanels: state`views.overview.import.data.genepanels`,
            priority: state`views.overview.import.priority`,
            priorityDisplay: state`app.config.analysis.priority.display`,
            importHistoryPageChanged: signal`views.overview.import.importHistoryPageChanged`,
            samplesSearchChanged: signal`views.overview.import.samplesSearchChanged`,
            selectedGenepanelChanged: signal`views.overview.import.selectedGenepanelChanged`,
            sampleSelected: signal`views.overview.import.sampleSelected`,
            customGenepanelSelected: signal`views.overview.import.customGenepanelSelected`,
            priorityChanged: signal`views.overview.import.priorityChanged`,
            importClicked: signal`views.overview.import.importClicked`,
            importSourceTypeSelected: signal`views.overview.import.importSourceTypeSelected`
        },
        'Import',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl

                Object.assign($ctrl, {
                    jobData: null,
                    userInput: '',
                    sampleSelectedWrapper(newValue) {
                        $ctrl.sampleSelected({
                            selectedSample: newValue ? newValue : null
                        })
                    },
                    searchSamples(search) {
                        $ctrl.samplesSearchChanged({ term: search, limit: 20 })
                        // angular-selector needs a returned Promise, although
                        // we set the options ourselves through cerebral
                        return Promise.resolve([])
                    },
                    parseInput() {
                        const splitInput = {}

                        // Find lines starting with '-'
                        const lines = $ctrl.userInput.split('\n')
                        let currentFile = ''
                        let uuid = null
                        for (let l of lines) {
                            if (l.trim() === '') continue

                            // Check if start of new file
                            if (!uuid || l.startsWith('-')) {
                                uuid = UUID()
                                if (l.startsWith('-')) {
                                    currentFile = l.replace(/-*\s*/g, '')
                                } else {
                                    currentFile = ''
                                }

                                splitInput[uuid] = {
                                    filename: currentFile,
                                    fileContents: ''
                                }

                                // Don't include line in contents if it is a separator line
                                if (l.startsWith('-')) continue
                            }
                            splitInput[uuid].fileContents += l + '\n'
                        }

                        let jobData = {}
                        for (let k in splitInput) {
                            jobData[k] = new ImportData(
                                splitInput[k].filename,
                                splitInput[k].fileContents
                            )
                        }
                        $ctrl.jobData = jobData
                    },
                    revertJobData() {
                        $ctrl.jobData = null
                    },
                    getImportDescription() {
                        let incomplete = 0
                        let createAnalyses = 0
                        let standaloneVariants = 0
                        let appendAnalyses = []
                        let appendVariants = 0

                        for (let j of Object.values($ctrl.jobData)) {
                            if (!j.isSelectionComplete()) {
                                incomplete += 1
                            } else if (j.isCreateNewAnalysisType()) {
                                createAnalyses += 1
                            } else if (j.isAppendToAnalysisType()) {
                                appendAnalyses.push(j.importSelection.analysis.name)
                                appendVariants += Object.values(j.contents.lines).filter(
                                    (l) => l.include
                                ).length
                            } else if (j.isVariantMode()) {
                                standaloneVariants += Object.values(j.contents.lines).filter(
                                    (l) => l.include
                                ).length
                            }
                        }

                        appendAnalyses = new Set(appendAnalyses).size

                        let description = []
                        if (incomplete) {
                            let s = `${incomplete} ${
                                incomplete > 1 ? 'imports' : 'import'
                            } incomplete.`
                            description.push(s)
                        }

                        if (createAnalyses) {
                            let s = `Create ${createAnalyses} new ${
                                createAnalyses > 1 ? 'analyses' : 'analysis'
                            }.`
                            description.push(s)
                        }

                        if (appendAnalyses) {
                            let s = `Append ${appendVariants} ${
                                appendVariants > 1 ? 'variants' : 'variant'
                            } to ${appendAnalyses} existing ${
                                appendAnalyses > 1 ? 'analyses' : 'analysis'
                            }`
                            description.push(s)
                        }

                        if (standaloneVariants) {
                            let s = `Import ${standaloneVariants} standalone ${
                                standaloneVariants > 1 ? 'variants' : 'variant'
                            }`
                            description.push(s)
                        }

                        return description
                    },
                    userImportDisabled() {
                        const allReady = Object.values($ctrl.jobData)
                            .map((j) => j.isSelectionComplete())
                            .every((v) => v)
                        return !allReady
                    },
                    userImportClickedWrapper() {
                        const importJobs = Object.values($ctrl.jobData).map((j) => j.process())
                        $ctrl.importClicked({ importJobs })
                        $ctrl.jobData = null
                        $ctrl.userInput = ''
                    }
                })
            }
        ]
    )
})
