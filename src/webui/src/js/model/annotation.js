/* jshint esnext: true */


class AnnotationTranscript {

    constructor(data) {
        Object.assign(this, data);
        // Precompute values
        this.transcript = this._transcript();
        this.gene = this._gene();
        this.HGVSc = this._HGVSc();
        this.HGVSc_short = this._HGVScShort();
        this.freq = this._freq();
    }

    _transcript() {
        if (this.CSQ && this.CSQ.Feature_type === 'Transcript') {
            let transcript = this.CSQ.Feature;
            // Split NM_xxxxxx.x transcripts to NM_xxxxxxx
            if (transcript.startsWith('NM')) {
                transcript = transcript.split('.', 1)[0];
            }
            return transcript;
        }
        return null;
    }

    _gene() {
        if (!this.CSQ || !this.CSQ.SYMBOL) {
            return null;
        }
        return this.CSQ.SYMBOL;
    }

    _HGVSc() {
        if (this.CSQ) {
            return this.CSQ.HGVSc;
        }
        return null;
    }

    _HGVScShort() {
        if (this._HGVSc()) {
            return this._HGVSc().split(':')[1];
        }
        return null;
    }

    _calcExacFreq() {

        if (!('EXAC' in this)) {
            return {};
        }
        let freqs = {},
            counts = {},
            totals = {};

        for (let key of Object.keys(this.EXAC)) {
            let name_tag = key.split('_', 2);
            if (name_tag.length < 2) {
                continue;
            }
            let name = name_tag[0];
            let tag = name_tag[1];

            if (name == 'AC') {
                // Value should always be a single item array
                counts[tag] = this.EXAC[key][0];
            }

            else if (name == 'AN') {
                totals[tag] = this.EXAC[key];
            }
        }

        // Calculate frequencies
        for (let key of Object.keys(counts)) {
            if (key in totals) {
                freqs[key] = counts[key] / totals[key];
            }
        }
        return freqs;

    }

    /*
     * Parses the annotation data and creates a frequency structure in this.freq.
     * The structure consists of {group_name: {name: float}}
     */
    _freq() {


        function parseMAF(maf) {
            if (maf) {
                let val = Object.values(maf);
                if (val.length > 1) {
                    throw `Multiple frequencies for ${maf} not supported.`;
                }
                return parseFloat(val);
            }
            return NaN;
        }

        let frequencies = {
            'exac': this._calcExacFreq()
        };

        // Handle VEP data
        if (this.CSQ) {
            var groups = [
                [
                    'esp6500',
                    [
                        'AA_MAF',
                        'EA_MAF',
                    ]
                ],
                [
                    'thousand_g',
                    [
                        'GMAF',
                        'AFR_MAF',
                        'AMR_MAF',
                        'ASN_MAF',
                        'EUR_MAF'
                    ]
                ]
            ];

            for (let group of groups) {
                if (!(group in frequencies)) {
                    frequencies[group[0]] = {};
                }
                for (let k of group[1]) {
                    let v = parseMAF(this.CSQ[k]);
                    if (!isNaN(v)) {
                        frequencies[group[0]][k] = v;
                    }
                }

            }
        }

        return frequencies;
    }


    /*
     * Iterate over all frequency groups and find the total max frequency.
     */
    getMaxFreq() {

        let max = 0;
        for (let key of Object.keys(this.freq)) {
            if (Object.keys(this.freq[key]).length) {
                let new_max = Math.max(...Object.values(this.freq[key]));
                if (new_max > max) {
                    max = new_max;
                }
            }
        }
        return max;
    }

    getReferenceData() {
        let ref_data = [];
        if (this.HGMD && this.HGMD.extrarefs) {
            for (let extraref of this.HGMD.extrarefs) {
                if ('pmid' in extraref) {
                    ref_data.push({
                        pmid: extraref.pmid,
                        sources: ['HGMDx']
                    });
                }
            }
        }
        if (this.CSQ && 'PUBMED' in this.CSQ) {
            for (let pubmed of this.CSQ.PUBMED) {
                let r = ref_data.find(x => x.pmid == pubmed);
                if (r) {
                    r.sources.push('VEP');
                }
                else {
                    ref_data.push({
                        pmid: pubmed,
                        sources: ['VEP']
                    });
                }
            }
        }
        return ref_data;
    }

}



class Annotation {
    constructor(data) {
        this._data = data;
        this.transcripts = [];
        this._createAnnotationTranscripts();
    }

    _createAnnotationTranscripts() {
        if ('CSQ' in this._data) {
            for (let entry of this._data.CSQ) {
                if (!('SYMBOL' in entry)) {
                    continue;
                }
                let gene = entry.SYMBOL;

                if (!gene || !(entry.Feature && entry.Feature_type === 'Transcript')) {
                    continue;
                }

                // Copy data and overwrite CSQ list with single CSQ entry for this transcript
                let data = {};
                Object.assign(data, this._data);
                data.CSQ = entry;
                this.transcripts.push(new AnnotationTranscript(data));
            }
        }
    }

    /**
     * Returns the entry matching any of the provided transcripts.
     * The use case is that you provide a global list of transcripts you're interested
     * in, and you want one AnnotationTranscript object per allele.
     * If multiple matching AnnotationTranscript objects are found
     * for the provided transcript list, an exception is thrown.
     * @param  {Array(string)} transcripts Transcript names
     * @return {AnnotationTranscript} Matching AnnotationTranscript object.
     */
    getByTranscripts(transcripts) {
        var annotation_transcripts = this.transcripts.filter(
            e => transcripts.find(i => i === e.transcript)
        );
        if (annotation_transcripts.length > 1) {
            throw "Got multiple AnnotationTranscript objects for provided transcripts for one allele. This is not supported."
        }
        return annotation_transcripts[0];
    }
}
