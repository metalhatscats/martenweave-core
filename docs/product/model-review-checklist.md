# Model Review Checklist

A practical checklist for reviewing model readiness before approval or implementation.

## Categories

### Business Definition
- [ ] Name and description are clear
- [ ] Purpose is documented
- [ ] Scope boundaries are defined

### Ownership
- [ ] Business owner assigned
- [ ] Data steward assigned
- [ ] Technical owner identified

### Source / Target
- [ ] Source systems documented
- [ ] Target systems documented
- [ ] FieldEndpoints mapped

### Mappings
- [ ] Attribute-to-field mappings exist
- [ ] Mappings have value mappings where needed
- [ ] Mapping logic is validated

### Value Lists
- [ ] Allowed values defined
- [ ] Value mappings complete
- [ ] Unknown value handling documented

### Validation Rules
- [ ] Rules defined for key attributes
- [ ] Rules tested against sample data
- [ ] Rule coverage above threshold

### Data Quality
- [ ] Dataset profiled
- [ ] Quality expectations documented
- [ ] Gap analysis reviewed

### Evidence
- [ ] Decisions recorded
- [ ] Risks identified
- [ ] Issues tracked

### System Lineage
- [ ] Upstream dependencies traced
- [ ] Downstream impact assessed
- [ ] Cross-system flows documented

### Release Scope
- [ ] Environment scope defined
- [ ] Release wave assigned
- [ ] Rollout plan reviewed

## Commands (Future)

```bash
modelops review-checklist --repo ./my-model --object DOMAIN-1
modelops review-checklist --repo ./my-model --release wave-3
```

## Gap → Action

Unchecked items link to Issue or ChangeRequest drafts for follow-up.
