/* jshint esnext: true */

export default class Analysis {
    /**
     * Represents one Analysis.
     *
     * Also holds the genepanel (which should be model.Genepanel in the future)
     * @param  {object} Analysis data from server, see api/v1/interpretations/
     */
    constructor(data) {
        Object.assign(this, data);

    }

    getInterpretationState() {
        var STATE_PRIORITY = ['Not started', 'Ongoing', 'Done'];
        let states = this.interpretations.map(x => x.status);
        if (states.length) {
            return states.sort(x => STATE_PRIORITY.indexOf(x))[0];
        }
    }

    findGeneConfig(geneSymbol) {
        let panelConfig = this.genepanel.config;
        if (panelConfig && panelConfig.data && geneSymbol in panelConfig.data) {
            return panelConfig.data[geneSymbol];
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
        let overrides = this.findGeneConfig(geneSymbol);
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
        if (! this.genepanel) {
            return '';
        }

        let source = this.genepanel.phenotypes;
        let config = this.findGeneConfig(geneSymbol);
        if (config && 'inheritance' in config) {
            return config['inheritance'];
        }

        if (source) {
            let codes = source.filter(ph => ph.gene.hugoSymbol == geneSymbol)
                .map( ph => ph.inheritance)
                .filter(i => i) // remove empty
                .sort();

            return codes.join('/');
        } else {
            return '';
        }

    }


    getInterpretationId() {
        // TODO: implement me
        return this.interpretations[this.interpretations.length - 1].id;
    }

    /**
     * Returns the user of the last interpretation for analysis.
     */
    getInterpretationUser() {
        return this.interpretations[this.interpretations.length - 1].user;
    }
}


