# Feature Specification: File Attachment Handling

**Feature Branch**: `001-teams-file-upload`  
**Created**: 2026-01-06  
**Status**: Draft  
**Input**: User description: "Implement file attachment handling in Teams bot. The bot receives file attachments directly in messages, extracts metadata (filename, type, download URL), validates file types (PDF, DOC, DOCX), logs successful uploads, and provides feedback to users."

## User Scenarios & Testing _(mandatory)_

> **Note**: File attachment handling is automatically triggered when users send messages with attachments in Teams. Testing requires access to a Teams environment with the bot deployed and the ability to send file attachments.

### User Story 1 - Receive and Extract File Metadata (Priority: P1)

A user sends a message with file attachments in Teams. The bot automatically receives the message, extracts the file metadata (filename, file type, and download URL), and processes it without requiring any special commands or user consent workflows.

**Why this priority**: This is the foundation of file handling. Without the ability to receive and extract basic file information, no file processing is possible.

**Independent Test**: A user sends a message with a PDF attachment and the bot successfully receives and logs the attachment metadata.

**Acceptance Scenarios**:

1. **Given** a user sends a message with one or more file attachments, **When** the bot receives the message activity, **Then** the bot should extract the filename, file type, and temporary download URL for each attachment.
2. **Given** extracted file metadata, **When** the bot processes the attachment, **Then** all metadata should be available for validation and logging.

---

### User Story 2 - Validate File Types (Priority: P1)

The bot validates that uploaded files match supported types (PDF, DOC, DOCX). If validation fails, the user receives an immediate notification about unsupported file types.

**Why this priority**: Prevents processing of incompatible file formats and provides clear guidance to users about supported types.

**Independent Test**: User sends a message with both a supported file (PDF) and unsupported file (JPG); bot notifies user that JPG is unsupported.

**Acceptance Scenarios**:

1. **Given** one or more file attachments, **When** the bot validates file types, **Then** it should identify which files are supported (PDF, DOC, DOCX) and which are not.
2. **Given** one or more unsupported files, **When** validation completes, **Then** the bot should send a message to the user specifying which file types are not supported.
3. **Given** mixed valid and invalid files, **When** validation completes, **Then** the bot should continue processing only the valid files and notify the user about the invalid ones.

---

### User Story 3 - Log and Confirm Successful Processing (Priority: P2)

After validating file types, the bot logs the successful file processing to application logs and sends a confirmation message to the user.

**Why this priority**: Essential for audit trail and user confirmation that files were received and accepted.

**Independent Test**: User sends a valid PDF file; bot logs the event and sends a success confirmation message.

**Acceptance Scenarios**:

1. **Given** successfully validated files, **When** the bot completes processing, **Then** it should write an entry to the application log with filename and timestamp.
2. **Given** successfully validated files, **When** the bot completes processing, **Then** it should send a confirmation message to the user listing the accepted filenames.

---

### Edge Cases

- **Multiple Attachments with Mixed Types**: User sends 3 files - one PDF, one DOC, one JPG. Bot should accept PDF and DOC, reject JPG, and notify user of the rejection.
- **No Attachments in Message**: User sends a message without attachments. Bot should not attempt file processing.
- **Empty or Corrupted Attachments**: If attachment metadata cannot be extracted, bot should log the error and notify the user.
- **Expired Download URL**: If download URL expires before processing, bot should handle gracefully and notify user.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST detect and extract file attachments from incoming message activities in Teams.
- **FR-002**: For each attachment, the system MUST extract and store: filename, file type (MIME type), and temporary download URL provided by Teams.
- **FR-003**: System MUST validate that all attachments have file types matching the supported list: PDF, DOC, DOCX (identified by extension or MIME type).
- **FR-004**: System MUST provide feedback to the user about validation results (which files are accepted, which are rejected, and why).
- **FR-005**: System MUST log successful file processing to the application logger, including filename, file type, timestamp, and originating user.
- **FR-006**: File attachment handling logic MUST be implemented in a shared module (e.g., `src/utils/file_handler.py` or extended `genie_manager.py`) to enable reuse across multiple bot classes including FoundryBot.
- **FR-007**: System MUST NOT require file consent workflows, special upload commands, or state tracking - file attachments are processed directly from message activities.

### Key Entities

- **FileAttachment**: Represents a file received in a Teams message, containing filename, file type, and temporary download URL.
- **ValidationResult**: Represents the outcome of file type validation, indicating whether each file is supported or rejected with reason.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: 100% of file attachments with supported types (PDF, DOC, DOCX) are successfully processed and logged.
- **SC-002**: File validation completes and user feedback is delivered within 2 seconds of message receipt.
- **SC-003**: The file attachment handling logic is decoupled from any specific bot class and can be integrated into another bot type with less than 1 hour of additional development effort.
- **SC-004**: All file processing events are logged with filename, file type, timestamp, and user information for audit purposes.
