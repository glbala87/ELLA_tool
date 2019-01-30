import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'

export const ContentBoxTable = styled.div`
    display: table;
`

export const ContentBoxTableRow = styled.div`
    display: table-row;
`

export const ContentBoxTableCell = styled.div`
    display: table-cell;
    white-space: nowrap;
    padding-right: 2.6rem;
    font-size: 1.4rem;
    color: #333;
    font-weight: 400;
    padding: 0.2rem 2.6rem 0.2rem 0;
    font-family: 'Source Sans Pro', sans-serif;
`

export const ContentBoxTableDataCell = styled.div`
    display: table-cell;
    white-space: nowrap;
    padding: 0.2rem 2.6rem 0.2rem 0;
    white-space: pre;
`
export const ContentBoxTableHeader = styled.div`
    display: table-cell;
    font-weight: 500;
    font-size: 1.25rem;
    padding: 0.2rem 2.6rem 0.2rem 0;
    white-space: pre;
    letter-spacing: -0.04rem;
    text-transform: uppercase;
    opacity: 0.5;
    font-family: 'Source Sans Pro', sans-serif;
`
