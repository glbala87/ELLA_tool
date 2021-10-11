import { toggle } from 'cerebral/operators'
import { props, state } from 'cerebral/tags'

export default [toggle(state`views.overview.import.user.jobData.${props`index`}.collapsed`)]
