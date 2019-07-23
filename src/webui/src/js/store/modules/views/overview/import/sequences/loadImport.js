import { sequence, parallel } from 'cerebral'
import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanels from '../actions/getGenepanels'
import toast from '../../../../../common/factories/toast'
import setDefaultSelectedGenepanel from '../actions/setDefaultSelectedGenepanel'
import loadImportJobs from './loadImportJobs'

export default sequence('loadImport', [
    getGenepanels,
    {
        success: [
            set(state`views.overview.import.data.genepanels`, props`result`),
            setDefaultSelectedGenepanel
        ],
        error: [toast('error', 'Failed to load genepanels')]
    },
    loadImportJobs
])
