/* jshint esnext: true */

export default class Genepanel {
    /**
     * Represents one Genepanel.
     *
     * @param  {object} Genepanel data from server, see api/v1/genepanels/
     */
    constructor(data) {
        Object.assign(this, data);

    }

    findGeneConfigOverrides(geneSymbol) {
        let panelConfig = this.config;
        if (panelConfig && panelConfig.data && geneSymbol in panelConfig.data) {
            return panelConfig.data[geneSymbol];
        } else {
            return {};
        }
    }

    find_cutoff(key, inheritance, overrides, default_values) {
        if (key in overrides) {
            return {'_type': 'genepanel_override', 'value': overrides[key]};
        } else {
            if (inheritance == 'AD') {
                return default_values['freq_cutoffs']['AD'][key];
            } else {
                return default_values['freq_cutoffs']['Other'][key];
            }
        }
    }

    /**
     *
     * The values in the object are either a primitive or an object. The object form indicates the value
     * is "hardcoded"/overridden in the genepanel config, as opposed to being calculated from
     * the panels phenotypes/transcripts. The object form looks like {'_type': 'genepanel_override', value: primitive}
     *
     * @param geneSymbol
     * @param default_genepanel_config
     * @returns {object} the keys are the possible properties of a genepanel and the value is the value of the property
     */
    calculateGenepanelConfig(geneSymbol, default_genepanel_config) {
        let result = {};
        let props = ['last_exon', 'disease_mode']; // see api/util/genepanelconfig.py#COMMON_GENEPANEL_CONFIG
        let overrides = this.findGeneConfigOverrides(geneSymbol);
        for (let p of props) {
                result[p] = p in overrides ?
                    {'_type': 'genepanel_override', 'value': overrides[p]} : default_genepanel_config[p];
        }

        let inheritanceCodes = this.getInheritanceCodes(geneSymbol); // no object wrapper
        result['inheritance'] = inheritanceCodes;

        result['hi_freq_cutoff'] = this.find_cutoff('hi_freq_cutoff', inheritanceCodes, overrides, default_genepanel_config);
        result['lo_freq_cutoff'] = this.find_cutoff('lo_freq_cutoff', inheritanceCodes, overrides, default_genepanel_config);

        if ('comment' in overrides) {
            result['comment'] = overrides['comment'];
        }

        return result;
    }

    // Return inheritance from relevant phenotypes, or the hardcoded value defined in the genepanel config
    getInheritanceCodes(geneSymbol) {
        let config = this.findGeneConfigOverrides(geneSymbol);
        if (config && 'inheritance' in config) {
            return config['inheritance'];
        }

        let phenotypes = this.phenotypesBy(geneSymbol);
        if (phenotypes) {
            let codes = phenotypes
                .map(ph => ph.inheritance)
                .filter(i => i && i.length > 0); // remove empty
            let uniqueCodes = new Set(codes);
            return Array.from(uniqueCodes.values()).sort().join('/');
        } else {
            return '';
        }

    }

    phenotypesBy(geneSymbol) {
        let phenotypes = this.phenotypes;
        if (phenotypes) {
            return phenotypes.filter(ph => ph.gene.hugo_symbol == geneSymbol);
        } else {
            return null;
        }
    }
}


