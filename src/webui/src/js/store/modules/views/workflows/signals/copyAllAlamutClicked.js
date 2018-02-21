import toastr from '../../../../common/factories/toastr'
import copyAllAlamut from '../actions/copyAllAlamut'

export default [copyAllAlamut, toastr('info', `Copied all variants to clipboard`)]
