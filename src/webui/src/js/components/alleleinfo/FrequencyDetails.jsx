import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'
import { connect } from '@cerebral/react'
import { state, props } from 'cerebral/tags'

import {
    ContentBoxTable,
    ContentBoxTableCell,
    ContentBoxTableHeader,
    ContentBoxTableRow,
    ContentBoxTableDataCell,
    ContentBoxWarning
} from '../base'
import getFrequencyAnnotation from '../../store/common/computes/getFrequencyAnnotation'

export const FrequencyDetails = connect(
    {
        frequencies: getFrequencyAnnotation(state`${props`allelePath`}`, props`group`)
    },
    function FrequencyDetails({ frequencies, group }) {
        if (!frequencies) {
            return null
        }

        const filterFailed = frequencies.filter
            ? frequencies.filter.filter((f) => f !== 'PASS')
            : []
        const filterWarning = filterFailed.length ? (
            <ContentBoxWarning>FILTER: {filterFailed.join(',')}</ContentBoxWarning>
        ) : null

        const headerCells = ['pop'].concat(frequencies.fields).map((f) => {
            return <ContentBoxTableHeader key={f}>{f}</ContentBoxTableHeader>
        })

        const freqRows = frequencies.frequencies.map((f) => {
            const freqData = frequencies.fields.map((field) => (
                <ContentBoxTableDataCell key={field}>{f[field]}</ContentBoxTableDataCell>
            ))
            return (
                <ContentBoxTableRow key={f.name}>
                    <ContentBoxTableCell>{f.name}:</ContentBoxTableCell>
                    {freqData}
                </ContentBoxTableRow>
            )
        })

        const indicationsTables = frequencies.indications.map((i) => {
            const indicationsRows = i.indications.map((indValues) => {
                return (
                    <ContentBoxTableRow key={indValues.name}>
                        <ContentBoxTableDataCell>- {indValues.name}:</ContentBoxTableDataCell>
                        <ContentBoxTableDataCell>{indValues.value}</ContentBoxTableDataCell>
                    </ContentBoxTableRow>
                )
            })
            return (
                <ContentBoxTable key={i.name}>
                    <ContentBoxTableRow>
                        <ContentBoxTableCell>{i.name} indications:</ContentBoxTableCell>
                        <ContentBoxTableDataCell />
                    </ContentBoxTableRow>
                    {indicationsRows}
                </ContentBoxTable>
            )
        })

        return (
            <div>
                {filterWarning}
                <ContentBoxTable className={`id-frequency-${group}`}>
                    <ContentBoxTableRow>{headerCells}</ContentBoxTableRow>
                    {freqRows}
                </ContentBoxTable>
                {indicationsTables}
            </div>
        )

        /*<div class="cb-warning" ng-if="$ctrl.getFilterFail().length" >FILTER: {{$ctrl.getFilterFail().join(', ')}}</div>
<div class="cb-table id-frequency-{{ $ctrl.group }}" ng-if="$ctrl.frequencies.frequencies.length > 0">
  <div class="tabular-row">
  <div class="cell"><h4 class="faded-title">Pop</h4></div>
  <div class="cell" ng-repeat="field in $ctrl.frequencies.fields"> <!-- table headers -->
    <h4 class="faded-title">{{field}}</h4>
  </div>
  </div>
  <div class="tabular-row exac" ng-repeat="freqData in $ctrl.frequencies.frequencies">
    <div class="cell"><h5>{{freqData.name}}:</h5></div>
    <div class="cell" ng-repeat="field in $ctrl.frequencies.fields">
      <p>{{freqData[field]}}</p>
    </div>
  </div>
</div>
<div class="cb-table" ng-repeat="indications in $ctrl.frequencies.indications" ng-if="$ctrl.frequencies.indications.length">
  <div class="tabular-row">
    <div class="cell"><h5>{{indications.name}} indications:</h5></div>
    <div class="cell"></div>
  </div>
  <div class="tabular-row" ng-repeat="i in indications.indications">
    <div class="cell"><p>- {{i.name}}:</p></div>
    <div class="cell"><p>{{i.value}}</p></div>
  </div>
  </ng-if>
</div>
*/
    }
)

FrequencyDetails.propTypes = {
    allelePath: PropTypes.string.isRequired,
    group: PropTypes.string.isRequired
}
