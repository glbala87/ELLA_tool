import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'
import setCollapse from '../actions/setCollapse'
import saveOverviewState from '../actions/saveOverviewState'

export default [setCollapse, saveOverviewState]
