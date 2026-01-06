# Data Model: File Attachment Handling

## Entities

### `FileAttachmentInfo` (Internal Metadata)

Represents the extracted information from a Teams attachment activity.

| Field          | Type    | Description                                                |
| -------------- | ------- | ---------------------------------------------------------- |
| `name`         | string  | The original filename (e.g., "report.pdf")                 |
| `download_url` | string  | The temporary URL provided by Teams to download the file   |
| `file_type`    | string  | The MIME type or extension reported by Teams               |
| `is_supported` | boolean | Calculated field based on supported types (PDF, DOC, DOCX) |

## Validation Rules

- **Extension Check**: Filename MUST end with `.pdf`, `.doc`, or `.docx` (case-insensitive).
- **MIME Type Check (Optional)**: If available, should match standard document MIME types.
- **URL Presence**: MUST have a valid `downloadUrl` in the content dictionary.

## State Transitions

The system is stateless regarding file uploads.

1. **Received**: Attachment detected in incoming activity.
2. **Processed**: Metadata extracted and validated.
3. **Confirmed**: Success/Failure message sent to user and logged.
