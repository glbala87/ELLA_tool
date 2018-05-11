import { sequence } from 'cerebral'
import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanels from '../actions/getGenepanels'
import getGenepanel from '../actions/getGenepanel'
import toastr from '../../../../../common/factories/toastr'
import loadSelectedGenepanel from './loadSelectedGenepanel'
import loadDefaultGenepanel from './loadDefaultGenepanel'
import prepareAddedGenepanel from '../actions/prepareAddedGenepanel'
import setDefaultSelectedGenepanel from '../actions/setDefaultSelectedGenepanel'

export default sequence('loadImport', [
    getGenepanels,
    {
        success: [
            set(state`views.overview.import.data.genepanels`, props`result`),
            setDefaultSelectedGenepanel
        ],
        error: [toastr('error', 'Failed to load genepanels')]
    }
])
