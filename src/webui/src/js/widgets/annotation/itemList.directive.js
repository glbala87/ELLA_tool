import app from '../../ng-decorators'
import { getNested } from '../../util'
import { Compute } from 'cerebral'
import { connect } from '@cerebral/angularjs'
import { state, props } from 'cerebral/tags'
import template from './itemList.ngtmpl.html' // eslint-disable-line no-unused-vars
import getAnnotationConfigItem from '../../store/modules/views/workflows/computed/getAnnotationConfigItem'
import getInterpolatedUrlFromTemplate from '../../store/modules/views/workflows/computed/getInterpolatedUrlFromTemplate'

const extractedData = Compute(
    state`${props`allelePath`}.annotation.${props`source`}`,
    getAnnotationConfigItem,
    (rawData, viewConfig) => {
        if (rawData === undefined) {
            return []
        }

        let processed = []

        for (let subconfig of viewConfig.items) {
            let subsource = subconfig.subsource
            let subRawData
            if (subsource !== undefined) {
                subRawData = getNested(rawData, subsource)
            } else {
                subRawData = rawData
            }

            if (subRawData === undefined) {
                continue
            } else if (!Array.isArray(subRawData)) {
                subRawData = [subRawData]
            }

            const valueType = subconfig.type || 'primitives'
            const key = subconfig.key || null
            const url = subconfig.url || null

            for (let item of subRawData) {
                if (valueType === 'primitives') {
                    processed.push({ item, url })
                } else if (valueType === 'objects') {
                    let subItems = getNested(item, key)
                    if (subItems === undefined) {
                        continue
                    } else if (!Array.isArray(subItems)) {
                        subItems = [subItems]
                    }
                    for (let subItem of subItems) {
                        processed.push({ item: subItem, url })
                    }
                }
            }
        }
        return processed
    }
)

app.component('itemList', {
    bindings: {
        source: '@',
        boxTitle: '@',
        url: '@',
        urlEmpty: '@',
        allelePath: '<',
        annotationConfigId: '=',
        annotationConfigItemIdx: '='
    },
    templateUrl: 'itemList.ngtmpl.html',
    controller: connect({
        data: extractedData,
        titleUrl: getInterpolatedUrlFromTemplate(props`url`, state`${props`allelePath`}`),
        viewConfig: getAnnotationConfigItem
    })
})
