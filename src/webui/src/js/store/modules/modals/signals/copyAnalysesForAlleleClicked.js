import { set } from 'cerebral/operators'
import { state, props } from 'cerebral/tags'
import copyAnalysesForAlleleClipboard from '../actions/copyAnalysesForAlleleClipboard'
import toastr from '../../../common/factories/toastr'

export default [copyAnalysesForAlleleClipboard, toastr('info', 'Copied analyses to clipboard')]
