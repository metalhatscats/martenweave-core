# Stakeholder Interview Questions

> Use these questions during the discovery phase of a Migration Model Readiness Assessment.
> Adapt based on the stakeholder role.

## Data Ownership & Governance

1. Who is the business owner for customer / vendor / material master data?
2. Who has authority to approve changes to field definitions or value mappings?
3. How do you currently track which SAP fields are actively used vs. legacy?
4. Is there a data stewardship process in place today?
5. What happens when two systems disagree on the meaning of a field?

## SAP Migration Scope

6. Which SAP modules are in scope for this migration (SD, MM, FI, BP, etc.)?
7. Are you migrating from ECC, S/4HANA, or a third-party system?
8. What is the target go-live date for the migration?
9. Which objects are highest risk: Customer, Vendor, Material, or something else?
10. Are there known data quality issues that have blocked past migrations?

## Field Mapping Confidence

11. For your top 20 SAP fields, how confident are you that the business meaning is documented?
12. Are there fields that different teams interpret differently?
13. Which fields have complex value mappings or transformations?
14. Do you have a current field dictionary or data catalog?
15. How are custom fields (Z-fields) documented and governed?

## Decisions & Evidence

16. What open decisions about the target model still need to be made?
17. Where are those decisions documented today (email, wiki, meetings, nowhere)?
18. Is there an audit requirement to show traceability from source to target?
19. How do you currently handle change requests to the data model?
20. What would an auditor ask for if they reviewed your migration next week?

## Validation & Rules

21. Which fields have business rules that must be enforced in the target system?
22. Are there validation rules that differ by company code, sales area, or plant?
23. How do you test that mappings produce correct target values?
24. Are there reference value lists (LoV) that are incomplete or outdated?
25. Who maintains the value mappings (e.g., country codes, payment terms)?

## Readiness & Handoff

26. What would convince you that the model is ready for the build/convert phase?
27. Who needs to sign off on the field mappings before development begins?
28. How will the business review the model without reading Markdown or Git?
29. What format do downstream teams need (Excel, PDF, API, database)?
30. If you re-ran this assessment in 30 days, what would you want to see improved?

## Notes

- Keep answers in the engagement working notes.
- Turn unresolved decisions into Martenweave `Decision` or `Issue` objects.
- Do not record confidential data or real customer information.
