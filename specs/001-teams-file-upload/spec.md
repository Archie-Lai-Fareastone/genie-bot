# Feature Specification: Upload file handling

**Feature Branch**: `001-teams-file-upload`  
**Created**: 2026-01-06  
**Status**: Draft  
**Input**: User description: "build a new feature 'Upload file handling' in addition to existing teams bot. scope: Apply the feature to FoundryBot but other bots may need the feature in the future, so prefer adding the logic to shared modules. success criteria: User can upload file via teams (saved to one drive). Teams bot is able to get the read permission of the file uploaded. constraints: authentication: the bot uses service principal to access azure resources. user journey: 1. teams bot prompt user to upload file 2. user upload file in teams 3. the file is saved to user's one drive 4. teams bot obtains the one drive file url and permission to read file 5. teams bot send feedback adaptive card to user to tell that file is uploaded"

## User Scenarios & Testing _(mandatory)_

> **Note**: This feature cannot be tested locally as it relies on Teams integration and OneDrive access. It MUST be deployed to a environment accessible by Teams and tested manually by a user.

### User Story 1 - Secure File Upload and Access (Priority: P1)

A user needs to share a document with the bot so the bot can process its content. The user uploads the file directly in the Teams chat, and the bot automatically gains the necessary permissions to read it from the user's OneDrive.

**Why this priority**: This is the core functionality that enables all subsequent file-based features. Without secure upload and read access, the feature provides no value.

**Independent Test**: Can be fully tested by a user uploading a single PDF or text file in Teams and verifying that the bot can retrieve the file metadata and content using its Service Principal credentials.

**Acceptance Scenarios**:

1. **Given** the bot has prompted for a file, **When** the user uploads a file and grants consent, **Then** the bot should receive a `fileConsentAccept` event with the download URL.
2. **Given** a valid file download URL, **When** the bot attempts to read the file using the Service Principal, **Then** the file content should be successfully retrieved.

---

### User Story 2 - Upload Confirmation Feedback (Priority: P2)

After a user successfully uploads a file, the bot should provide immediate and clear feedback confirming that the file has been received and is being processed.

**Why this priority**: Essential for a good user experience, ensuring the user knows their action was successful and what to expect next.

**Independent Test**: Can be tested by observing the Adaptive Card response sent by the bot immediately after the `fileConsentAccept` event is processed.

**Acceptance Scenarios**:

1. **Given** a successful file upload and permission grant, **When** the bot completes the initial retrieval, **Then** it must send an Adaptive Card containing the file name and a success message.

---

### Edge Cases

- **User Declines Consent**: If the user declines the file upload consent in Teams, the bot should handle the `fileConsentDecline` event gracefully and notify the user that the operation was cancelled.
- **File Too Large**: If the file exceeds OneDrive or Teams upload limits, the bot should handle the error and provide a meaningful message to the user.
- **Network Timeout**: If the connection to OneDrive fails during the read operation, the bot should retry or inform the user of the temporary failure.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST be able to send a File Consent Card to the user to initiate the upload process.
- **FR-002**: System MUST implement handlers for `fileConsentAccept` and `fileConsentDecline` invoke activities.
- **FR-003**: System MUST use the Service Principal's credentials to authenticate with Microsoft Graph API for file access.
- **FR-004**: System MUST be able to download the file content from the provided OneDrive download URL.
- **FR-005**: System MUST support common document file types including PDF, DOC, and DOCX.
- **FR-006**: The file upload logic MUST be implemented in a shared module (e.g., `src/utils/genie_manager.py` or a new `file_handler.py`) to allow use by multiple bot types.

### Key Entities

- **UploadRequest**: Represents the initial request from the bot to the user to upload a file, identified by a unique ID.
- **UploadedFile**: Represents the file metadata received from Teams, including name, content type, download URL, and unique ID.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: 100% of successfully consented files are readable by the bot via the Service Principal.
- **SC-002**: The feedback Adaptive Card is delivered to the user within 3 seconds of the bot receiving the consent acceptance.
- **SC-003**: The implementation logic is decoupled from `FoundryBot` such that it can be integrated into another bot class with less than 2 hours of additional development effort.
