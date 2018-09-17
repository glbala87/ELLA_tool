import { sequence } from 'cerebral'
import prepareIGV from '../actions/prepareIGV'
import updateIgvTracks from '../actions/updateIgvTracks'

export default sequence('loadVisualization', [prepareIGV, updateIgvTracks])
