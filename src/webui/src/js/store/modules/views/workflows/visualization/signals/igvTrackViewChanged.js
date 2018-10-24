import { set, when, toggle } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import showHideTrack from '../actions/showHideTrack'
import updateIgvTracks from '../actions/updateIgvTracks'

export default [showHideTrack, updateIgvTracks]
