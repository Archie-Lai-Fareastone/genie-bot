# Feature Specification: Upload file handling

**Feature Branch**: `001-teams-file-upload`  
**Created**: 2026-01-06  
**Status**: Draft  
**Input**: User description: "build a new feature 'Upload file handling' in addition to existing teams bot. scope: Apply the feature to FoundryBot but other bots may need the feature in the future, so prefer adding the logic to shared modules. success criteria: User can upload file via teams (saved to one drive). Teams bot is able to get the read permission of the file uploaded. constraints: authentication: the bot uses service principal to access azure resources. user journey: 1. teams bot prompt user to upload file 2. user upload file in teams 3. the file is saved to user's one drive 4. teams bot obtains the one drive file url and permission to read file 5. teams bot send feedback adaptive card to user to tell that file is uploaded"

## User Scenarios & Testing _(mandatory)_

> **Note**: This feature cannot be tested locally as it relies on Teams integration and OneDrive access. It MUST be deployed to a environment accessible by Teams and tested manually by a user.

### User Story 1 - Secure Multiple File Upload and Access (Priority: P1)

A user needs to share one or more documents with the bot so the bot can process their content. The user uploads the files directly in the Teams chat, and the bot automatically gains the necessary permissions to read them from the user's OneDrive.

**Why this priority**: This is the core functionality that enables all subsequent file-based features. Supporting multiple files allows for richer data processing (e.g., comparing documents).

**Independent Test**: Can be fully tested by a user uploading multiple PDF or text files in Teams and verifying that the bot can retrieve the metadata and content for all uploaded files using its Service Principal credentials.

**Acceptance Scenarios**:

1. **Given** the bot has prompted for files, **When** the user uploads multiple files and grants consent for each, **Then** the bot should receive `fileConsentAccept` events for each file with their respective download URLs.
2. **Given** valid file download URLs, **When** the bot attempts to read the files using the Service Principal, **Then** the content of all files should be successfully retrieved.

---

### User Story 2 - Multiple Upload Confirmation Feedback (Priority: P2)

After a user successfully uploads one or more files, the bot should provide immediate and clear feedback confirming all files that have been received and are being processed.

**Why this priority**: Essential for clarity, especially when multiple files are involved, so the user knows exactly which files the bot has successfully accessed.

**Independent Test**: Can be tested by observing the Adaptive Card response sent by the bot after it has processed the `fileConsentAccept` events, ensuring it lists all uploaded files.

**Acceptance Scenarios**:

1. **Given** multiple successful file uploads and permission grants, **When** the bot completes the initial retrieval, **Then** it must send an Adaptive Card containing a list of all file names and a success message.

---

### User Story 3 - Upload Session Management and Recovery (Priority: P2)

The bot needs to handle interrupted upload sessions gracefully, including automatic timeout cleanup, user-initiated cancellation, and the ability to restart failed upload batches.

**Why this priority**: Prevents system from getting stuck in pending states and provides users with control over the upload process.

**Independent Test**: Can be tested by initiating an upload, waiting for timeout, cancelling mid-process, or intentionally declining some files, then verifying state is properly cleaned up and new uploads can be initiated.

**Acceptance Scenarios**:

1. **Given** an upload batch is created, **When** no files are uploaded within the configured timeout (default 3 minutes), **Then** the batch state should be automatically cleared and the user should be able to start a new upload.
2. **Given** an upload is in progress, **When** the user issues a "cancel upload" command, **Then** the current batch state should be cleared immediately and confirmation sent to the user.
3. **Given** an upload batch exists with pending status, **When** the user issues a "force restart upload" command, **Then** the existing batch should be cleared and a new upload process should begin.
4. **Given** a partial upload failure (some files uploaded, some declined), **When** the user attempts to upload again, **Then** they should receive clear guidance on how to restart the process.

---

### Edge Cases

- **User Declines Consent**: If the user declines the file upload consent in Teams, the bot should handle the `fileConsentDecline` event gracefully and notify the user that the operation was cancelled.
- **File Too Large**: If the file exceeds OneDrive or Teams upload limits, the bot should handle the error and provide a meaningful message to the user.
- **Network Timeout**: If the connection to OneDrive fails during the read operation, the bot should retry or inform the user of the temporary failure.
- **Upload Session Timeout**: If the user doesn't complete the upload within the configured timeout period (default 3 minutes), the batch state should be automatically cleared to prevent blocking future uploads.
- **Stuck Pending State**: If a previous upload attempt left the system in a pending state, the user should be able to forcefully restart the upload process using explicit commands.
- **Partial Batch Completion**: If only some files in a batch are successfully uploaded, the user should receive clear feedback and have the option to restart the entire batch.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST be able to send File Consent Cards to the user to initiate the upload process for one or more files.
- **FR-002**: System MUST implement handlers for `fileConsentAccept` and `fileConsentDecline` invoke activities, supporting multiple responses.
- **FR-003**: System MUST use the Service Principal's credentials to authenticate with Microsoft Graph API for file access.
- **FR-004**: System MUST be able to download the content of all consented files from the provided OneDrive download URLs.
- **FR-005**: System MUST support common document file types including PDF, DOC, and DOCX.
- **FR-006**: The file upload logic MUST be implemented in a shared module (e.g., `src/utils/genie_manager.py` or a new `file_handler.py`) to allow use by multiple bot types.
- **FR-007**: System MUST automatically clean up upload batch states that remain pending for longer than the configured timeout period (default: 3 minutes, configurable via `UPLOAD_TIMEOUT_MINUTES` environment variable or settings).
- **FR-008**: System MUST support user-initiated cancellation of ongoing upload batches via explicit commands (e.g., "取消上傳", "cancel upload").
- **FR-009**: System MUST support force restart of upload sessions via explicit commands (e.g., "重新上傳", "upload reset") to clear stuck pending states.
- **FR-010**: System MUST provide clear user feedback when an upload batch is cancelled (manually or by timeout) and guide users on how to start a new upload.

### Configuration Requirements

- **CFG-001**: System MUST read upload timeout configuration from `UPLOAD_TIMEOUT_MINUTES` environment variable, defaulting to 3 minutes if not set.
- **CFG-002**: The timeout value MUST be configurable in `src/core/settings.py` with proper type validation (positive integer).
- **CFG-003**: System MUST log the active timeout configuration on startup for operational visibility.

### Key Entities

- **UploadRequest**: Represents the initial request from the bot to the user to upload files, potentially tracking a batch of files.
- **UploadedFile**: Represents the metadata for a single file received from Teams, including name, content type, download URL, and unique ID.
- **UploadBatchState**: Tracks the state of an upload session including `created_at` timestamp for timeout detection, `status` (pending/completed/cancelled), `expected_files` count, and list of `uploaded_files`.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: 100% of successfully consented files (even when multiple files are uploaded) are readable by the bot via the Service Principal.
- **SC-002**: The feedback Adaptive Card listing all uploaded files is delivered to the user within 3 seconds of the bot processing the final consent acceptance in a batch.
- **SC-003**: The implementation logic is decoupled from `FoundryBot` such that it can be integrated into another bot class with less than 2 hours of additional development effort.
- **SC-004**: Upload batch states that remain pending for longer than the configured timeout are automatically cleaned up within 10 seconds of the timeout expiration.
- **SC-005**: Users can successfully start a new upload process within 2 seconds after cancelling or after a timeout, without encountering "upload in progress" errors.
