What is Transparency in Coverage? What is this tool?
----------------------------------------------------

“In November 2020, the U.S. Department of Health & Human Services (HHS), Department of Labor, and Department of the Treasury issued the Transparency in Coverage Rule. Based on Affordable Care Act (ACA) requirements, it mandates payers post machine-readable files (MRFs) that list in-network rates and out-of-network allowed amounts on a publicly available website by July 1, 2022” \[[Source: Kaiser Permanente's Transparency in Coverage Machine Readable Files page\]](https://healthy.kaiserpermanente.org/northern-california/front-door/machine-readable)

Per the above government departments, this allows "the public to have access to health coverage information that can be used to understand health care pricing and potentially dampen the rise in health care spending.” \[[Source: TiC, a rule by the IRS, the EBSA, and the HHS](https://www.federalregister.gov/documents/2020/11/12/2020-24591/transparency-in-coverage)\]

While a noble and ultimately helpful goal from the federal government, a brief skim through, for instance, Kaiser's MRFs reveal that there are some problems with this ruling. Primarily, there's just too much data! Their most recent in-network MRF for just their North California Region is more than 4 GBs. I can't store a file that large on my computer without major slowdowns, which means that it is useless to me, part of the public that the federal government wants to serve with this ruling. Further, the [schema mandated by the CMS](https://github.com/CMSgov/price-transparency-guide/tree/master/schemas) is in a key-relationship value format. While there are many benefits to JSON/XML schemas, human readability isn't one of them. As far as I am aware, I can't just drop the file into a GUI and start exploring the data, like I can with CSV/TSV files. And while it is worth pointing out that the ruling mandates machine readable files, not human readable files, I think that if the end goal is to allow the public access to this data, then humans will need some kind of tool to read the data.

Those were my thoughts last Friday when I tried to take a look at Kaiser's data. So to that end, I made a (POC) tool over the weekend that converts Kaiser's in-network data into a .db file that can be opened in any SQLite front-end of your choosing. While I am still ironing out some kinks, I wanted to take a second and write out my motivation and the steps I took before jumping back into it. 

(Un)fortunately, the CMS offers a lot of flexibility in how health plans and insurance issuers can format this data. For example, KP uses an optional Table of Contents file, which allowed them to drastically shrink the size of the in-network file itself. The schema also allows for some data to be stored in separate files, the HTTP locations of which have to be provided in the main JSON. Thankfully, Kaiser didn't do that, which cut down on the complexity of my tool greatly, but that _also means that my tool won't be useful for other health plans' files which did opt to provide additional files._ Maybe next weekend!

What is this data?
------------------

If you don't have an insurance background, though, some of the data and some of the decisions that I made in converting key-value data into tabular data might not make sense. Hopefully this section clears up some questions you may have.

### The schema and my design

The following tables are provided by CMS. If a line is crossed out, then Kaiser does not use that field, and I do not parse it out.

#### In-Network File

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **reporting\_entity\_name** | Entity Name | String | The legal name of the entity publishing the machine-readable file. | Yes |
| **reporting\_entity\_type** | Entity Type | String | The type of entity that is publishing the machine-readable file (a group health plan, health insurance issuer, or a third party with which the plan or issuer has contracted to provide the required information, such as a third-party administrator, a health care claims clearinghouse, or a health insurance issuer that has contracted with a group health plan sponsor). | Yes |
| ~**plan\_name**~ | ~Plan Name~ | ~String~ | ~The plan name and name of plan sponsor and/or insurance company.~ | ~No~ |
| ~**plan\_id\_type**~ | ~Plan Id Type~ | ~String~ | ~Allowed values: "EIN" and "HIOS"~ | ~No~ |
| ~**plan\_id**~ | ~Plan ID~ | ~String~ | ~The 10-digit Health Insurance Oversight System (HIOS) identifier, or, if the 10-digit HIOS identifier is not available, the 5-digit HIOS identifier, or if no HIOS identifier is available, the Employer Identification Number (EIN)for each plan or coverage offered by a plan or issuer.~ | ~No~ |
| ~**plan\_market\_type**~ | ~Market Type~ | ~String~ | ~Allowed values: "group" and "individual"~ | ~No~ |
| **in\_network** | In-Network Negotiated Rates | Array | An array of [in-network object types](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#in-network-object) | Yes |
| **provider\_references** | Provider References | Array | An array of [provider reference object types.](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#provider-reference-object) | No  |
| **last\_updated\_on** | Last Updated On | String | The date in which the file was last updated. Date must be in an ISO 8601 format (i.e. YYYY-MM-DD) | Yes |
| **version** | Version | String | The version of the schema for the produced information | Yes |

This describes the preliminary data about Kaiser and starts the nesting for `in_network` and `provider_references`, which contains the actual juicy data. All of the plan data is stored in a separate table of contents file, accessible in\_network on their site. Since Kaiser has the same singular in-networks file for all their plans, for our purposes, the differences between plans is purely differences in deductibles and out-of-pockets. However, another insurance issuer out there can have different rates for each of their plans, which would mean their files could potentially be _n_ times as large, where _n_ is the number of plans that they have.

#### In-Network Object

This type defines an in-network object.

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **negotiation\_arrangement** | Negotiation Arrangement | String | An indication as to whether a reimbursement arrangement other than a standard fee-for-service model applies. Allowed values: "ffs", "bundle", or "capitation" | Yes |
| **name** | Name | String | This is name of the item/service that is offered | Yes |
| **billing\_code\_type** | Billing Code Type | String | Common billing code types. Please see a list of the [currently allowed codes](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#additional-notes-concerning-billing_code_type) at the bottom of this document. | Yes |
| **billing\_code\_type\_version** | Billing Code Type Version | String | There might be versions associated with the `billing_code_type`. For example, Medicare's current (as of 5/24/21) MS-DRG version is 37.2. If there is no version available for the `billing_code_type`, use the current plan's year `YYYY` that is being disclosed. | Yes |
| **billing\_code** | Billing Code | String | The code used by a plan or issuer or its in-network providers to identify health care items or services for purposes of billing, adjudicating, and paying claims for a covered item or service. If a custom code is used for `billing_code_type`, please refer to [custom billing code values](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#additional-notes-concerning-billing_code) | Yes |
| **description** | Description | String | Brief description of the item/service | Yes |
| **negotiated\_rates** | Negotiated Rates | Array | This is an array of [negotiated rate details object types](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#negotiated-rate-details-object) | Yes |
| ~**bundled\_codes**~ | ~Bundled Codes~ | ~Array~ | ~This is an array of~ [~bundle code objects~](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#bundle-code-object)~. This array contains all the different codes in a bundle if~ `~bundle~` ~is selected for~ `~negotiation_arrangement~` | No  |
| ~**covered\_services**~ | ~Covered Service~ | ~Array~ | ~This is an array of~ [~covered services objects~](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#covered-services-object)~. This array contains all the different codes in a capitation arrangement if~ `~capitation~` ~is selected for~ `~negotiation_arrangement~` | No  |

*   `negotiation_arrangement` describes how a provider is being paid for their services. `ffs`/ Fee-for-service indicates that they are paid for each service that they provide (for example, for each x-ray taken, for each medication given, for each night in bed). `capitation`, on the other hand, indicates that the provider is paid a flat rate per month per patient under their care, regardless of if the patient is seen or not. This financially incentivizes providers to get and keep their patients healthy, while FFS incentivizes providers to give as much care to a patient, regardless of if that care is needed. 
*   `billing_code_type` is used to describe what ails the patient or what service is being offered. There are a few bodies that govern codes that describe diagnoses (fever, broken bone, tummy hurts a bit too much for a bit too long) and procedures (Tylenol, a cast and physical therapy, a night of observation in the emergency room), among other things. This, alongside `billing_code_type_version` and `billing_code` can be used as a primary composite key for this object. But that's a little silly, so I also created a `id` column to serve as a primary key for in-network objects. This is helpful because we need to reference this table in `negotiated_rates`, as we will see later.
*   I still have to do some investigation into `bundled_codes`. Doing a `cat 2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.json | grep "bundled_codes" -m 1 -B 1 -A 25` shows us that there are many bundle code objects that are empty except for a `description`, which I don't believe is permissible. For the time being, I am ignoring all `bundled_codes`, but adding in the correctly formatted codes while still ignoring the bad ones is on my TODO list.
*   `negotiated_rates` is another array of data that represents something wholly different from billing codes. It is a weak entity that is dependent on an `in_network` row. I'll explain this more in the next table.
*   Kaiser has no `covered_services`, and I don't understand why. They do have `capitation` `negotiation_arrangement`s so they should have covered services.  
*   Overall, this is easily rearranged into a tabular structure. We needed to add an `id` column, but other than that, no special handling was required.

#### Negotiated Rate Details Object

This type defines a negotiated rate

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **negotiated\_prices** | Negotiated Prices | Array | An array of [negotiated price objects](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#negotiated-price-object) defines information about the type of negotiated rate as well as the dollar amount of the negotiated rate | Yes |
| ~**provider\_groups**~ | ~Provider Groups~ | ~Array~ | ~The~ [~providers object~](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#providers-object) ~defines information about the provider and their associated TIN related to the negotiated price.~ | ~No~ |
| **provider\_references** | Provider References | Array | An array of `provider_group_id`s defined in the [provider reference Object.](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#provider-reference-object) | No  |

#### Negotiated Price Object

The negotiated price object contains negotiated pricing information that the type of negotiation for the covered item or service.

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **negotiated\_type** | Negotiated Type | String | There are a few ways in which negotiated rates can happen. Allowed values: "negotiated", "derived", "fee schedule", "percentage", and "per diem". See [additional notes](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#additional-notes-1). | Yes |
| **negotiated\_rate** | Negotiated Rate | Number | The dollar or percentage amount based on the `negotiation_type` | Yes |
| **expiration\_date** | Expiration Date | String | The date in which the agreement for the `negotiated_price` based on the `negotiated_type` ends. Date must be in an ISO 8601 format (i.e. YYYY-MM-DD). See additional notes. | Yes |
| **service\_code** | Place of Service Code | An array of two-digit strings | The [CMS-maintained two-digit code](https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set) that is placed on a professional claim to indicate the setting in which a service was provided. When attribute of `billing_class` has the value of "professional", `service_code` is required. | No  |
| **billing\_class** | Billing Class | String | Allowed values: "professional", "institutional", "both" | Yes |
| **billing\_code\_modifier** | Billing Code Modifier | Array | An array of strings. There are certain billing code types that allow for modifiers (e.g. The CPT coding type allows for modifiers). If a negotiated rate for a billing code type is dependent on a modifier for the reported item or service, then an additional negotiated price object should be included to represent the difference. | No  |
| ~**additional\_information**~ | ~Additional Information~ | ~String~ | ~The additional information text field can be used to provide context for negotiated arrangements that do not fit the existing schema format. Please open a Github discussion to ask a question about your situation if you plan to use this attribute.~ | No  |

I describe these tables together because `negotiated_prices` isn't anything on its own: I ended up unpacking it in my `negotiated_rates` SQL table. I will describe provider data soon.

*   `negotiated_type` lines up somewhat with `negotiation_arrangement`. CMS's additional notes on it in their repository does a better job than I would at describing what these are.
*   `negotiated_rate` is the juicy bit here, in my opinion. How much are providers receiving for a given service?
*   `expiration_date` lets us know when this negotiation expires. At that point, the provider group and Kaiser will need to renegotiate rates for this billing code (a.k.a `in_network` row), if desired.
*   `service_code` is used when a provider is submitting a claim, rather than an institution like a hospital. It details the location service was given.
*   When a provider submits a claim directly, the claim has a `billing_class` of `professional`. If an institution such as a hospital submits the claim, its an `institutional` claim.
*   The description provided by CMS for `billing_code_modifier` is pretty good. An example can be when multiple providers performed the service, or when a smaller or larger amount of a drug is given than usual.
*   Kaiser didn't find the need to add `additional_information`, fortunately.

#### Provider Reference Object

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **provider\_group\_id** | Provider Group Id | Number | The unique, primary key for the associated `provider_group` object | Yes |
| **provider\_groups** | Provider Groups | Array | The [providers object](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#providers-object) defines information about the provider and their associated TIN related to the negotiated price. | No  |
| **location** | Location | String | A fully qualified domain name on where the provider group data can be downloaded. The file must validate against the requirements found in the [provider reference](https://github.com/CMSgov/price-transparency-guide/tree/master/examples/provider-reference). Examples can be found [here](https://github.com/CMSgov/price-transparency-guide/blob/574caa73dd0a1f49c7b4696f585dc6f8b087d67a/examples/in-network-rates/in-network-rates-fee-for-service-single-plan-sample.json#L25-L28) that would link to a valid provider reference file such as one found [here](https://github.com/CMSgov/price-transparency-guide/blob/master/examples/provider-reference/provider-reference.json). | No  |

#### Providers Object

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **npi** | NPI | Array | An array of National Provider Identifiers (NPIs). The NPI array attribute can contain a mix of Type 1 and Type 2 NPIs, both of which must be provided, if available. In contractual arrangements with Type 2 NPIs where Type 1 NPIs are unknown or otherwise unavailable, only the Type 2 NPIs must be reported. | Yes |
| **tin** | Tax Identification Number | Object | The [tax identifier object](https://github.com/CMSgov/price-transparency-guide/blob/master/schemas/in-network-rates/README.md#tas-identifier-object) contains tax information on the place of business | Yes |

#### Tax Identifier Object

| Field | Name | Type | Definition | Required |
| --- | --- | --- | --- | --- |
| **type** | Type | String | Allowed values: "ein" and "npi". | Yes |
| **value** | Value | String | Either the unique identification number issued by the Internal Revenue Service (IRS) for type "ein" or the provider's npi for type "npi". | Yes |

Once again, I'm describing these three tables together because they are all very similar conceptually. I ended up breaking them into two SQL tables, `provider_group` and `provider`. 

*   `provider_groups` are groups of providers. As a group, these providers negotiate rates with insurance issuers, giving them more bargaining power. Legally speaking, they don't need to have any similarities, but in practice they often share locations or provide similar services. Importantly, they all share a single Tax Identification Number, a.k.a a `tin`. The `tin` is either the group's employer identification number (`ein`) or, when relevant, their `npi` as a drop-in for their SSN, which would be personally identifiable information and shouldn't be publicly available.
*   Because a providers object can have so many `npi`s, and because SQLite doesn't allow for lists as a data type, I decided to make each `npi` a row in its own table, which links to `provider_group` via the `provider_group_id`.

Technical Details
-----------------

I'd also like to talk about some of the engineering decisions I made in creating this tool and how I researched the file. Future employers. look here!

### Research and Development

I almost exclusively used the [in-network readme.md file](https://github.com/CMSgov/price-transparency-guide/tree/master/schemas/in-network-rates) to structure my tool. The .json examples that CMS provides were more for type validation than data parsing, in my opinion, and the inability to quickly view the structure of nested arrays made it difficult to use for my needs. 

I also heavily relied on one of Kaiser's files itself. I mentioned earlier that I couldn't open the file in memory. Fortunately, it turns out that [grep](https://www.gnu.org/software/grep/manual/grep.html) reads files line by line, and as such could parse through the entire 4 GBs in about seconds I was able to gleam a lot of data into Kaiser's structure by doing this. For instance, provider group data can optionally be uploaded at a different `location` rather than be provided on the main file itself. If that's the case, then there will be no `provider_groups` key. A quick `cat 2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.json | grep “location:” | wc -l` proves to us that they don't use `location` and, just for sanity's sake, `cat 2024-04-01_KFHP_NC-COMMERCIAL_in-network-rates.json | grep provider_groups | wc -l` confirms that there are 5419 provider groups within the file itself, as expected.

[ijson](https://pypi.org/project/ijson/) is an incredibly easy-to-use python library to parse a JSON object bit by bit. Rather than ingesting the entire JSON object at once, which would be impossible for my computer, ijson instead iterates through each key:value pair. If a value is an array, then it parses through each key-prefixed value:value element pair. Once a key:value pair starts or is complete, it sends a `start_array` or `start_map`' event or an `end_array` or `end_map` event, respectively, which can be used to drive logic. 

### Language Choice and ORM vs Query Building

I initially wanted to use Rust to develop this tool as an excuse to further learn the language. Looking into it, it seemed a natural choice: since I knew the schema of the data ahead of time, I could map the data to a `hashmap` and thus also include some kind of data validation into the tool for free. I eventually realized, though, that going that route would require storing the entire JSON in memory at once which was a non-starter. In a fit of disillusionment and disinflation, I figured that if I couldn't have all the cool features, I may as well go with what I know best: Python. Since ijson uses C by default to parse, performance was likely similar enough and development time would be much faster. Another time, Rust.

I also decided to build out my queries in SQL rather than using an ORM. In almost all online discussions I've read about this, people recommend ORMs over query builders for this kind of a use case. However, as a fledgling technical solutions engineer looking to break into the data field, I need to practice my SQL skills. Now, one might argue that writing a couple of basic CREATE TABLE and INSERT INTO template strings that then take in placeholder variables barely constitutes practicing SQL.

Conclusion
----------

Overall, developing this tool was interesting and fun. ijson's iterator made it very easy once I realized that I was  looking for events and keys in the same structure as the file itself. Building in a full validation tool, and generalizing the tool to all possible JSON files, would be good next steps. This would allow us to compare data across insurance issuers, giving even more insight to the public about healthcare costs in the US.