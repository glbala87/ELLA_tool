import { Compute } from 'cerebral'
import { state } from 'cerebral/tags'
/* jshint esnext: true */
export const getSplitInput = (rawInput) => {
    const lines = rawInput.split('\n')
    let splitInput = {}

    let currentFile = ''
    let uuid = null
    let importId = 0
    for (let l of lines) {
        if (l.trim() === '') continue

        // Check if start of new file
        // if (!uuid || l.startsWith("-")) {
        if (importId === 0 || l.startsWith('-')) {
            importId += 1
            if (l.startsWith('-')) {
                currentFile = l.replace(/-*\s*/g, '')
            } else {
                currentFile = ''
            }

            splitInput[importId] = {
                filename: currentFile,
                input: ''
            }

            // Don't include line in contents if it is a separator line
            if (l.startsWith('-')) continue
        }
        splitInput[importId].input += l + '\n'
    }
    return splitInput
}

export const getParsedInput = (input) => {
    const _parseVcfLine = (line) => {
        const vals = line.trim().split('\t')
        const chrom = vals[0]
        const pos = vals[1]
        const ref = vals[3]
        const alt = vals[4]

        const format = vals[8]
        const sample = vals[9]

        let gt_index = format.split(':').indexOf('GT')
        let displayGenotype = gt_index >= 0 ? sample.split(':')[gt_index] : '?/?'
        return [`${chrom}:${pos} ${ref}>${alt} (${displayGenotype})`, gt_index >= 0]
    }

    const _parseSeqPilotLine = (header, line) => {
        const splitHeader = header.trim().split('\t')
        const splitLine = line.trim().split('\t')
        const values = {}
        for (let i = 0; i < splitHeader.length; i++) {
            values[splitHeader[i]] = splitLine[i]
        }
        const transcript = values['Transcript']
        const cdna = values['c. HGVS']
        let genotype = values['Nuc Change'].match(/\(het\)|\(homo\)/)
        let displayGenotype = Boolean(genotype) ? genotype : '(?)'

        return [`${transcript}.${cdna} ${displayGenotype}`, Boolean(genotype)]
    }

    const _parseGenomicOrHGVScLine = (line) => {
        let genotype = line.match(/ \((het|homo)\)?/)
        return [line, Boolean(genotype)]
    }

    // Contents
    let lines = input.trim().split('\n')
    const variantDataLines = []
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
        if (fileType === 'vcf') {
            var [display, hasGenotype] = _parseVcfLine(l)
        } else if (fileType === 'seqpilot') {
            var [display, hasGenotype] = _parseSeqPilotLine(header, l)
        } else {
            var [display, hasGenotype] = _parseGenomicOrHGVScLine(l)
        }

        variantDataLines.push({
            display: display,
            value: l,
            hasGenotype
        })
    }
    return { header: header.trim(), variantDataLines }
    //   this.contents.header = header.trim();
}

export const getDefaultSelection = (parsedInput) => {
    return {
        mode: 'Analysis',
        type: 'Create',
        technology: 'Sanger',
        priority: 1,
        analysis: null,
        analysisName: '',
        genepanel: null
    }
}

export const isSelectionComplete = (importKey) => {
    return Compute(importKey, state`views.overview.import.jobData`, (importKey, jobData) => {
        console.log(importKey)
        if (jobData === undefined) {
            return false
        }
        if (importKey !== undefined) {
            jobData = { importKey: jobData[importKey] }
        }
        console.log(jobData)
        for (let jd of Object.values(jobData)) {
            let a = jd.selection.type === 'Variants' && jd.selection.genepanel
            let b =
                jd.selection.type === 'Analysis' &&
                jd.selection.mode === 'Create' &&
                jd.selection.analysisName &&
                jd.selection.genepanel
            let c =
                jd.selection.type === 'Analysis' &&
                jd.selection.mode === 'Append' &&
                jd.selection.analysis
            let d = Object.values(jd.selection.include).filter((c) => c).length

            if (!Boolean((a || b || c) && d)) {
                return false
            }
        }
        return true
    })
}

export class ImportData {
    constructor({ filename, input }) {
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

        return data
    }
}
