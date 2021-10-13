## Background

Prepare and release [version]

## Implementation

--- DELETE ME ---

Remember:

- Assign **Weight**, if possible

--- DELETE ME ---

### Tasks specific for this release

[List tasks that are specific for this release here]

### Tasks that should always be performed

#### Staging, before user verification test
- [ ] Automatic import (specific samples and detailed check list)
- [ ] Manual import (specific samples and detailed check list)
- [ ] Exports (EKG, all variants)
- [ ] CLI: check fixtures, usergroups, gene panels, filter configs
- [ ] Load test (automated script; Hey)

#### On startup of ELLA
- [ ] Schema checks
- [ ] Check filter config

#### Testing and documentation
- [ ] ELLA endringskontroll (versjonsoppdatering)
- [ ] Release notes (list any breaking changes)
- [ ] Verifiseringstest: New or changed functionality (before production, in staging env)
- [ ] Akseptansetest: In production env, before full release. Standardized check list.

Major changes? (import/filter) 
- [ ] Risk evaluation
- [ ] Verifiserings-/valideringsrapport
- [ ] Not applicable

/label ~"work::draft" ~"type::chore" ~"DMG docs"
/confidential 