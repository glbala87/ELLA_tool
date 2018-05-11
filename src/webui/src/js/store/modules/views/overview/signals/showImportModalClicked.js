import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import showImportModal from '../actions/showImportModal'

export default [
    showImportModal,
    {
        result: [],
        dismissed: []
    }
]
