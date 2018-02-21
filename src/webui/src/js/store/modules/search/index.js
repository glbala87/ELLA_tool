import { Module } from 'cerebral'

import queryChanged from './signals/queryChanged'
import optionsSearchChanged from './signals/optionsSearchChanged'

export default Module({
    state: {
        query: {
            freetext: null,
            gene: null,
            user: null,
            filter: false
        },
        options: {
            genepanel: null,
            user: null
        },
        results: null,
        loading: false
    },
    signals: {
        optionsSearchChanged,
        queryChanged
    }
})
