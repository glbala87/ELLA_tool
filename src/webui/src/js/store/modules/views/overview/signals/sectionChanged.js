import { set } from 'cerebral/operators'
import { state, props, string } from 'cerebral/tags'
import { redirect } from '@cerebral/router/operators'

export default [redirect(string`/overview/${props`section`}`)]
