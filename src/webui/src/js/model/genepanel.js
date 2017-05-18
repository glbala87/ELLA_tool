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

    findGeneConfigOverride(geneSymbol) {
        let panelConfig = this.config;
        if (panelConfig && panelConfig.data && geneSymbol in panelConfig.data) {
            return panelConfig.data[geneSymbol];
        } else {
            return {};
        }
    }

    find_cutoff(inheritance, default_values) {
        if (inheritance == 'AD') {
            return default_values['freq_cutoffs']['AD'];
        } else {
            return default_values['freq_cutoffs']['default'];
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
        let result = {
            _overridden: []  // Holds keys that are overridden by genepanel config.
        };
        let props = ['last_exon_important', 'disease_mode', 'freq_cutoffs'];
        let config_override = this.findGeneConfigOverride(geneSymbol);
        for (let p of props) {
            if (p in config_override) {
                result[p] = config_override[p];
                result['_overridden'].push(p);
            }
            else {
                result[p] = default_genepanel_config[p];
            }
        }

        result['inheritance'] = this.getInheritanceCodes(geneSymbol);
        if ('inheritance' in config_override) {
            result['_overridden'].push('inheritance');
        }

        // If 'freq_cutoffs' is defined in genepanel config, use those. Otherwise, use the default
        // given the inheritance key
        if (!('freq_cutoffs' in config_override)) {
            result['freq_cutoffs'] = this.find_cutoff(result['inheritance'], default_genepanel_config);
        }

        if ('comment' in config_override) {
            result['comment'] = config_override['comment'];
        }
        result['omim_entry_id'] = this.getOmimEntryId(geneSymbol);

        return result;
    }

    /**
     * Returns either overridden inheritance from genepanel config,
     * or searches the gene's phenotypes to get distinct set of inheritance codes.
     * @param  {String} geneSymbol Gene symbol
     * @return {String}            Inheritance code formatted like 'AD/AR/XD'
     */
    getInheritanceCodes(geneSymbol) {
        let config = this.findGeneConfigOverride(geneSymbol);
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
    /**
     * Returns the OMIM entry ID for the gene as found in the phenotypes file,
     * @param  {String} geneSymbol Gene symbol
     * @return {String}            Entry ID like 113705
     */
    getOmimEntryId(geneSymbol) {
        let phenotypes = this.phenotypesBy(geneSymbol);
        // all phenotypes have the same gene and thus omim entry
        return phenotypes ? phenotypes[0].gene.omim_entry_id : '';

    }

    getDisplayInheritance(gene_symbol) {
        return this.getInheritanceCodes(gene_symbol);
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


