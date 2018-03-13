import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import setVerificationStatus from '../actions/setVerificationStatus'
import setDirty from '../interpretation/actions/setDirty'

export default [
    setDirty,
    setVerificationStatus
]
