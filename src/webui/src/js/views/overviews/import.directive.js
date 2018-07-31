import app from '../../ng-decorators'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './import.ngtmpl.html'

const addedCount = Compute(state`views.overview.import.added.addedGenepanel`, (addedGenepanel) => {
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
    state`views.overview.import.added.addedGenepanel`,
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
    state`views.overview.import.added.addedGenepanel`,
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
    template,
    controller: connect(
        {
            canImport,
            addedCount,
            displayGenepanelName,
            customGenepanel: state`views.overview.import.customGenepanel`,
            selectedSample: state`views.overview.import.selectedSample`,
            samples: state`views.overview.import.data.samples`,
            selectedGenepanel: state`views.overview.import.selectedGenepanel`,
            genepanels: state`views.overview.import.data.genepanels`,
            samplesSearchChanged: signal`views.overview.import.samplesSearchChanged`,
            selectedGenepanelChanged: signal`views.overview.import.selectedGenepanelChanged`,
            sampleSelected: signal`views.overview.import.sampleSelected`,
            customGenepanelSelected: signal`views.overview.import.customGenepanelSelected`,
            importClicked: signal`views.overview.import.importClicked`
        },
        'Import',
        [
            '$scope',
            ($scope) => {
                const $ctrl = $scope.$ctrl
                Object.assign($ctrl, {
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
                    }
                })
            }
        ]
    )
})
