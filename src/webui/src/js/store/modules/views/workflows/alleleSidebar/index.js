import { Module } from 'cerebral'
import alleleRowClicked from './signals/alleleRowClicked'
import orderByChanged from './signals/orderByChanged'
import toggleExpanded from './signals/toggleExpanded'
import quickClassificationClicked from './signals/quickClassificationClicked'

export default Module({
    state: {},
    signals: {
        alleleRowClicked,
        orderByChanged,
        toggleExpanded,
        quickClassificationClicked
    }
})
