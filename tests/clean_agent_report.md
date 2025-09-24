# Ontology Research Report

## Input Text

```json
{
  "artifact_type": "MFT Records",
  "description": "Master File Table records containing filesystem metadata and file system structure information",
  "source": "NTFS filesystem analysis",
  "records": [
    {
      "EntryNumber": 42,
      "SequenceNumber": 3,
      "ParentEntryNumber": 5,
      "FullPath": "\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf",
      "InUse": true,
      "SI_Created": "2025-09-17T10:30:00Z",
      "SI_Modified": "2025-09-17T10:35:15Z",
      "SI_Accessed": "2025-09-17T10:35:15Z",
      "FN_Created": "2025-09-17T10:30:00Z",
      "FN_Modified": "2025-09-17T10:35:15Z"
    },
    {
      "EntryNumber": 314,
      "SequenceNumber": 1,
      "ParentEntryNumber": 200,
      "FullPath": "\\Users\\Alice\\Documents\\report.docx",
      "InUse": true,
      "SI_Created": "2024-10-05T09:12:00Z",
      "SI_Modified": "2025-01-20T16:33:11Z",
      "SI_Accessed": "2025-01-22T07:02:45Z",
      "FN_Created": "2024-10-05T09:12:00Z",
      "FN_Modified": "2025-01-20T16:33:11Z"
    }
  ]
}
```

## Summary

**Identified Artifacts:** MFT Records

**Forensic Significance:** Master File Table records containing filesystem metadata and file system structure information

**Relevant CASE/UCO Classes (Objects):** File, FileSystemObject, NTFSFile, FileSystem

**Applicable Facets (Property Bundles):** MftRecordFacet, FileFacet

**Class Properties:** accessedTime, allocationStatus, extension, fileName, filePath, isDirectory, metadataChangeTime, modifiedTime, observableCreatedTime, sizeInBytes, createdBy, description, externalReference, hasFacet, name, tag, accessedFile, applicationFileName, archiveType, browserUserProfile, characteristics, clusterSize, contactProfile, contactProfilePlatform, entryID, execProgramHashes, execProgramPath, execWorkingDirectory, extDeletionTime, extFileType, extFlags, extInodeChangeTime, extPermissions, extSGID, extSUID, favoritesCount, fileAlignment, fileHeaderHashes, fileSystemType, followersCount, friendsCount, isMapped, listedCount, mftFileID, mftFileNameAccessedTime, mftFileNameCreatedTime, mftFileNameLength, mftFileNameModifiedTime, mftFileNameRecordChangeTime, mftFlags, mftParentID, mftRecordChangeTime, ntfsHardLinkCount, ntfsOwnerID, ntfsOwnerSID, openFileDescriptor, pointerToSymbolTable, profile, profileAccount, profileBackgroundHash, profileBackgroundLocation, profileBannerHash, profileBannerLocation, profileCreated, profileIdentity, profileImageHash, profileImageLocation, profileIsProtected, profileIsVerified, profileLanguage, profileService, profileWebsite, rangeOffsetType, sections, sizeOfHeaders, statusesCount, targetFile, twitterHandle, twitterId, userLocationString, volume, windowsTempDirectory

**Facet Properties:** createdBy, description, externalReference, hasFacet, name, tag

**Relationship Patterns:** Object-to-Facet relationships via hasFacet

## Mapping Rationale

**Artifact Identification:** The input is MFT Records records, confirmed by the presence of MFT Records in the artifact_type field.

## Detailed Class & Facet Documentation

### Classes (Observable Objects)

#### File

# File

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/File`

**Description:** A file is a computer resource for recording data discretely on a computer storage device.

## Superclasses (6)

1. UcoThing
2. Observable
3. UcoObject
4. ObservableObject
5. Item
6. FileSystemObject

## Property Shapes

By the associated SHACL property shapes, instances of File can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **FileFacet** | | | | | | |
| accessedTime | DatatypeProperty | The date and time at which the Object was accessed... | None | 1 | dateTime | None |
| allocationStatus | DatatypeProperty | The allocation status of a file. | None | 1 | string | None |
| extension | DatatypeProperty | The file name extension: everything after the last... | None | 1 | string | None |
| fileName | DatatypeProperty | Specifies the name associated with a file in a fil... | None | None | string | None |
| filePath | DatatypeProperty | Specifies the file path for the location of a file... | None | None | string | None |
| isDirectory | DatatypeProperty | Specifies whether a file entry represents a direct... | None | None | boolean | None |
| metadataChangeTime | DatatypeProperty | The date and time at which the file metadata was l... | None | 1 | dateTime | None |
| modifiedTime | DatatypeProperty | The date and time at which the Object was last mod... | None | 1 | dateTime | None |
| observableCreatedTime | DatatypeProperty | The date and time at which the observable object b... | None | 1 | dateTime | None |
| sizeInBytes | DatatypeProperty | The size of the data in bytes. | None | 1 | integer | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |
| **Semantic** | | | | | | |
| accessedFile | ObjectProperty | Files (e.g., DLLs and other support files) used by... | None | None | ObservableObject | ObservableObject |
| applicationFileName | DatatypeProperty | Name of the executable of the prefetch file. | None | 1 | string | None |
| archiveType | DatatypeProperty | The type of a file archive, e.g. ZIP, GZIP or RAR. | None | 1 | string | None |
| browserUserProfile | DatatypeProperty | Specifies the web browser user profile for which t... | None | 1 | string | None |
| characteristics | DatatypeProperty | Specifies the flags that indicate the fileâ€™s cha... | None | None | unsignedShort | None |
| clusterSize | DatatypeProperty | The size of cluster allocation units in a file sys... | None | 1 | integer | None |
| contactProfile | ObjectProperty | Contact profile specifies information characterizi... | 0 | None | ContactProfile | ContactProfile |
| contactProfilePlatform | ObjectProperty | A contact profile platform specifies an online ser... | None | 1 | ObservableObject | ObservableObject |
| entryID | DatatypeProperty | A unique identifier for the file within the filesy... | None | 1 | integer | None |
| execProgramHashes | ObjectProperty | Specifies the hashes of the executable file launch... | None | None | Hash | Hash |
| execProgramPath | DatatypeProperty | Specifies the path to the executable file launched... | None | 1 | string | None |
| execWorkingDirectory | DatatypeProperty | Specifies the directory that contains either the e... | None | 1 | string | None |
| extDeletionTime | DatatypeProperty | Specifies the time at which the file represented b... | None | 1 | dateTime | None |
| extFileType | DatatypeProperty | Specifies the EXT file type (FIFO, Directory, Regu... | None | 1 | integer | None |
| extFlags | DatatypeProperty | Specifies user flags to further protect (limit its... | None | 1 | integer | None |
| extInodeChangeTime | DatatypeProperty | The date and time at which the file Inode metadata... | None | 1 | dateTime | None |
| extPermissions | DatatypeProperty | Specifies the read/write/execute permissions for t... | None | 1 | integer | None |
| extSGID | DatatypeProperty | Specifies the group ID for the file represented by... | None | 1 | integer | None |
| extSUID | DatatypeProperty | Specifies the user ID that 'owns' the file represe... | None | 1 | integer | None |
| favoritesCount | DatatypeProperty | Specifies the number of times that this profile ha... | None | 1 | nonNegativeInteger | None |
| fileAlignment | DatatypeProperty | Specifies the factor (in bytes) that is used to al... | None | None | unsignedInt | None |
| fileHeaderHashes | ObjectProperty | Specifies any hashes that were computed for the fi... | None | None | Hash | Hash |
| fileSystemType | DatatypeProperty | The specific type of a file system. | None | 1 | string | None |
| followersCount | DatatypeProperty | Specifies the followers count associated with the ... | None | 1 | nonNegativeInteger | None |
| friendsCount | DatatypeProperty | Specifies the friends count associated with the tw... | None | 1 | nonNegativeInteger | None |
| isMapped | DatatypeProperty | The isMapped property specifies whether or not the... | None | 1 | boolean | None |
| listedCount | DatatypeProperty | Specifies the number of public lists that this pro... | None | 1 | integer | None |
| mftFileID | DatatypeProperty | Specifies the record number for the file within an... | None | 1 | integer | None |
| mftFileNameAccessedTime | DatatypeProperty | The access date and time recorded in an MFT entry ... | None | 1 | dateTime | None |
| mftFileNameCreatedTime | DatatypeProperty | The creation date and time recorded in an MFT entr... | None | 1 | dateTime | None |
| mftFileNameLength | DatatypeProperty |  Specifies the length of an NTFS file name, in uni... | None | 1 | integer | None |
| mftFileNameModifiedTime | DatatypeProperty | The modification date and time recorded in an MFT ... | None | 1 | dateTime | None |
| mftFileNameRecordChangeTime | DatatypeProperty | The metadata modification date and time recorded i... | None | 1 | dateTime | None |
| mftFlags | DatatypeProperty | Specifies basic permissions for the file (Read-Onl... | None | 1 | integer | None |
| mftParentID | DatatypeProperty | Specifies the record number within an NTFS Master ... | None | 1 | integer | None |
| mftRecordChangeTime | DatatypeProperty | The date and time at which an NTFS file metadata w... | None | 1 | dateTime | None |
| ntfsHardLinkCount | DatatypeProperty | Specifies the number of directory entries that ref... | None | 1 | integer | None |
| ntfsOwnerID | DatatypeProperty | Specifies the identifier of the file owner, from t... | None | 1 | string | None |
| ntfsOwnerSID | DatatypeProperty | Specifies the security ID (key in the $SII Index a... | None | 1 | string | None |
| openFileDescriptor | DatatypeProperty | Specifies a listing of the current file descriptor... | None | None | integer | None |
| pointerToSymbolTable | DatatypeProperty | Specifies the file offset of the COFF symbol table... | None | None | hexBinary | None |
| profile | ObjectProperty | A profile specifies a particular online service pr... | None | 1 | ObservableObject | ObservableObject |
| profileAccount | ObjectProperty | Specifies the online service account associated wi... | None | 1 | ObservableObject | ObservableObject |
| profileBackgroundHash | ObjectProperty | Specifies hashes of the background associated with... | 0 | None | Hash | Hash |
| profileBackgroundLocation | ObjectProperty | Specifies the network location of the background a... | None | 1 | ObservableObject | ObservableObject |
| profileBannerHash | ObjectProperty | Specifies hashes of the banner associated with the... | 0 | None | Hash | Hash |
| profileBannerLocation | ObjectProperty | Specifies the network location of the banner assoc... | None | 1 | ObservableObject | ObservableObject |
| profileCreated | DatatypeProperty | Specifies the date and time the profile was create... | None | 1 | dateTime | None |
| profileIdentity | ObjectProperty | Specifies the identity associated with the profile... | None | 1 | Identity | Identity |
| profileImageHash | ObjectProperty | Specifies hashes of the profile image associated w... | 0 | None | Hash | Hash |
| profileImageLocation | ObjectProperty | Specifies the network location of the profile imag... | None | 1 | ObservableObject | ObservableObject |
| profileIsProtected | DatatypeProperty | Specifies whether the twitter profile is protected... | None | 1 | boolean | None |
| profileIsVerified | DatatypeProperty | Specifies whether the twitter profile is verified. | None | 1 | boolean | None |
| profileLanguage | DatatypeProperty | Specifies the language associated with the profile... | 0 | None | string | None |
| profileService | ObjectProperty | Specifies the online service associated with the p... | None | 1 | ObservableObject | ObservableObject |
| profileWebsite | ObjectProperty | Specifies the website URL associated with the prof... | None | 1 | ObservableObject | ObservableObject |
| rangeOffsetType | DatatypeProperty | The type of offset defined for the range (e.g., im... | None | 1 | string | None |
| sections | ObjectProperty | Specifies metadata about the sections in the PE fi... | None | None | WindowsPESection | WindowsPESection |
| sizeOfHeaders | DatatypeProperty | Specifies the combined size of the MS-DOS, PE head... | None | None | unsignedInt | None |
| statusesCount | DatatypeProperty | Specifies the number of tweets that this profile h... | None | 1 | nonNegativeInteger | None |
| targetFile | ObjectProperty | Specifies the file targeted by a symbolic link. | None | 1 | ObservableObject | ObservableObject |
| twitterHandle | DatatypeProperty | Specifies the twitter handle associated with the p... | None | 1 | string | None |
| twitterId | DatatypeProperty | Specifies the twitter id associated with the profi... | None | 1 | string | None |
| userLocationString | DatatypeProperty | Specifies the user-provided location string associ... | None | 1 | string | None |
| volume | ObjectProperty | The volume from which the prefetch application was... | None | 1 | ObservableObject | ObservableObject |
| windowsTempDirectory | ObjectProperty | The Windows_Temp_Directory field specifies the ful... | None | 1 | ObservableObject | ObservableObject |

## Summary

- **Total Properties:** 82
- **Facet Properties:** 10
- **Inherited Properties:** 72
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to FileFacet

#### FileSystemObject

# FileSystemObject

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/FileSystemObject`

**Description:** A file system object is an informational object represented and managed within a file system.

## Superclasses (5)

1. UcoThing
2. Observable
3. UcoObject
4. ObservableObject
5. Item

## Property Shapes

By the associated SHACL property shapes, instances of FileSystemObject can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 6
- **Facet Properties:** 0
- **Inherited Properties:** 6
- **Semantic Properties:** 0
Direct property usage

#### NTFSFile

# NTFSFile

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/NTFSFile`

**Description:** An NTFS file is a New Technology File System (NTFS) file.

## Superclasses (7)

1. UcoThing
2. Observable
3. UcoObject
4. File
5. ObservableObject
6. Item
7. FileSystemObject

## Property Shapes

By the associated SHACL property shapes, instances of NTFSFile can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **NTFSFileFacet** | | | | | | |
| alternateDataStreams | ObjectProperty | alternateDataStreams property | None | None | AlternateDataStream | AlternateDataStream |
| entryID | DatatypeProperty | A unique identifier for the file within the filesy... | None | 1 | integer | None |
| sid | DatatypeProperty | sid property | None | 1 | string | None |
| **File** | | | | | | |
| accessedTime | DatatypeProperty | The date and time at which the Object was accessed... | None | 1 | dateTime | None |
| allocationStatus | DatatypeProperty | The allocation status of a file. | None | 1 | string | None |
| extension | DatatypeProperty | The file name extension: everything after the last... | None | 1 | string | None |
| fileName | DatatypeProperty | Specifies the name associated with a file in a fil... | None | None | string | None |
| filePath | DatatypeProperty | Specifies the file path for the location of a file... | None | None | string | None |
| isDirectory | DatatypeProperty | Specifies whether a file entry represents a direct... | None | None | boolean | None |
| metadataChangeTime | DatatypeProperty | The date and time at which the file metadata was l... | None | 1 | dateTime | None |
| modifiedTime | DatatypeProperty | The date and time at which the Object was last mod... | None | 1 | dateTime | None |
| observableCreatedTime | DatatypeProperty | The date and time at which the observable object b... | None | 1 | dateTime | None |
| sizeInBytes | DatatypeProperty | The size of the data in bytes. | None | 1 | integer | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 19
- **Facet Properties:** 3
- **Inherited Properties:** 16
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to NTFSFileFacet

#### FileSystem

# FileSystem

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/FileSystem`

**Description:** A file system is the process that manages how and where data on a storage medium is stored, accessed and managed. [based on https://www.techopedia.com/definition/5510/file-system]

## Superclasses (5)

1. UcoThing
2. Observable
3. UcoObject
4. ObservableObject
5. Item

## Property Shapes

By the associated SHACL property shapes, instances of FileSystem can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **FileSystemFacet** | | | | | | |
| clusterSize | DatatypeProperty | The size of cluster allocation units in a file sys... | None | 1 | integer | None |
| fileSystemType | DatatypeProperty | The specific type of a file system. | None | 1 | string | None |
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |
| **Semantic** | | | | | | |
| entryID | DatatypeProperty | A unique identifier for the file within the filesy... | None | 1 | integer | None |
| filePath | DatatypeProperty | Specifies the file path for the location of a file... | None | None | string | None |

## Summary

- **Total Properties:** 10
- **Facet Properties:** 2
- **Inherited Properties:** 8
- **Semantic Properties:** 0
- **Usage Pattern:** Use 'hasFacet' property to link to FileSystemFacet

### Facets (Property Bundles)

#### MftRecordFacet

# MftRecordFacet

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/MftRecordFacet`

**Description:** An MFT record facet is a grouping of characteristics unique to the details of a single file as managed in an NTFS (new technology filesystem) master file table (which is a collection of information about all files on an NTFS filesystem). [based on https://docs.microsoft.com/en-us/windows/win32/devnotes/master-file-table]

## Superclasses (3)

1. UcoThing
2. Facet
3. UcoInherentCharacterizationThing

## Property Shapes

By the associated SHACL property shapes, instances of MftRecordFacet can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 6
- **Facet Properties:** 0
- **Inherited Properties:** 6
- **Semantic Properties:** 0
Direct property usage

#### FileFacet

# FileFacet

**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/FileFacet`

**Description:** A file facet is a grouping of characteristics unique to the storage of a file (computer resource for recording data discretely in a computer storage device) on a file system (process that manages how and where data on a storage device is stored, accessed and managed). [based on https://en.wikipedia.org/Computer_file and https://www.techopedia.com/definition/5510/file-system]

## Superclasses (3)

1. UcoThing
2. Facet
3. UcoInherentCharacterizationThing

## Property Shapes

By the associated SHACL property shapes, instances of FileFacet can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **Inherited** | | | | | | |
| createdBy | ObjectProperty | The identity that created a characterization of a ... | None | 1 | IdentityAbstraction | IdentityAbstraction |
| description | DatatypeProperty | A description of a particular concept characteriza... | None | None | string | None |
| externalReference | ObjectProperty | Specifies a reference to a resource outside of the... | 0 | None | ExternalReference | ExternalReference |
| hasFacet | ObjectProperty | Further sets of properties characterizing a concep... | None | None | Facet | Facet |
| name | DatatypeProperty | The name of a particular concept characterization. | 1 | 1 | string | None |
| tag | DatatypeProperty | A generic tag/label. | None | None | string | None |

## Summary

- **Total Properties:** 6
- **Facet Properties:** 0
- **Inherited Properties:** 6
- **Semantic Properties:** 0
Direct property usage

## JSON Output

```json
{
  "artifacts": [
    "MFT Records"
  ],
  "classes": [
    "File",
    "FileSystemObject",
    "NTFSFile",
    "FileSystem"
  ],
  "facets": [
    "MftRecordFacet",
    "FileFacet"
  ],
  "properties": {
    "File": [
      "accessedTime",
      "allocationStatus",
      "extension",
      "fileName",
      "filePath",
      "isDirectory",
      "metadataChangeTime",
      "modifiedTime",
      "observableCreatedTime",
      "sizeInBytes",
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag",
      "accessedFile",
      "applicationFileName",
      "archiveType",
      "browserUserProfile",
      "characteristics",
      "clusterSize",
      "contactProfile",
      "contactProfilePlatform",
      "entryID",
      "execProgramHashes",
      "execProgramPath",
      "execWorkingDirectory",
      "extDeletionTime",
      "extFileType",
      "extFlags",
      "extInodeChangeTime",
      "extPermissions",
      "extSGID",
      "extSUID",
      "favoritesCount",
      "fileAlignment",
      "fileHeaderHashes",
      "fileSystemType",
      "followersCount",
      "friendsCount",
      "isMapped",
      "listedCount",
      "mftFileID",
      "mftFileNameAccessedTime",
      "mftFileNameCreatedTime",
      "mftFileNameLength",
      "mftFileNameModifiedTime",
      "mftFileNameRecordChangeTime",
      "mftFlags",
      "mftParentID",
      "mftRecordChangeTime",
      "ntfsHardLinkCount",
      "ntfsOwnerID",
      "ntfsOwnerSID",
      "openFileDescriptor",
      "pointerToSymbolTable",
      "profile",
      "profileAccount",
      "profileBackgroundHash",
      "profileBackgroundLocation",
      "profileBannerHash",
      "profileBannerLocation",
      "profileCreated",
      "profileIdentity",
      "profileImageHash",
      "profileImageLocation",
      "profileIsProtected",
      "profileIsVerified",
      "profileLanguage",
      "profileService",
      "profileWebsite",
      "rangeOffsetType",
      "sections",
      "sizeOfHeaders",
      "statusesCount",
      "targetFile",
      "twitterHandle",
      "twitterId",
      "userLocationString",
      "volume",
      "windowsTempDirectory"
    ],
    "FileSystemObject": [
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag"
    ],
    "NTFSFile": [
      "alternateDataStreams",
      "entryID",
      "sid",
      "accessedTime",
      "allocationStatus",
      "extension",
      "fileName",
      "filePath",
      "isDirectory",
      "metadataChangeTime",
      "modifiedTime",
      "observableCreatedTime",
      "sizeInBytes",
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag"
    ],
    "FileSystem": [
      "clusterSize",
      "fileSystemType",
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag",
      "entryID",
      "filePath"
    ],
    "MftRecordFacet": [
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag"
    ],
    "FileFacet": [
      "createdBy",
      "description",
      "externalReference",
      "hasFacet",
      "name",
      "tag"
    ]
  },
  "relationships": [
    {
      "type": "hasFacet",
      "source": "File",
      "target": "MftRecordFacet"
    },
    {
      "type": "hasFacet",
      "source": "File",
      "target": "FileFacet"
    },
    {
      "type": "hasFacet",
      "source": "FileSystemObject",
      "target": "MftRecordFacet"
    },
    {
      "type": "hasFacet",
      "source": "FileSystemObject",
      "target": "FileFacet"
    },
    {
      "type": "hasFacet",
      "source": "NTFSFile",
      "target": "MftRecordFacet"
    },
    {
      "type": "hasFacet",
      "source": "NTFSFile",
      "target": "FileFacet"
    },
    {
      "type": "hasFacet",
      "source": "FileSystem",
      "target": "MftRecordFacet"
    },
    {
      "type": "hasFacet",
      "source": "FileSystem",
      "target": "FileFacet"
    }
  ],
  "analysis": "Analysis of MFT Records records with 4 classes and 2 facets",
  "additional_details": {
    "note": "Properties extracted from actual CASE/UCO analysis results"
  }
}
```
