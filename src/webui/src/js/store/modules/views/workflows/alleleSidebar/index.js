import { Module } from 'cerebral'
import selectedAlleleChanged from './signals/selectedAlleleChanged'
import orderByChanged from './signals/orderByChanged'

export default Module({
    state: {},
    signals: {
        selectedAlleleChanged,
        orderByChanged
    }
})
