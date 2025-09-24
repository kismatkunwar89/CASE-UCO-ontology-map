Ontology Research Report
Input Text

{
  "event": "User logged in",
  "user": "admin",
  "timestamp": "2023-10-01T12:00:00Z",
  "ip_address": "192.168.1.1",
  "process": "login.exe",
  "file": "user_data.txt"
}
Summary Identified Artifacts: User Account, Process, File, Network Connection

Relevant CASE/UCO Classes (Objects): UserAccount, Process, File, NetworkConnection

Applicable Facets (Property Bundles): ProcessFacet, FileFacet, NetworkConnectionFacet

Class Properties: accessedTime, fileName, filePath, pid, arguments, destinationPort, src, startTime

Facet Properties: isHidden, exitStatus, sizeInBytes, protocols, isActive

Relationship Patterns:

UserAccount → LoggedIn → Process
Process → Accessed → File
NetworkConnection → Established → UserAccount
Mapping Rationale

Artifact Identification: The input describes a user login event, confirmed by the presence of the user "admin" and the process "login.exe".
UserAccount: Because the input contains a user key, I selected the UserAccount class to represent the entity logging in.
Process: Because the input contains the process "login.exe", I selected the Process class to represent the execution of the login action.
File: Because the input mentions "user_data.txt", I selected the File class to represent the file accessed during the login.
NetworkConnection: Because the input includes an IP address, I selected the NetworkConnection class to represent the network activity associated with the login.
Detailed Class & Facet Documentation Classes (Observable Objects)

UserAccount
# UserAccount

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/UserAccount`

**Description:** A user account is an account that allows a user to access a computer system or network.

## Superclasses (5)

1. UcoThing
2. ObservableObject
3. Item
4. UcoObject
5. Observable

## Property Shapes

By the associated SHACL property shapes, instances of UserAccount can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **UserAccountFacet** | | | | | | |
| username | DatatypeProperty | The name of the user account. | 1 | 1 | string | None |
| password | DatatypeProperty | The password associated with the user account. | 1 | 1 | string | None |
| email | DatatypeProperty | The email address associated with the user account. | 0 | 1 | string | None |
| lastLogin | DatatypeProperty | The date and time of the last login. | 0 | 1 | dateTime | None |
| status | DatatypeProperty | The status of the user account (active, inactive). | 1 | 1 | string | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created the user account. | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of the user account. | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the user account. | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a user account. | None | None | Facet | Facet |
| name | DatatypeProperty | The name of the user account. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 6
- **Facet Properties:** 1
- **Inherited Properties:** 5
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to UserAccountFacet
Process
# Process

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/Process`

**Description:** A process is an instance of a computer program executed on an operating system.

## Superclasses (5)

1. UcoThing
2. ObservableObject
3. Item
4. UcoObject
5. Observable

## Property Shapes

By the associated SHACL property shapes, instances of Process can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **ProcessFacet** | | | | | | |
| arguments | DatatypeProperty | A list of arguments utilized in initiating the process. | None | None | string | None |
| binary | ObjectProperty | binary property | None | 1 | ObservableObject | ObservableObject |
| creatorUser | ObjectProperty | The user that created/owns the process. | None | 1 | ObservableObject | ObservableObject |
| currentWorkingDirectory | DatatypeProperty | currentWorkingDirectory property | None | 1 | string | None |
| environmentVariables | ObjectProperty | A list of environment variables associated with the process. | None | 1 | Dictionary | Dictionary |
| exitStatus | DatatypeProperty | A small number passed from the process to the parent process. | None | 1 | integer | None |
| exitTime | DatatypeProperty | The time at which the process exited. | None | 1 | dateTime | None |
| isHidden | DatatypeProperty | The isHidden property specifies whether the process is hidden. | None | 1 | boolean | None |
| observableCreatedTime | DatatypeProperty | The date and time at which the observable object was created. | None | 1 | dateTime | None |
| parent | ObjectProperty | The process that created this process. | None | 1 | ObservableObject | ObservableObject |
| pid | DatatypeProperty | The Process ID, or PID, of the process. | None | 1 | integer | None |
| status | DatatypeProperty | Specifies a list of statuses for a given process. | None | 1 |  | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a process. | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characterization. | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the process. | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a process. | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 25
- **Facet Properties:** 12
- **Inherited Properties:** 13
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to ProcessFacet
File
# File

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/File`

**Description:** A file is a computer resource for recording data discretely on a computer storage device.

## Superclasses (6)

1. UcoThing
2. ObservableObject
3. FileSystemObject
4. Item
5. Observable
6. UcoObject

## Property Shapes

By the associated SHACL property shapes, instances of File can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **FileFacet** | | | | | | |
| accessedTime | DatatypeProperty | The date and time at which the Object was accessed. | None | 1 | dateTime | None |
| allocationStatus | DatatypeProperty | The allocation status of a file. | None | 1 | string | None |
| extension | DatatypeProperty | The file name extension: everything after the last dot in the file name. | None | 1 | string | None |
| fileName | DatatypeProperty | Specifies the name associated with a file in a file system. | None | None | string | None |
| filePath | DatatypeProperty | Specifies the file path for the location of a file in a file system. | None | None | string | None |
| isDirectory | DatatypeProperty | Specifies whether a file entry represents a directory. | None | None | boolean | None |
| metadataChangeTime | DatatypeProperty | The date and time at which the file metadata was last modified. | None | 1 | dateTime | None |
| modifiedTime | DatatypeProperty | The date and time at which the Object was last modified. | None | 1 | dateTime | None |
| observableCreatedTime | DatatypeProperty | The date and time at which the observable object was created. | None | 1 | dateTime | None |
| sizeInBytes | DatatypeProperty | The size of the data in bytes. | None | 1 | integer | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a file. | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characterization. | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the file. | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a file. | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 82
- **Facet Properties:** 10
- **Inherited Properties:** 72
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to FileFacet
NetworkConnection
# NetworkConnection

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/NetworkConnection`

**Description:** A network connection is a connection (completed or attempted) across a digital network (a group of two or more computer systems linked together).

## Superclasses (5)

1. UcoThing
2. ObservableObject
3. Item
4. UcoObject
5. Observable

## Property Shapes

By the associated SHACL property shapes, instances of NetworkConnection can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **NetworkConnectionFacet** | | | | | | |
| destinationPort | DatatypeProperty | Specifies the destination port used in the connection. | None | 1 | integer | None |
| dst | ObjectProperty | Specifies the destination(s) of the network connection. | None | None | ObservableObject | ObservableObject |
| endTime | DatatypeProperty | endTime property | None | 1 | dateTime | None |
| isActive | DatatypeProperty | Indicates whether the network connection is still active. | None | 1 | boolean | None |
| protocols | ObjectProperty | Specifies the protocols involved in the network connection. | None | 1 | ControlledDictionary | ControlledDictionary |
| sourcePort | DatatypeProperty | Specifies the source port used in the connection, if applicable. | None | 1 | integer | None |
| src | ObjectProperty | Specifies the source(s) of the network connection. | None | None | UcoObject | UcoObject |
| startTime | DatatypeProperty | startTime property | None | 1 | dateTime | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a network connection. | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characterization. | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the network connection. | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a network connection. | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 14
- **Facet Properties:** 8
- **Inherited Properties:** 6
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to NetworkConnectionFacet
Facet Associations

Process: ProcessFacet — captures specific details about the process execution.
File: FileFacet — captures specific details about the file accessed.
NetworkConnection: NetworkConnectionFacet — captures specific details about the network connection.
Relationship Patterns Object-to-Facet Relationships:

UserAccount → hasFacet → UserAccountFacet — to characterize the user account.
Process → hasFacet → ProcessFacet — to characterize the process.
File → hasFacet → FileFacet — to characterize the file.
NetworkConnection → hasFacet → NetworkConnectionFacet — to characterize the network connection.
Object-to-Object Relationships:

UserAccount → LoggedIn → Process — the user logged in using the process.
Process → Accessed → File — the process accessed the file.
NetworkConnection → Established → UserAccount — the network connection was established by the user account.
{
  "artifacts": ["User Account", "Process", "File", "Network Connection"],
  "classes": ["UserAccount", "Process", "File", "NetworkConnection"],
  "facets": ["ProcessFacet", "FileFacet", "NetworkConnectionFacet"],
  "properties": {
    "UserAccount": ["username", "password", "email", "lastLogin", "status"],
    "Process": ["arguments", "binary", "creatorUser", "currentWorkingDirectory", "environmentVariables"],
    "File": ["accessedTime", "allocationStatus", "extension", "fileName", "filePath"],
    "NetworkConnection": ["destinationPort", "dst", "endTime", "isActive", "protocols"]
  },
  "relationships": [
    {
      "type": "hasFacet",
      "source": "UserAccount",
      "target": "UserAccountFacet"
    },
    {
      "type": "hasFacet",
      "source": "Process",
      "target": "ProcessFacet"
    },
    {
      "type": "hasFacet",
      "source": "File",
      "target": "FileFacet"
    },
    {
      "type": "hasFacet",
      "source": "NetworkConnection",
      "target": "NetworkConnectionFacet"
    },
    {
      "type": "ObservableRelationship",
      "source": "UserAccount",
      "target": "Process",
      "kind": "LoggedIn",
      "directional": true
    },
    {
      "type": "ObservableRelationship",
      "source": "Process",
      "target": "File",
      "kind": "Accessed",
      "directional": true
    },
    {
      "type": "ObservableRelationship",
      "source": "NetworkConnection",
      "target": "UserAccount",
      "kind": "Established",
      "directional": true
    }
  ],
  "analysis": "The analysis identifies the user account, process, file, and network connection involved in the login event. Each class and facet is justified based on the input data.",
  "additional_details": {
    "note": "The relationships reflect the interactions between the identified objects."
  }
}
95.50s
11,014
