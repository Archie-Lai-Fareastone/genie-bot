# Tasks: Teams File Upload

**Input**: Design documents from `specs/001-teams-file-upload/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure and verify shared module availability in `src/utils/`
- [x] T002 Update `src/core/settings.py` to include Graph API settings (Client ID, Secret, Tenant ID)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T003 [P] Implement Graph API authentication and token caching in `src/utils/file_handler.py`
- [x] T004 [P] Implement base `download_file` function in `src/utils/file_handler.py` using `requests` or Graph SDK
- [ ] T002b [P] Add `UPLOAD_TIMEOUT_MINUTES` configuration to `src/core/settings.py` (default: 3 minutes, environment variable support)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Secure Multiple File Upload and Access (Priority: P1) 🎯 MVP

**Goal**: Users can upload multiple files via Teams and the bot can access them using a Service Principal.

**Independent Test**: Manually trigger file upload prompt in Teams, upload multiple files, and verify bot logs show successful content retrieval.

### Implementation for User Story 1

- [x] T005 [US1] Extend `src/bot/base_bot.py` to handle `on_teams_file_consent_accept` and `on_teams_file_consent_decline` activities
- [x] T006 [US1] Implement `handle_file_consent_accept` logic in `src/utils/file_handler.py` according to `contracts/file_handler_interface.md`
- [x] T007 [US1] Implement file upload prompt logic using `send_file_consent_card` in `src/bot/foundry_bot.py`
- [x] T008 [US1] Update `src/utils/file_handler.py` to support `UploadedFile` and `FileUploadState` defined in `data-model.md`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Multiple Upload Confirmation Feedback (Priority: P2)

**Goal**: Provide clear Adaptive Card feedback listing all uploaded files.

**Independent Test**: Observe the Adaptive Card response in Teams after a successful multi-file upload.

### Implementation for User Story 2

- [x] T009 [P] [US2] Extend `src/utils/card_builder.py` to include a template for file upload confirmation feedback
- [x] T010 [US2] Integrate feedback card delivery in `src/bot/foundry_bot.py` after processing `FileUploadState`

**Checkpoint**: User Story 2 is complete, providing a polished user experience.

---

## Phase 5: User Story 3 - Upload Session Management and Recovery (Priority: P2)

**Goal**: Handle interrupted upload sessions with automatic timeout cleanup and user-initiated controls.

**Independent Test**: Initiate upload, wait for timeout or cancel manually, then verify new upload can start successfully.

### Implementation for User Story 3

- [ ] T013 [US3] Implement automatic timeout detection in `src/utils/file_handler.py::get_upload_state()` to check `created_at` timestamp and auto-clear expired states
- [ ] T014 [US3] Add `_is_cancel_upload_command()` and `_handle_cancel_upload_command()` methods to `src/utils/command_handler.py`
- [ ] T015 [US3] Extend `_is_upload_command()` in `src/utils/command_handler.py` to detect force restart keywords (e.g., "重新上傳", "upload reset")
- [ ] T016 [US3] Update `_handle_upload_command()` in `src/utils/command_handler.py` to support `force_restart` parameter that bypasses pending state check
- [ ] T017 [US3] Add `clear_upload_state()` method to `src/utils/file_handler.py` for manual state cleanup
- [ ] T018 [US3] Update help message in `src/utils/command_handler.py::_handle_help_command()` to include cancel and restart commands
- [ ] T019 [P] [US3] Add logging for timeout events and manual cancellations in `src/utils/file_handler.py`

**Checkpoint**: Upload session management is complete, system handles edge cases gracefully.

---

## Final Phase: Polish & Cross-cutting Concerns

- [x] T011 [P] Implement comprehensive error handling and logging for file operations in `src/utils/file_handler.py`
- [x] T012 Update `specs/001-teams-file-upload/quickstart.md` with final deployment and verification steps
- [ ] T020 Update `specs/001-teams-file-upload/quickstart.md` with timeout configuration and session management testing steps

## Dependency Graph

```mermaid
graph TD
    T001 --> T002
    T002 --> T002b
    T002 --> T003
    T002 --> T004
    T002b --> US1
    T003 --> US1
    T004 --> US1
    US1 --> US2
    US1 --> US3
    US2 --> T011
    US3[User Story 3] --> T013
    US3 --> T014
    US3 --> T015
    US3 --> T016
    US3 --> T017
    US3 --> T018
    US3 --> T019
    T013 --> T020
    T014 --> T020
    T015 --> T020
    T016 --> T020
    T017 --> T020
    T018 --> T020
    T019 --> T020
    T011 --> T012
    T020 --> FinalReview[Final Review]
```

## Parallel Execution Examples

- **Foundational**: T002b, T003, and T004 can be implemented simultaneously after T002.
- **US2**: T009 can be started as soon as T001 is done, even before US1 is finished.
- **US3**: T014, T015, T017, T019 can be implemented in parallel once US1 is complete.

## Implementation Strategy

- **MVP**: Focus on completing US1 (Phase 1-3) to achieve basic upload and read capability.
- **Enhanced UX**: Add UI feedback (US2) for better user experience.
- **Robustness**: Implement session management (US3) to handle edge cases and improve reliability.
- **Incremental**: Each user story can be deployed and tested independently.
