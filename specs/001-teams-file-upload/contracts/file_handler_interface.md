# Internal Contracts: FileHandler

## `FileHandler` Interface

### `send_file_consent_card`

Sends a Teams File Consent Card to the user.

- **Parameters**:
  - `turn_context`: `TurnContext`
  - `filename`: `str`
  - `description`: `str` (Optional)
- **Returns**: `Promise<ResourceResponse>`

### `download_file`

Downloads file content from a given URL or Teams ID.

- **Parameters**:
  - `download_url`: `str`
- **Returns**: `Promise<bytes>`

### `handle_file_consent_accept`

Logic to execute when user accepts upload.

- **Parameters**:
  - `turn_context`: `TurnContext`
  - `file_consent_card_response`: `FileConsentCardResponse`
- **Returns**: `Promise<UploadedFile>`
