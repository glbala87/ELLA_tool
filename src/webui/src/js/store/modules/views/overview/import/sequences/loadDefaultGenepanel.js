import { set, equals } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import getGenepanel from '../actions/getGenepanel'
import toastr from '../../../../../common/factories/toastr'

export default [
    set(props`genepanelName`, state`app.user.group.default_import_genepanel.name`),
    set(props`genepanelVersion`, state`app.user.group.default_import_genepanel.version`),
    getGenepanel,
    {
        success: [set(state`views.overview.import.data.defaultGenepanel`, props`result`)],
        error: [toastr('error', 'Failed to load default genepanel')]
    }
]
