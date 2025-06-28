# Implementation Plan: Parallel Scenario Evaluation

This document outlines the strategy for refactoring the Rogue application to support the concurrent evaluation of multiple scenarios.

## 1. Objective

The goal is to enable users to run multiple evaluation scenarios in parallel to speed up the testing process. The number of parallel runs will be configurable. The UI must be updated to display a dedicated, real-time chat log for each concurrent evaluation session.

## 2. Current State Analysis

The current architecture is strictly sequential:

- A single "Run" button triggers one evaluation process.
- The `ScenarioEvaluationService` iterates through each scenario one by one.
- The UI has a single chat window and status box, which are updated linearly as the single evaluation progresses.

## 3. Proposed Architecture

We will move from a sequential model to a parallel one orchestrated by a central UI event handler.

- **Configuration**: The user will set the desired number of parallel runs (`N`) in the config screen.
- **Batching**: The main list of scenarios will be divided into `N` smaller batches.
- **Execution**: `N` instances of the evaluation process will be spawned as concurrent `asyncio` tasks.
- **UI Display**: The UI will contain `N` dedicated output areas (chat + status). Each area will be updated independently and in real-time by its corresponding evaluation task.

```mermaid
graph TD
    subgraph "UI Layer (Gradio)"
        A[Config Screen] -- "1. Set Parallel Runs (N)" --> B(Scenario Runner);
        B -- "2. Splits Scenarios into N Batches" --> C{Run Evaluation};
    end

    subgraph "Async Orchestration"
        C -- "3. Creates N Concurrent Tasks" --> D{Task 1};
        C -- "..." --> E{Task 2};
        C -- "..." --> F{Task N};
    end

    subgraph "Execution & UI Updates"
        D -- "Batch 1" --> G1[Evaluation Service];
        E -- "Batch 2" --> G2[Evaluation Service];
        F -- "Batch N" --> GN[Evaluation Service];

        G1 -- "Live Updates" --> H1[Chat UI 1];
        G2 -- "Live Updates" --> H2[Chat UI 2];
        GN -- "Live Updates" --> HN[Chat UI N];
    end

    style "UI Layer (Gradio)" fill:#f9f,stroke:#333,stroke-width:2px
    style "Async Orchestration" fill:#ccf,stroke:#333,stroke-width:2px
    style "Execution & UI Updates" fill:#cfc,stroke:#333,stroke-width:2px

```

## 4. Step-by-Step Implementation Plan

### Step 1: Update Configuration

- **File**: `rogue/models/config.py`
  - **Action**: Add a new field `parallel_runs: int = 1` to the `AgentConfig` model.
- **File**: `rogue/ui/components/config_screen.py`
  - **Action**: Add a `gr.Slider` component to allow users to select the number of parallel runs (e.g., from 1 to 10).
  - **Action**: Bind this slider to the new `parallel_runs` field in the state and the `save_config` function.
- **File**: `rogue/ui/app.py`
  - **Action**: Ensure the `parallel_runs` value is correctly handled by the `app.load` function, providing a default value.

### Step 2: Redesign UI for Parallel Display

- **File**: `rogue/ui/components/scenario_runner.py`
  - **Action**: Remove the single `live_chat_display` and `status_box`.
  - **Action**: Create a _fixed_ number of output groups in a loop (e.g., `MAX_RUNS = 10`). Each group will contain a `gr.Chatbot` and a `gr.Textbox` for status, initially hidden (`visible=False`). Store these components in lists.
  - **Action**: The main `run_and_evaluate_scenarios` function will first make the first `N` of these component groups visible based on the user's configuration.

### Step 3: Implement Core Orchestration Logic

- **File**: `rogue/ui/components/scenario_runner.py`
  - **Action**: In the `run_and_evaluate_scenarios` function, after receiving the "run" click:
    1. Read the `parallel_runs` value from the config.
    2. Split the full list of scenarios into `N` batches.
    3. Create `N` worker tasks using `asyncio.create_task`. Each task will be responsible for calling the evaluation service for one batch of scenarios and updating its dedicated UI components.

### Step 4: Manage Real-time Updates for Multiple UIs

This is the most complex part, as a single Gradio event handler must manage all UI updates.

- **File**: `rogue/ui/components/scenario_runner.py`
  - **Action**: The `run_and_evaluate_scenarios` function will become the central orchestrator. It can no longer be a simple generator that yields updates for a single process.
  - **Action**: We will use `asyncio.gather` to run the `N` worker tasks. Each worker task will need a mechanism to send updates back to the orchestrator. A callback function is a good approach.
  - **Action**: The orchestrator will define a callback that workers can call with their updates (e.g., `update_callback(worker_id, update_type, data)`).
  - **Action**: This callback will build a dictionary of `gr.update` objects and `yield` it to Gradio, targeting the specific UI components for that `worker_id`.

### Step 5: Refactor Service Layer and Aggregate Results

- **File**: `rogue/services/scenario_evaluation_service.py`
  - **Action**: The `evaluate_scenarios` method already operates on a `Scenarios` object. We will now pass it the smaller batches of scenarios. The internal logic of the service, which iterates through the scenarios it receives, remains largely the same.
- **File**: `rogue/ui/components/scenario_runner.py`
  - **Action**: The orchestrator will `await` the completion of all `N` worker tasks.
  - **Action**: Each worker will return an `EvaluationResults` object for its batch.
  - **Action**: The orchestrator will combine these `N` result objects into a single, comprehensive `EvaluationResults` object.
  - **Action**: This final, combined object will be used to generate the final summary report, just as it is now.
- **File**: `rogue/models/evaluation_result.py`
  - **Action**: Add a `combine` method to the `EvaluationResults` class to facilitate the easy merging of results from multiple batches.
