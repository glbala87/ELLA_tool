import { Module } from 'cerebral'
import alleleRowClicked from './signals/alleleRowClicked'
import alleleRowToggled from './signals/alleleRowToggled'
import reviewedClicked from './signals/reviewedClicked'
import orderByChanged from './signals/orderByChanged'
import classificationTypeChanged from './signals/classificationTypeChanged'
import callerTypeSelectedChanged from './signals/callerTypeSelectedChanged'
import quickClassificationClicked from './signals/quickClassificationClicked'
import filterconfigChanged from './signals/filterconfigChanged'

export default Module({
    state: {},
    signals: {
        alleleRowClicked,
        alleleRowToggled,
        reviewedClicked,
        orderByChanged,
        classificationTypeChanged,
        callerTypeSelectedChanged,
        quickClassificationClicked,
        filterconfigChanged
    }
})
