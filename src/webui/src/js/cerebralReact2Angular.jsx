import { react2angular } from 'react2angular'
import React from 'react'
import { Container } from '@cerebral/react'

export default (WrappedComponent, bindingNames) => {
    const names =
        bindingNames ||
        (WrappedComponent.propTypes && Object.keys(WrappedComponent.propTypes)) ||
        []
    const Wrapper = (props) => {
        return (
            <Container controller={props.cerebral.controller}>
                <WrappedComponent {...props} />
            </Container>
        )
    }
    return react2angular(Wrapper, names, ['cerebral'])
}
