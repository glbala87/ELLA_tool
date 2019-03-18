import { Module } from 'cerebral'

import queryChanged from './signals/queryChanged'
import optionsSearchChanged from './signals/optionsSearchChanged'
import modals from './modals'

export default Module({
    state: {
        query: {
            freetext: null,
            gene: null,
            user: null
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
    },
    modules: {
        modals
    }
})
