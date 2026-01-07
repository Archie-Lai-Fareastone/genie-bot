# Tasks: File Attachment Handling

**Input**: Design documents from `specs/001-teams-file-upload/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Includes exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Initialize shared utility file in `src/utils/file_handler.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [x] T003 Define `FileAttachmentInfo` dataclass and constants in `src/utils/file_handler.py`
- [x] T004 Setup logger instance in `src/utils/file_handler.py` using `src/core/logger_config.py`

---

## Phase 3: User Story 1 - Receive and Extract File Metadata (Priority: P1) 🎯 MVP

**Goal**: Extract filename, type, and download URL from Teams message activity attachments.

**Independent Test**: User sends a file in Teams; verify metadata is correctly extracted and available for processing.

### Implementation for User Story 1

- [x] T005 [US1] Implement `extract_attachments(activity)` logic in `src/utils/file_handler.py`
- [x] T006 [US1] Update `FoundryBot.on_message_activity` in `src/bot/foundry_bot.py` to call attachment extraction

---

## Phase 4: User Story 2 - Validate File Types (Priority: P1)

**Goal**: Validate that attachments are PDF, DOC, or DOCX and notify user of rejections.

**Independent Test**: Send a JPG file; verify bot replies with "File type not supported" message.

### Implementation for User Story 2

- [x] T008 [US2] Implement `validate_attachments(files)` in `src/utils/file_handler.py` (Whitelist: .pdf, .doc, .docx)
- [x] T009 [US2] Add logic in `src/bot/foundry_bot.py` to send error messages for unsupported file types

---

## Phase 5: User Story 3 - Log and Confirm Successful Processing (Priority: P2)

**Goal**: Log successful attachment processing and send confirmation to the user.

**Independent Test**: Send a valid PDF; verify bot logs info and sends "Successfully received: [filename]" message.

### Implementation for User Story 3

- [x] T011 [US3] Implement `log_attachment(file_info, user_info)` in `src/utils/file_handler.py`
- [x] T012 [US3] Add success feedback response logic in `src/bot/foundry_bot.py`
- [x] T013 [P] [US3] Verify log output matches requirements in `logs/app.log`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements and final validation

- [x] T014 [P] Update `specs/001-teams-file-upload/quickstart.md` with final testing details
- [x] T015 Perform final end-to-end manual validation per `quickstart.md`
- [x] T016 [P] Code cleanup and docstrings for all new functions in `src/utils/file_handler.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1
- **User Stories (Phase 3-5)**: All depend on Foundational completion
  - US1 (P1) and US2 (P1) are both high priority but US2 depends on metadata extracted in US1.
  - US3 (P2) depends on US1 and US2 success.
- **Polish (Phase 6)**: Depends on all stories completion.

### Parallel Opportunities

- Documentation updates (T014) can run in parallel with polish tasks.

---

## Parallel Example: User Story 1 & 2

```bash
# Developer A: Implement extraction
- [ ] T005 [US1] Implement extract_attachments(activity) in src/utils/file_handler.py

# Developer B: Implement validation (can start on same file if partitioned)
- [ ] T008 [US2] Implement validate_attachments(files) in src/utils/file_handler.py
```
