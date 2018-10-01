import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import copyAnalysesForAlleleClipboard from '../actions/copyAnalysesForAlleleClipboard'
import toast from '../../../common/factories/toast'

export default [copyAnalysesForAlleleClipboard, toast('info', 'Copied analyses to clipboard')]
