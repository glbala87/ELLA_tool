import getOptions from '../actions/getOptions'

export default [
    getOptions,
    {
        success: [
            ({ props, module }) => {
                if (props.result) {
                    for (let key of Object.keys(props.result)) {
                        module.set(`options.${key}`, props.result[key])
                    }
                }
            }
        ],
        error: []
    }
]
