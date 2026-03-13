# sky-bootstrap Specification

## Purpose
TBD - created by archiving change sky-bootstrap-progress. Update Purpose after archive.
## Requirements
### Requirement: Visual Progress Display
The system SHALL display a visual progress bar during Sky Chat initialization showing each component being loaded.

#### Scenario: Bootstrap with RAG enabled
- **WHEN** user executes `sky.cmd` with `USE_RAG_MEMORY=true`
- **THEN** system displays progress bar with stages: Environment → Embedding Model → Vector DB → Collections → Textual UI
- **AND** each stage shows its name and current status
- **AND** progress bar updates in real-time as each stage completes

#### Scenario: Bootstrap without RAG
- **WHEN** user executes `sky.cmd` with `USE_RAG_MEMORY=false`
- **THEN** system displays progress bar with stages: Environment → Textual UI
- **AND** embedding/database stages are skipped

### Requirement: Database Size Display
The system SHALL display the current size of the vector database during initialization.

#### Scenario: Vector DB stage shows database size
- **WHEN** Vector DB stage is loading
- **THEN** stage description includes database size in megabytes
- **AND** format is "Inicializando banco vetorial... (X MB)"
- **AND** size is calculated before loading the database

#### Scenario: Empty database
- **WHEN** Vector DB stage is loading and database is empty or new
- **THEN** stage description shows "Inicializando banco vetorial... (novo)"
- **OR** stage description shows "Inicializando banco vetorial... (0 MB)"

### Requirement: Collection Names Display
The system SHALL display the names of collections being initialized during the Collections stage.

#### Scenario: Collections stage shows collection names
- **WHEN** Collections stage is loading
- **THEN** stage description lists the collections being initialized
- **AND** format is "Configurando coleções... (identity, shared-moments, teachings, operational)"
- **AND** only collections that exist or will be created are shown

#### Scenario: Collections stage with empty collections
- **WHEN** Collections stage is loading and no collections exist yet
- **THEN** stage description shows "Configurando coleções... (criando defaults)"
- **AND** default collections are created: identity, shared-moments, teachings, operational

### Requirement: Stage Timing Display
The system SHALL display elapsed time for each bootstrap stage.

#### Scenario: Stage timing shown
- **WHEN** bootstrap is running
- **THEN** each stage displays elapsed time while active
- **AND** total elapsed time is shown at the end

#### Scenario: Slow stage identification
- **WHEN** a stage takes longer than 3 seconds
- **THEN** the stage is highlighted in the progress bar
- **AND** user can identify which component is causing delay

### Requirement: Bootstrap Cancellation
The system SHALL allow user to cancel bootstrap with Ctrl+C.

#### Scenario: User cancels during embedding load
- **WHEN** user presses Ctrl+C while embedding model is loading
- **THEN** system gracefully terminates bootstrap
- **AND** displays cancellation message
- **AND** exits with code 130 (standard SIGINT)

#### Scenario: User cancels after Textual starts
- **WHEN** user presses Ctrl+C after Textual UI is running
- **THEN** Textual handles the interruption (not bootstrap)

### Requirement: Bootstrap Bypass
The system SHALL support `--no-bootstrap` flag to skip progress display.

#### Scenario: Bootstrap bypassed
- **WHEN** user executes `sky.cmd --no-bootstrap`
- **THEN** system skips progress bar display
- **AND** initialization proceeds as before (original behavior)
- **AND** output goes directly to console logs

### Requirement: Error Handling
The system SHALL handle errors during bootstrap with clear messages.

#### Scenario: Embedding model not cached
- **WHEN** embedding model is not in local cache
- **THEN** system displays error message with download instructions
- **AND** bootstrap terminates gracefully
- **AND** exit code is 1

#### Scenario: Database corruption
- **WHEN** SQLite database is corrupted
- **THEN** system displays error indicating database issue
- **AND** suggests recovery action (reinit database)
- **AND** bootstrap terminates gracefully

### Requirement: Stage Completion Order
The system SHALL load bootstrap stages in the correct dependency order.

#### Scenario: Stage dependency order
- **WHEN** bootstrap starts
- **THEN** stages load in this order:
  1. Environment (PYTHONPATH, .env)
  2. Embedding Model (if RAG enabled)
  3. Vector DB (if RAG enabled)
  4. Collections (if RAG enabled)
  5. Textual UI
- **AND** a stage cannot start until previous stage completes
- **AND** failed stage prevents subsequent stages from loading

### Requirement: Progress Bar Persistence
The system SHALL keep progress bar visible until Textual UI takes over.

#### Scenario: Clean handoff to Textual
- **WHEN** all bootstrap stages complete
- **THEN** progress bar displays "Starting Sky Chat..." message
- **AND** progress bar clears when Textual UI renders
- **AND** no visual artifacts remain

### Requirement: Rich Library Integration
The system SHALL use `rich.progress` for progress display.

#### Scenario: Rich progress bar styling
- **WHEN** bootstrap is running
- **THEN** progress bar uses Rich's Progress, BarColumn, and TimeElapsedColumn
- **AND** styling matches Sky Chat theme (blue/cyan colors)
- **AND** spinner shows activity during active stage

