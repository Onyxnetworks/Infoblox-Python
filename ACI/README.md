# Contract Deployment Script
### Use Case:
* Create contracts, subjects & filters.
* Add filters to existing subjects.
* Consume & Provide contracts on Internal or External EPG's.
* Can be run against DC1/DC2/LAB.
* Can be used to only provide, consume or add filter or all three.
### Script caveats:
* Contracts & Filters must exist in common tenant.
* Contracts & Filters must be unique.
* Internal & External EPG's must already exist.
* Must be used with the CONTRACT_DEPLOYMENT_EXCEL_TEMPLATE.xlsx.
* Only one EPG can be populated in the Consume/Provide fields.
* Cant be used on the DTE Tenant
### Excel Example:
![Excel Example](/Docs/Images/EXCEL_EXAMPLE.PNG)

# EPG Contract Search Script
### Use Case:
* Used to search internal & external EPG's to show a list of consumed and provided contracts.

# EPG IP Search Script
### Use Case:
* Used to list all active IP addresses for an Internal EPG.

# External EPG Additions Script
### Use Case:
* Used to create new External EPG's and add subnets to new or existing external EPG's.
* Provide error checking against EPG naming and to ensure the same subnets are not added to multiple EPG's within the same VRF.
* Add Virtual Server EPGs and import/export subnets under DCI and INET L3Outs.
### Script Caveats:
* L3Outs must exist in the common tenant.
* Cant be used on the DTE Tenant
* Must be used with the CONTRACT_DEPLOYMENT_EXCEL_TEMPLATE.xlsx.

# Find Endpoint Internal External Script
### Use Case:
* Search by IP Address/Network and list the EPG (Internal/External) this is located in.
* Select Y to "Filter Migration L3Outs" option to remove all of the any any Network Centric migrations.

# List IPG Mapped to EPGs Script
### Use Case:
* Search by IPG Name to display all of the vlans that are mapped as static bindings for this IPG.

### Script caveats:
* May not display correctly when using the generic "ACCESS" IPG 
