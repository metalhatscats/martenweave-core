---
id: PP-SCHEMA-9EDF23919A5B701D
type: PatchProposal
status: accepted
name: PP-SCHEMA-9EDF23919A5B701D
title: 'Schema Import Proposal: BusinessPartnerService'
created_by: system
created_at: '2026-07-25T08:47:53Z'
source_evidence: 'Schema import evidence from business-partner-service.wsdl (wsdl,
  checksum 9edf23919a5b701d1d748a2af6b86d8eb21d7547bcd15f1666622e24560b781d, parser
  1.0, inspected 2026-07-25T08:47:53Z). Warnings: none.'
source_state: proposal
affected_objects:
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
- ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-CITY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
- VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
- VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
- ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
- FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
- IFACE-SCHEMA-BUSINESSPARTNERSERVICE
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
- MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-CITY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
- SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
- IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATE
- IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREAD
operations:
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    type: BusinessEntity
    status: draft
    name: BusinessPartnerCreateRequest
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    type: BusinessEntity
    status: draft
    name: BusinessPartnerCreateResponse
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
    type: BusinessEntity
    status: draft
    name: BusinessPartnerReadRequest
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/schema/BusinessPartnerReadRequest.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
    type: BusinessEntity
    status: draft
    name: BusinessPartnerReadResponse
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/schema/BusinessPartnerReadResponse.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    type: BusinessEntity
    status: draft
    name: BusinessPartnerCreateInput
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/message/BusinessPartnerCreateInput.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    type: BusinessEntity
    status: draft
    name: BusinessPartnerCreateOutput
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/message/BusinessPartnerCreateOutput.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
    type: BusinessEntity
    status: draft
    name: BusinessPartnerReadInput
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/message/BusinessPartnerReadInput.
- op: create_object
  object_id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
  object_type: BusinessEntity
  target_path: null
  before: null
  after:
    id: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
    type: BusinessEntity
    status: draft
    name: BusinessPartnerReadOutput
    description: Imported from wsdl schema evidence.
  reason: Entity imported from BusinessPartnerService/message/BusinessPartnerReadOutput.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    type: Attribute
    status: draft
    name: BusinessPartnerCategory
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for BusinessPartnerCategory.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/BusinessPartnerCategory.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    type: FieldEndpoint
    status: draft
    name: BusinessPartnerCategory
    endpoint_type: wsdl_message_field
    technical_name: BusinessPartnerCategory
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/BusinessPartnerCategory.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/BusinessPartnerCategory.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    type: Attribute
    status: draft
    name: AccountGroup
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for AccountGroup.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/AccountGroup.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    type: FieldEndpoint
    status: draft
    name: AccountGroup
    endpoint_type: wsdl_message_field
    technical_name: AccountGroup
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/AccountGroup.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/AccountGroup.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    type: Attribute
    status: draft
    name: FirstName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for FirstName.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/FirstName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    type: FieldEndpoint
    status: draft
    name: FirstName
    endpoint_type: wsdl_message_field
    technical_name: FirstName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/FirstName.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/FirstName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    type: Attribute
    status: draft
    name: LastName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for LastName.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/LastName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    type: FieldEndpoint
    status: draft
    name: LastName
    endpoint_type: wsdl_message_field
    technical_name: LastName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/LastName.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/LastName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    type: Attribute
    status: draft
    name: OrganizationName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for OrganizationName.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/OrganizationName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    type: FieldEndpoint
    status: draft
    name: OrganizationName
    endpoint_type: wsdl_message_field
    technical_name: OrganizationName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/OrganizationName.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/OrganizationName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    type: Attribute
    status: draft
    name: Country
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for Country.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/Country.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    type: FieldEndpoint
    status: draft
    name: Country
    endpoint_type: wsdl_message_field
    technical_name: Country
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/Country.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/Country.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    type: Attribute
    status: draft
    name: City
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    description: Imported attribute for City.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/City.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-CITY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    type: FieldEndpoint
    status: draft
    name: City
    endpoint_type: wsdl_message_field
    technical_name: City
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/City.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/City.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    type: Attribute
    status: draft
    name: BusinessPartner
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    description: Imported attribute for BusinessPartner.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/BusinessPartner.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    type: FieldEndpoint
    status: draft
    name: BusinessPartner
    endpoint_type: wsdl_message_field
    technical_name: BusinessPartner
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/BusinessPartner.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/BusinessPartner.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    type: Attribute
    status: draft
    name: ProcessingStatus
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    description: Imported attribute for ProcessingStatus.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/ProcessingStatus.
- op: create_object
  object_id: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
  object_type: ValueList
  target_path: null
  before: null
  after:
    id: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    type: ValueList
    status: draft
    name: ProcessingStatus values
    value_list_type: enum
    entries:
    - code: created
      label: created
    - code: rejected
      label: rejected
    description: Imported enumeration for ProcessingStatus.
  reason: Enumeration imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/ProcessingStatus.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    type: FieldEndpoint
    status: draft
    name: ProcessingStatus
    endpoint_type: wsdl_message_field
    technical_name: ProcessingStatus
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    value_list: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/ProcessingStatus.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/ProcessingStatus.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    type: Attribute
    status: draft
    name: FullName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
    description: Imported attribute for FullName.
  reason: Attribute imported from BusinessPartnerService/schema/BusinessPartnerReadResponse/element/FullName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    type: FieldEndpoint
    status: draft
    name: FullName
    endpoint_type: wsdl_message_field
    technical_name: FullName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/schema/BusinessPartnerReadResponse/element/FullName.
  reason: FieldEndpoint imported from BusinessPartnerService/schema/BusinessPartnerReadResponse/element/FullName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    type: Attribute
    status: draft
    name: parameters
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    type: FieldEndpoint
    status: draft
    name: parameters
    endpoint_type: wsdl_message_field
    technical_name: parameters
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    type: Attribute
    status: draft
    name: BusinessPartnerCategory
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.BusinessPartnerCategory.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/BusinessPartnerCategory.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    type: FieldEndpoint
    status: draft
    name: parameters.BusinessPartnerCategory
    endpoint_type: wsdl_message_field
    technical_name: parameters.BusinessPartnerCategory
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/BusinessPartnerCategory.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/BusinessPartnerCategory.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    type: Attribute
    status: draft
    name: AccountGroup
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.AccountGroup.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/AccountGroup.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    type: FieldEndpoint
    status: draft
    name: parameters.AccountGroup
    endpoint_type: wsdl_message_field
    technical_name: parameters.AccountGroup
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/AccountGroup.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/AccountGroup.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    type: Attribute
    status: draft
    name: FirstName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.FirstName.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/FirstName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    type: FieldEndpoint
    status: draft
    name: parameters.FirstName
    endpoint_type: wsdl_message_field
    technical_name: parameters.FirstName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/FirstName.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/FirstName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    type: Attribute
    status: draft
    name: LastName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.LastName.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/LastName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    type: FieldEndpoint
    status: draft
    name: parameters.LastName
    endpoint_type: wsdl_message_field
    technical_name: parameters.LastName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/LastName.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/LastName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    type: Attribute
    status: draft
    name: OrganizationName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.OrganizationName.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/OrganizationName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    type: FieldEndpoint
    status: draft
    name: parameters.OrganizationName
    endpoint_type: wsdl_message_field
    technical_name: parameters.OrganizationName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/OrganizationName.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/OrganizationName.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    type: Attribute
    status: draft
    name: Country
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.Country.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/Country.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    type: FieldEndpoint
    status: draft
    name: parameters.Country
    endpoint_type: wsdl_message_field
    technical_name: parameters.Country
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/Country.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/Country.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    type: Attribute
    status: draft
    name: City
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    description: Imported attribute for parameters.City.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/City.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    type: FieldEndpoint
    status: draft
    name: parameters.City
    endpoint_type: wsdl_message_field
    technical_name: parameters.City
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/City.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/City.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    type: Attribute
    status: draft
    name: BusinessPartner
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    description: Imported attribute for parameters.BusinessPartner.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/BusinessPartner.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    type: FieldEndpoint
    status: draft
    name: parameters.BusinessPartner
    endpoint_type: wsdl_message_field
    technical_name: parameters.BusinessPartner
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/BusinessPartner.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/BusinessPartner.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    type: Attribute
    status: draft
    name: ProcessingStatus
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    description: Imported attribute for parameters.ProcessingStatus.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/ProcessingStatus.
- op: create_object
  object_id: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
  object_type: ValueList
  target_path: null
  before: null
  after:
    id: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    type: ValueList
    status: draft
    name: parameters.ProcessingStatus values
    value_list_type: enum
    entries:
    - code: created
      label: created
    - code: rejected
      label: rejected
    description: Imported enumeration for parameters.ProcessingStatus.
  reason: Enumeration imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/ProcessingStatus.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    type: FieldEndpoint
    status: draft
    name: parameters.ProcessingStatus
    endpoint_type: wsdl_message_field
    technical_name: parameters.ProcessingStatus
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    value_list: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/ProcessingStatus.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/ProcessingStatus.
- op: create_object
  object_id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
  object_type: Attribute
  target_path: null
  before: null
  after:
    id: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    type: Attribute
    status: draft
    name: FullName
    entity: ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
    description: Imported attribute for parameters.FullName.
  reason: Attribute imported from BusinessPartnerService/message/BusinessPartnerReadOutput/part/parameters/element/FullName.
- op: create_object
  object_id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
  object_type: FieldEndpoint
  target_path: null
  before: null
  after:
    id: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    type: FieldEndpoint
    status: draft
    name: parameters.FullName
    endpoint_type: wsdl_message_field
    technical_name: parameters.FullName
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    value_list: null
    description: Imported schema field from BusinessPartnerService/message/BusinessPartnerReadOutput/part/parameters/element/FullName.
  reason: FieldEndpoint imported from BusinessPartnerService/message/BusinessPartnerReadOutput/part/parameters/element/FullName.
- op: create_object
  object_id: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
  object_type: Interface
  target_path: null
  before: null
  after:
    id: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    type: Interface
    status: draft
    name: BusinessPartnerService
    description: Imported WSDL interface from business-partner-service.wsdl.
  reason: Interface imported from WSDL evidence.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    type: MessageType
    status: draft
    name: BusinessPartnerCreateInput
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: request
    description: Imported message structure for BusinessPartnerCreateInput from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerCreateInput'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    type: MessageType
    status: draft
    name: BusinessPartnerCreateOutput
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: response
    description: Imported message structure for BusinessPartnerCreateOutput from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerCreateOutput'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    type: MessageType
    status: draft
    name: BusinessPartnerCreateRequest
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: schema
    description: Imported message structure for BusinessPartnerCreateRequest from
      business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerCreateRequest'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    type: MessageType
    status: draft
    name: BusinessPartnerCreateResponse
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: schema
    description: Imported message structure for BusinessPartnerCreateResponse from
      business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerCreateResponse'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
    type: MessageType
    status: draft
    name: BusinessPartnerReadInput
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: request
    description: Imported message structure for BusinessPartnerReadInput from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerReadInput'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
    type: MessageType
    status: draft
    name: BusinessPartnerReadOutput
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: response
    description: Imported message structure for BusinessPartnerReadOutput from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerReadOutput'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST
    type: MessageType
    status: draft
    name: BusinessPartnerReadRequest
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: schema
    description: Imported message structure for BusinessPartnerReadRequest from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerReadRequest'.
- op: create_object
  object_id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
  object_type: MessageType
  target_path: null
  before: null
  after:
    id: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
    type: MessageType
    status: draft
    name: BusinessPartnerReadResponse
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    protocol: wsdl
    message_role: schema
    description: Imported message structure for BusinessPartnerReadResponse from business-partner-service.wsdl.
  reason: MessageType imported for entity 'BusinessPartnerReadResponse'.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    type: SchemaNode
    status: draft
    name: BusinessPartnerCategory
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY
    value_list: null
    technical_name: BusinessPartnerCategory
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for BusinessPartnerCategory.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/BusinessPartnerCategory.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    type: SchemaNode
    status: draft
    name: AccountGroup
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP
    value_list: null
    technical_name: AccountGroup
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for AccountGroup.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/AccountGroup.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    type: SchemaNode
    status: draft
    name: FirstName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME
    value_list: null
    technical_name: FirstName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for FirstName.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/FirstName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    type: SchemaNode
    status: draft
    name: LastName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME
    value_list: null
    technical_name: LastName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for LastName.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/LastName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    type: SchemaNode
    status: draft
    name: OrganizationName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME
    value_list: null
    technical_name: OrganizationName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for OrganizationName.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/OrganizationName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    type: SchemaNode
    status: draft
    name: Country
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY
    value_list: null
    technical_name: Country
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for Country.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/Country.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-CITY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    type: SchemaNode
    status: draft
    name: City
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-CITY
    value_list: null
    technical_name: City
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for City.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateRequest/element/City.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    type: SchemaNode
    status: draft
    name: BusinessPartner
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER
    value_list: null
    technical_name: BusinessPartner
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for BusinessPartner.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/BusinessPartner.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    type: SchemaNode
    status: draft
    name: ProcessingStatus
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    value_list: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS
    technical_name: ProcessingStatus
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for ProcessingStatus.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerCreateResponse/element/ProcessingStatus.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    type: SchemaNode
    status: draft
    name: FullName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME
    value_list: null
    technical_name: FullName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for FullName.
  reason: SchemaNode imported from BusinessPartnerService/schema/BusinessPartnerReadResponse/element/FullName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    type: SchemaNode
    status: draft
    name: parameters
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: null
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    value_list: null
    technical_name: parameters
    data_type: object
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    type: SchemaNode
    status: draft
    name: BusinessPartnerCategory
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY
    value_list: null
    technical_name: parameters.BusinessPartnerCategory
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.BusinessPartnerCategory.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/BusinessPartnerCategory.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    type: SchemaNode
    status: draft
    name: AccountGroup
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP
    value_list: null
    technical_name: parameters.AccountGroup
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.AccountGroup.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/AccountGroup.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    type: SchemaNode
    status: draft
    name: FirstName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME
    value_list: null
    technical_name: parameters.FirstName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for parameters.FirstName.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/FirstName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    type: SchemaNode
    status: draft
    name: LastName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME
    value_list: null
    technical_name: parameters.LastName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for parameters.LastName.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/LastName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    type: SchemaNode
    status: draft
    name: OrganizationName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME
    value_list: null
    technical_name: parameters.OrganizationName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for parameters.OrganizationName.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/OrganizationName.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    type: SchemaNode
    status: draft
    name: Country
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY
    value_list: null
    technical_name: parameters.Country
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.Country.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/Country.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    type: SchemaNode
    status: draft
    name: City
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY
    value_list: null
    technical_name: parameters.City
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for parameters.City.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateInput/part/parameters/element/City.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    type: SchemaNode
    status: draft
    name: BusinessPartner
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER
    value_list: null
    technical_name: parameters.BusinessPartner
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.BusinessPartner.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/BusinessPartner.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    type: SchemaNode
    status: draft
    name: ProcessingStatus
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    value_list: VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS
    technical_name: parameters.ProcessingStatus
    data_type: string
    required: true
    cardinality: 1..1
    description: Imported schema node for parameters.ProcessingStatus.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerCreateOutput/part/parameters/element/ProcessingStatus.
- op: create_object
  object_id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
  object_type: SchemaNode
  target_path: null
  before: null
  after:
    id: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    type: SchemaNode
    status: draft
    name: FullName
    message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
    parent_node: SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS
    business_attribute: ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    field_endpoint: FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME
    value_list: null
    technical_name: parameters.FullName
    data_type: string
    required: false
    cardinality: 0..1
    description: Imported schema node for parameters.FullName.
  reason: SchemaNode imported from BusinessPartnerService/message/BusinessPartnerReadOutput/part/parameters/element/FullName.
- op: create_object
  object_id: IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATE
  object_type: InterfaceEndpoint
  target_path: null
  before: null
  after:
    id: IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATE
    type: InterfaceEndpoint
    status: draft
    name: BusinessPartnerCreate
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    endpoint_type: wsdl_operation
    protocol: soap
    method: CALL
    path: urn:martenweave:example:bp:service/BusinessPartnerCreate
    request_message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT
    response_message_types:
    - MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT
    parameters: null
    message_exchange_pattern: request_response
    description: BusinessPartnerPortType.BusinessPartnerCreate
  reason: Interface endpoint imported from BusinessPartnerService/portType/BusinessPartnerPortType/BusinessPartnerCreate.
- op: create_object
  object_id: IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREAD
  object_type: InterfaceEndpoint
  target_path: null
  before: null
  after:
    id: IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREAD
    type: InterfaceEndpoint
    status: draft
    name: BusinessPartnerRead
    interface: IFACE-SCHEMA-BUSINESSPARTNERSERVICE
    endpoint_type: wsdl_operation
    protocol: soap
    method: CALL
    path: urn:martenweave:example:bp:service/BusinessPartnerRead
    request_message_type: MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT
    response_message_types:
    - MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT
    parameters: null
    message_exchange_pattern: request_response
    description: BusinessPartnerPortType.BusinessPartnerRead
  reason: Interface endpoint imported from BusinessPartnerService/portType/BusinessPartnerPortType/BusinessPartnerRead.
validation_status: valid
validation_results: []
generated_by: schema_import
updated_at: '2026-07-25T08:47:53.699789+00:00'
reviewer: factory-agent
reviewed_at: '2026-07-25T08:48:06Z'
application_status: applied
applied_at: '2026-07-25T08:48:08Z'
applied_by: system
applied_changed_files:
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/entities/ENTITY-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/value-lists/VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/value-lists/VLIST-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/attributes/ATTR-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/field-endpoints/FEP-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/interfaces/IFACE-SCHEMA-BUSINESSPARTNERSERVICE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEINPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEOUTPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATEREQUEST.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATERESPONSE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADINPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADOUTPUT.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADREQUEST.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/MSG-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREADRESPONSE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNERCATEGORY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ACCOUNTGROUP.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FIRSTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-LASTNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-ORGANIZATIONNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-COUNTRY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-CITY.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-BUSINESSPARTNER.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-PROCESSINGSTATUS.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/SNODE-SCHEMA-BUSINESSPARTNERSERVICE-PARAMETERS-FULLNAME.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERCREATE.md
- /Users/dzmitryikharlanau/Developments/martenweave/examples/sap_bp_customer_vendor_reference/model/IEP-SCHEMA-BUSINESSPARTNERSERVICE-BUSINESSPARTNERREAD.md
applied_audit_event_id: audit-07b62c3b567e
---

# Patch Proposal: PP-SCHEMA-9EDF23919A5B701D

## Source Evidence
Schema import evidence from business-partner-service.wsdl (wsdl, checksum 9edf23919a5b701d1d748a2af6b86d8eb21d7547bcd15f1666622e24560b781d, parser 1.0, inspected 2026-07-25T08:47:53Z). Warnings: none.
