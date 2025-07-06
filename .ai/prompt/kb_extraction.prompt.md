---
mode: 'agent'
---
## Feature Knowledge Extraction Prompt (Standard)

You are a Knowledge Extraction Agent assigned to reverse-engineer critical system knowledge from a brownfield codebase.

For the provided code, extract the following information for Feature KB documentation:

---

### 1. **Feature Overview**
- **Feature Name:** (Concise title based on its functionality)
- **Purpose:** (Why this feature exists)
- **Main Use Cases:** (Primary user flows or system triggers)

---

### 2. **Major Workflows**
- Identify the key APIs, events, or system actions that trigger this feature.
- For each trigger, outline the main control flow and major processing steps (preferably in step-by-step form).
- Clarify the typical input, output, and important state transitions.
- **For each step, include direct file/function/class references** (e.g., `[line/webhook/trigger_v2.py:Handler.message](../line/webhook/trigger_v2.py#L47)`).
- If multiple workflows exist, list them separately.
- Where relevant, provide a short code snippet or example payload to illustrate the contract or extension point.
- Use Mermaid diagrams (sequence, activity, etc.) to illustrate complex workflows where appropriate.
- When there are detailed differences in feature support, event handling, or data contract applicability, consider using a **support table** to help readers quickly understand nuanced distinctions. This approach is especially useful for showing which combinations of events, types, or options are supported, and what specific behaviors or data apply in each case.
    - Use checkmarks (✔) for supported, ✗ for not supported, and list any relevant details (such as reply message types) in each cell for clarity.
    - **Example format:**

      | Trigger Type | follow | message | postback | beacon |
      |--------------|:------:|:-------:|:--------:|:------:|
      | **Keyword**  | ✗      | ✔<br>ORIGINAL_FRIEND, BOUND_FRIEND | ✔<br>ORIGINAL_FRIEND, BOUND_FRIEND | ✔<br>ORIGINAL_FRIEND, BOUND_FRIEND |
      | **Welcome**  | ✔<br>NEW_FRIEND | ✗ | ✗ | ✗ |
      | **General**  | ✗ | ✔<br>ORIGINAL_FRIEND, BOUND_FRIEND | ✔<br>ORIGINAL_FRIEND, BOUND_FRIEND | ✗ |

      - ✔ = Supported; ✗ = Not supported
      - For each supported cell, the allowed reply message types are listed.

---

### 3. **Key Data Contracts & Payloads**
- Summarize important Data Transfer Objects (DTOs), API request/response payloads, and event message structures.
- **Provide example payloads or relevant code snippets (e.g., Pydantic models, class definitions) where possible, with code references.**
- Focus on the contracts for data interchange, not deep database model structures (which are covered in Section 4).

---

### 4. **System Architecture, Data Flow, and Reporting**

This section details the broader architecture, how data flows (especially for reporting), and how the feature integrates with others.

#### 4.1. **Model Relationships & Architecture**
- Describe key Database Models and their core responsibilities and roles within the feature.
- Provide Entity Relationship Diagrams (ERDs), preferably using Mermaid, to illustrate relationships between models.
- Illustrate core model hierarchies or significant groupings if applicable.
- **Include code references to model definitions.**

#### 4.2. **Data Pipelines & Collection (especially for reporting/analytics features)**
- For each significant data pipeline (e.g., for analytics, reporting data aggregation):
    - Provide an overview diagram (e.g., using Mermaid: `graph TD`, `sequenceDiagram`) illustrating the data flow.
    - Detail event collection, ingestion, transformation, processing, and storage steps.
    - Reference relevant code modules, functions, database tables, message queues, and external services involved in the pipeline.

#### 4.3. **Reporting Implementation & APIs (if applicable)**
- Describe the controller logic and key methods/services responsible for report generation or data retrieval.
- List relevant API endpoints, including parameters and typical usage.
- Summarize response formats and key serializers used for reporting data.
- Detail any access control mechanisms or permissions specific to reporting APIs.
- **Include code references for controllers, services, serializers, and API view definitions.**

#### 4.4. **Cross-Feature Integration Architecture**
- Explain how this feature integrates with other features, modules, or systems.
- Describe the integration mechanism (e.g., through shared models, reference links like `WebhookTriggerSettingReference`, events, direct API calls, message queues).
- Provide concrete examples of such integrations, referencing the specific models or code involved.
- Link to related KBs or code modules that interact significantly with this feature.

---

### 5. **External Dependencies**
- List all external systems, services, or APIs that this feature relies on (e.g., other microservices, third-party APIs like LINE Messaging API, payment gateways, cloud services like BigQuery, Pub/Sub).
- Specify cron jobs, scheduled tasks, or external event subscriptions that trigger or affect this feature.
- **Include code references where these dependencies are invoked or configured.**

---

### 6. **Edge Cases & Constraints**
- Provide a detailed list of important edge cases, rare paths, operational constraints, and system limits (e.g., rate limits, payload size limits, timeouts).
- For each, briefly describe how the system handles or mitigates the case.
- **Include code references for each edge case handling logic.**
- Cover aspects like retries, batching, idempotency, error fallback strategies, and any channel-specific or provider-specific constraints.

---

### 7. **Known Technical Traps**
- List specific technical challenges, common pitfalls, non-obvious behaviors, and risks that future developers should be aware of when working with this feature.
- For each, briefly explain why it is tricky and how it could cause failures, maintenance issues, or unexpected behavior.
- **Include code references illustrating the trap or its context.**

---

### 8. **Test Coverage**
- List the key test files, classes, and functions that cover this feature (unit, integration, E2E).
- Note any significant areas, critical paths, or edge cases not adequately covered by automated tests (gaps in testing).
- **Provide direct references to test files/functions.**

---

### 9. **Cache/State Management**
- If the feature utilizes caching or manages significant in-memory state:
    - Document cache keys, typical Time-To-Live (TTL) values, and cache invalidation strategies or triggers.
    - Describe any in-memory state variables, their scope, and how they are managed.
    - **Include code references for cache logic (e.g., cache reads, writes, invalidation points).**

---

### 10. **How to Extend/Debug**
- Provide guidance for common extension scenarios (e.g., adding a new trigger type, supporting a new data source).
- Offer tips for debugging common failures or issues, pointing to relevant logs, monitoring tools, or specific code sections to inspect.
- **Include code references to key extension points or debugging aids.**

---

### 11. **Known TODOs/Technical Debt**
- List any `TODO`, `FIXME` comments, or known areas of technical debt within the codebase related to this feature.
- Briefly describe the nature of the debt or the pending task.
- **Include code references to the location of these comments or relevant code sections.**

---

**Guidelines:**
- Use clear, human-readable language.
- Format lists (e.g., for Edge Cases, Traps, TODOs) as bullet points for clarity.
- Focus on capturing **knowledge that would help future developers safely modify, extend, debug, or migrate this feature**.
- Emphasize system behavior, architectural decisions, and workflow understanding over exhaustive low-level code details.
- **Format all code references as `[path/file.py:ClassName.method_name](../relative_path/to/file.py#L<line_number>)` or similar for easy navigation within the codebase.** E.g., `[line/webhook/trigger_v2.py:Handler.message](../line/webhook/trigger_v2.py#L47)`.
- **Utilize Mermaid diagrams** for ERDs, sequence diagrams, data flowcharts, and complex workflows to enhance understanding.
- Identify critical clarifications or hidden assumptions. If information is missing or unclear, formulate specific questions. You may provide multiple-choice options to speed up clarification if that helps.
  - Example format for multiple-choice options:
    - **Question:** What is the primary data source for the `XYZReport`?
      - (A) Direct query from `MainDataTable`.
      - (B) Aggregation via `DailySummaryTable`.
      - (C) External API `foo.com/data`.
      - (D) Other (please specify).

---

**Your goal:**
Produce actionable, navigable, and code-linked documentation that enables both humans and AI-driven agents to safely and efficiently work with this feature.

---