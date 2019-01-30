import React from 'react'
import PropTypes from 'prop-types'
import styled from 'styled-components'

const WarningContainer = styled.div`
    color: white;
    background-color: red;
    font-size: 1.5rem;
    padding: 0.3rem;
    padding-left: 1rem;
    padding-right: 1rem;
    margin-bottom: 1rem;
`

export const Warning = ({ children }) => {
    return <WarningContainer>{children}</WarningContainer>
}

Warning.propTypes = {}
