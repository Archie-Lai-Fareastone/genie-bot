# Research: File Attachment Handling in Teams Bot

## Findings

### Attachment Detection & Metadata Extraction

In Microsoft Teams, file attachments are present in the `activity.attachments` list. When a user uploads a file, the `contentType` of the attachment is set to `application/vnd.microsoft.teams.file.download.info`.

Relevant fields:

- `attachment.name`: The original filename.
- `attachment.content`: A dictionary containing Teams-specific metadata.
  - `downloadUrl`: The temporary URL to download the file.
  - `fileType`: The file extension or type (e.g., "pdf").
  - `uniqueId`: A unique identifier for the file.

### File Type Validation

The requirements specify supporting PDF, DOC, and DOCX.

- **MIME Types**:
  - `application/pdf`
  - `application/msword` (.doc)
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (.docx)
- **Extensions**: `.pdf`, `.doc`, `.docx`

The bot should check both the filename extension and the MIME type for robustness.

### Logging Integration

The project uses a standard logging wrapper in `src/core/logger_config.py`. Successful file processing should be logged at the `INFO` level, while failures should be logged at the `ERROR` level with stack traces.

## Decisions

- **Decision 1**: Implement a new utility class `FileHandler` in `src/utils/file_handler.py`.
  - **Rationale**: Keeps the bot logic clean and allows other bots to easily reuse the functionality as required.
- **Decision 2**: Use a whitelist-based validation approach for file extensions and MIME types.
  - **Rationale**: Provides better security and ensures only supported document types are processed.
- **Decision 3**: Feedback will be sent via plain text messages for simplicity, as per the revised user journey.

## Alternatives Considered

- **Alternative**: Using Microsoft Graph API to download files from OneDrive.
- **Rejected**: The user specifically requested to remove Graph API integration and use the direct `downloadUrl` provided by Teams to simplify the process.
- **Alternative**: Using `FileConsentCard`.
- **Rejected**: The user requested a more direct "drag-and-drop" experience without explicit consent steps.
