import { set, equals, when } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import toast from '../../../../../../common/factories/toast'
import setDefaultSelection from '../sequences/setDefaultSelection'
import searchReferences from '../actions/searchReferences'

const setSelectionValue = [
    when(props`value`, (x) => x !== undefined),
    {
        true: [
            set(state`views.workflows.modals.addReferences.selection.${props`key`}`, props`value`)
        ],
        false: []
    }
]

export default [
    equals(props`key`),
    {
        referenceMode: [
            set(state`views.workflows.modals.addReferences.${props`key`}`, props`value`),
            setDefaultSelection
        ],
        searchPhrase: [
            setSelectionValue,
            set(props`perPage`, state`views.workflows.modals.addReferences.maxSearchResults`),
            searchReferences,
            {
                success: [
                    set(
                        state`views.workflows.modals.addReferences.selection.searchResults`,
                        props`result`
                    )
                ],
                error: [toast('error', 'Failed to fetch search results', 10000)]
            }
        ],
        otherwise: [setSelectionValue]
    }
]
