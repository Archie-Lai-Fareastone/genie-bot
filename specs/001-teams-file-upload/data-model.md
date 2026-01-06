# Data Model: Teams File Upload

## Entities

### `UploadedFile`

Represents a file uploaded via Teams and its status.

| Field          | Type             | Description                            |
| -------------- | ---------------- | -------------------------------------- |
| `file_id`      | `str`            | Unique identifier from Teams/OneDrive. |
| `name`         | `str`            | Original filename.                     |
| `download_url` | `str`            | Direct download URL.                   |
| `content_type` | `str`            | MIME type (e.g., `application/pdf`).   |
| `size`         | `int`            | Size in bytes.                         |
| `local_path`   | `str` (Optional) | Path to temporary local copy.          |
| `owner_id`     | `str`            | Teams user ID who uploaded.            |

### `FileUploadState`

Used to track the state of a multi-file upload batch in a conversation.

| Field             | Type                 | Description                            |
| ----------------- | -------------------- | -------------------------------------- |
| `conversation_id` | `str`                | Teams conversation ID.                 |
| `expected_files`  | `int`                | Number of files user was prompted for. |
| `received_files`  | `List[UploadedFile]` | List of files successfully consented.  |
| `status`          | `str`                | `pending`, `completed`, `failed`.      |

## State Transitions

1. `PromptSent` -> User clicks "Accept" -> `on_teams_file_consent_accept` -> `FileDownloaded` -> `UpdateState`.
2. All files received -> `SendSummaryCard`.
