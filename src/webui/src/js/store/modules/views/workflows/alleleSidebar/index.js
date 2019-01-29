import { Module } from 'cerebral'
import alleleRowClicked from './signals/alleleRowClicked'
import reviewedClicked from './signals/reviewedClicked'
import orderByChanged from './signals/orderByChanged'
import toggleExpanded from './signals/toggleExpanded'
import quickClassificationClicked from './signals/quickClassificationClicked'
import filterconfigChanged from './signals/filterconfigChanged'

export default Module({
    state: {},
    signals: {
        alleleRowClicked,
        reviewedClicked,
        orderByChanged,
        toggleExpanded,
        quickClassificationClicked,
        filterconfigChanged
    }
})
