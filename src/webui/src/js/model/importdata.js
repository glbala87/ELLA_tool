/* jshint esnext: true */

export class ImportData {
    constructor(filename, input) {
        this.filename = filename
        this.input = input

        this.contents = {
            lines: {}, // {displayValue: {value: line, include: true/false}, ...}
            header: ''
        }

        this._choices = {
            mode: ['Analysis', 'Variants'],
            type: ['Create', 'Append'],
            technology: ['Sanger', 'HTS'],
            // Should be removed when porting to cerebral (use config values)
            priority: [1, 2, 3]
        }

        // Current import selection, with validation of choices
        this.importSelection = {
            _choices: this._choices,
            // Mode
            _mode: this._choices.mode[0],
            get mode() {
                return this._mode
            },
            set mode(val) {
                if (this._choices['mode'].indexOf(val) < 0) {
                    console.error(`Invalid choice for mode: ${val}`)
                    return
                }
                this._mode = val
            },
            // Type
            _type: this._choices.type[0],
            get type() {
                return this._type
            },
            set type(val) {
                if (this._choices['type'].indexOf(val) < 0) {
                    console.error(`Invalid choice for type: ${val}`)
                    return
                }
                this._type = val
            },
            // Technology
            _technology: this._choices.technology[0],
            get technology() {
                return this._technology
            },
            set technology(val) {
                if (this._choices['technology'].indexOf(val) < 0) {
                    console.error(`Invalid choice for technology: ${val}`)
                    return
                }
                this._technology = val
            },
            _priority: this._choices.priority[0],
            get priority() {
                return this._priority
            },
            set priority(val) {
                if (this._choices['priority'].indexOf(val) < 0) {
                    console.error(`Invalid choice for type: ${val}`)
                    return
                }
                this._priority = val
            },
            // Non-validated choices
            analysis: null,
            analysisName: '',
            genepanel: null
        }

        //
        this._hasGenotype = true

        this.parse()
    }

    getChoices(key) {
        return this._choices[key]
    }

    isAnalysisMode() {
        return this.importSelection.mode === 'Analysis'
    }

    isCreateNewAnalysisType() {
        return this.isAnalysisMode() && this.importSelection.type === 'Create'
    }

    isAppendToAnalysisType() {
        return this.isAnalysisMode() && this.importSelection.type === 'Append'
    }

    isVariantMode() {
        return this.importSelection.mode === 'Variants'
    }

    // Contents
    parse() {
        let lines = this.input.trim().split('\n')
        let header = ''
        let fileType
        for (let l of lines) {
            if (l.trim() === '') {
                continue
            }
            if (l.trim().startsWith('#CHROM')) {
                fileType = 'vcf'
            } else if (l.trim().startsWith('Index')) {
                fileType = 'seqpilot'
            }

            if (l.trim().startsWith('#') || l.trim().startsWith('Index')) {
                header += l + '\n'
                continue
            }
            let key
            if (fileType === 'vcf') {
                key = this._parseVcfLine(l)
            } else if (fileType === 'seqpilot') {
                key = this._parseSeqPilotLine(header, l)
            } else {
                key = this._parseGenomicOrHGVScLine(l)
            }

            this.contents.lines[key] = {
                value: l,
                include: true
            }
        }

        this.contents.header = header.trim()
    }

    _parseVcfLine(line) {
        const vals = line.trim().split('\t')
        const chrom = vals[0]
        const pos = vals[1]
        const ref = vals[3]
        const alt = vals[4]

        const format = vals[8]
        const sample = vals[9]

        let genotype
        let gt_index = format.split(':').indexOf('GT')
        if (gt_index < 0) {
            genotype = '?/?'
            this._hasGenotype = false
        } else {
            genotype = sample.split(':')[gt_index]
        }

        return `${chrom}:${pos} ${ref}>${alt} (${genotype})`
    }

    _parseSeqPilotLine(header, line) {
        const splitHeader = header.trim().split('\t')
        const splitLine = line.trim().split('\t')
        const values = {}
        for (let i = 0; i < splitHeader.length; i++) {
            values[splitHeader[i]] = splitLine[i]
        }
        const transcript = values['Transcript']
        const cdna = values['c. HGVS']
        let genotype = values['Nuc Change'].match(/\(het\)|\(homo\)/)
        if (!genotype) {
            this._hasGenotype = false
            genotype = '(?)'
        }

        return `${transcript}.${cdna} ${genotype}`
    }

    _parseGenomicOrHGVScLine(line) {
        let genotype = line.match(/ \((het|homo)\)?/)
        if (!genotype) {
            this._hasGenotype = false
        }
        return line
    }

    genotypeAvailable() {
        return this._hasGenotype
    }

    getFileNameBase() {
        let fileNameBase = ''
        if (this.filename) {
            if (this.filename.includes('.')) {
                fileNameBase = this.filename.substring(0, this.filename.lastIndexOf('.'))
            } else {
                fileNameBase = this.filename
            }
        }
        return fileNameBase
    }

    getFilename() {
        return this.filename
    }

    _rebuildData() {
        let data = this.contents.header
        for (let ld of Object.values(this.contents.lines)) {
            if (ld.include) {
                data += '\n' + ld.value
            }
        }
        return data
    }

    // Import selection
    isSelectionComplete() {
        let a = this.importSelection.mode === 'Variants' && this.importSelection.genepanel
        let b =
            this.importSelection.mode === 'Analysis' &&
            this.importSelection.type === 'Create' &&
            this.importSelection.analysisName &&
            this.importSelection.genepanel
        let c =
            this.importSelection.mode === 'Analysis' &&
            this.importSelection.type === 'Append' &&
            this.importSelection.analysis
        let d = Object.values(this.contents.lines).filter((c) => c.include).length

        return Boolean((a || b || c) && d)
    }

    process() {
        let properties = {
            sample_type: this.importSelection.technology
        }

        if (this.importSelection.mode === 'Analysis') {
            properties.create_or_append = this.importSelection.type
            if (this.importSelection.type === 'Create') {
                properties.analysis_name = this.importSelection.analysisName
                properties.priority = this.importSelection.priority
            } else {
                properties.analysis_name = this.importSelection.analysis.name
            }
        }

        if (this.isAppendToAnalysisType()) {
            var genepanel = this.importSelection.analysis.genepanel
        } else {
            var genepanel = this.importSelection.genepanel
        }

        let data = {
            mode: this.importSelection.mode,
            data: this._rebuildData(),
            genepanel_name: genepanel.name,
            genepanel_version: genepanel.version,
            properties: properties
        }

        console.log(data)

        return data
    }
}
