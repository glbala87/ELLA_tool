import { sequence } from 'cerebral'
import { set } from 'cerebral/operators'
import { module, props } from 'cerebral/tags'
import { UUID } from '../../../../util'
import toast from '../../../common/factories/toast'
import getResults from '../actions/getResults'
import checkQuery from '../actions/checkQuery'
import checkSearchId from '../actions/checkSearchId'

export default sequence('loadResults', [
    checkQuery,
    {
        true: [
            // Prevent an earlier search from overwriting our current in-flight search
            // Usually the searches with fewer characters are slower than the ones with more, leading to collisions
            () => {
                return { currentSearchId: UUID() }
            },
            set(module`currentSearchId`, props`currentSearchId`),
            getResults,
            {
                success: [
                    // Check that this signal's props id matches the latest issued one
                    checkSearchId,
                    {
                        true: [set(module`results`, props`result`)],
                        false: [] // Ignore result
                    }
                ],
                error: [toast('error', 'An error occured while searching.')]
            }
        ],
        false: [set(module`results`, null)]
    }
])
