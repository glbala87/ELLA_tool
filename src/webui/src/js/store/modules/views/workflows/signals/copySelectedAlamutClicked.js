import toastr from '../../../../common/factories/toastr'
import copySelectedAlamut from '../actions/copySelectedAlamut'

export default [copySelectedAlamut, toastr('info', `Copied selected variant to clipboard`)]
