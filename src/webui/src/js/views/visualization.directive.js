/* jshint esnext: true */

import app from '../ng-decorators'
import { connect } from '@cerebral/angularjs'
import { state, signal } from 'cerebral/tags'
import template from './visualization.ngtmpl.html'

app.component('visualization', {
    templateUrl: 'visualization.ngtmpl.html',
    controller: connect(
        {
            igvLocus: state`views.workflows.visualization.igv.locus`,
            igvTracks: state`views.workflows.visualization.igv.tracks`,
            igvReference: state`views.workflows.visualization.igv.reference`,
            tracks: state`views.workflows.visualization.tracks`,
            shownTracksChanged: signal`views.workflows.visualization.igvTrackViewChanged`
        },
        'Visualization'
    )
})
