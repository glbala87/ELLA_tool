import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
import { findGeneConfigOverride } from '../../common/helpers/genepanel'

/**
 * Calculates various genepanel information for every gene
 * found in the gene panel.
 * Returns an object with values per gene.
 * @param {state} genepanel Genepanel tag
 * @param {state} allele Allele tag
 */
export default (genepanel) => {
    return Compute(genepanel, state`app.config.user.user_config.acmg`, (genepanel, acmgConfig) => {
        const result = {}

        if (genepanel === undefined) {
            return result
        }

        const uniqueHgncIds = new Set(genepanel.transcripts.map((t) => t.gene.hgnc_id))
        for (let hgncId of uniqueHgncIds) {
            result[hgncId] = {}

            const props = ['last_exon_important', 'disease_mode']
            const geneConfigOverride = findGeneConfigOverride(hgncId, acmgConfig)
            for (let p of props) {
                result[hgncId][p] = {
                    value: p in geneConfigOverride ? geneConfigOverride[p] : acmgConfig[p],
                    overridden: p in geneConfigOverride
                }
            }

            result[hgncId].inheritance = [
                ...new Set(
                    genepanel.inheritances
                        .filter((inh) => inh.hgnc_id === hgncId)
                        .map((inh) => inh.inheritance)
                )
            ].join('|')

            // If 'frequency' is defined for the gene, use that.
            // Otherwise, use the default given the inheritance key
            if ('frequency' in geneConfigOverride) {
                result[hgncId].freqCutoffsACMG = {
                    value: geneConfigOverride.frequency.thresholds,
                    overridden: true
                }
            } else {
                result[hgncId].freqCutoffsACMG = {
                    value:
                        result[hgncId].inheritance === 'AD'
                            ? acmgConfig.frequency.thresholds['AD']
                            : acmgConfig.frequency.thresholds['default'],
                    overridden: false
                }
            }

            result[hgncId].phenotypes = genepanel.phenotypes.filter(
                (p) => p.gene.hgnc_id === hgncId
            )
            result[hgncId].transcripts = genepanel.transcripts.filter(
                (t) => t.gene.hgnc_id === hgncId
            )
        }
        return result
    })
}
