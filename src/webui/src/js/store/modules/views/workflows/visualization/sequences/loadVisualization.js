import { sequence } from 'cerebral'
import prepareIgv from '../actions/prepareIgv'
import updateIgvTracks from '../actions/updateIgvTracks'

export default sequence('loadVisualization', [prepareIgv, updateIgvTracks])
