# PRD.md — Ocean (Working Name)
*A modular, API-first knowledge and action workspace*

---

## 1. Problem Statement

Modern knowledge tools (e.g., Notion) attempt to be everything at once: documents, databases, project management, wikis, collaboration suites, and now AI platforms. This leads to:

- Cognitive overload for users
- Over-engineered products for small teams
- Poor composability for developers
- Limited API-first extensibility
- Slow iteration for founders building on top of them

**Founders and small teams need a focused, modular core** they can shape into their own workflows — not a monolith.

---

## 2. Target Users & Jobs-To-Be-Done (JTBD)

### Primary User
- Startup founders / small teams (1–10 people)
- Product builders, researchers, operators
- Comfortable with tools, but not wanting complexity

### Core JTBD
- *"Help me capture, organize, and evolve thinking into action — without forcing a rigid structure or overwhelming me."*
- *"Let me build my own system, then automate or extend it later via APIs."*

---

## 3. Product Principles

1. **Opinionated Core, Flexible Edges**
2. **MVP before Power**
3. **Composable > Complete**
4. **API-first by design**
5. **Non-goals are explicit**
6. **Fast to understand, hard to outgrow**

---

## 4. Product Definition (What Ocean Is)

Ocean is a **block-based, semantic workspace** where:

- Everything is a block
- Blocks have meaning (type + metadata)
- Blocks can link, nest, and reference
- The core product is intentionally small
- Power comes via APIs, not UI bloat

Ocean is **not** a Notion clone.
It is a **foundation layer**.

---

## 5. MVP Scope (Must-Have)

### 5.1 Core Objects (Blocks)

| Block Type | Description |
|----------|-------------|
| Text Block | Plain text with markdown support |
| Heading Block | Structural hierarchy |
| List Block | Bullet / numbered |
| Task Block | Checkbox + status |
| Link Block | Internal / external reference |
| Page | A container of blocks |

**Explicit exclusion (MVP):**
- Databases
- Tables
- Kanban boards
- Calendars
- Complex permissions
- Templates marketplace

---

### 5.2 Core Capabilities

#### A. Block Editor
- Keyboard-first
- Slash commands (`/text`, `/task`, etc.)
- Inline editing
- Drag-to-reorder

#### B. Linking & References
- Page ↔️ Page
- Block ↔️ Block
- Backlinks (read-only in MVP)

#### C. Semantic Metadata (Lightweight)
- Block type
- Created / updated timestamps
- Status (for tasks)
- Tags (flat, no hierarchy)

---

## 6. Explicit Non-Goals (Won't Build Now)

This section is **non-negotiable**.

- No databases / relational views
- No kanban / project management UI
- No team collaboration (single-user first)
- No real-time multiplayer
- No permissions / roles
- No AI copilot in V1 UI
- No mobile app

These may exist later **via APIs or extensions**, not core.

---

## 7. Feature Hypotheses (Validated Thinking)

| Hypothesis | Why It Matters | Validation Signal |
|----------|---------------|------------------|
| Users prefer fewer primitives | Reduces overwhelm | Faster onboarding, lower churn |
| API-first attracts builders | Extensibility without UI bloat | External integrations built |
| Single-user first speeds PMF | Less complexity | Faster iteration cycles |
| Semantic blocks enable future AI | Future-proofing | Clean data graph |

---

## 8. Core User Flows (MVP)

### Flow 1: Create Thinking Space
1. Create Page
2. Add blocks
3. Link to other pages
4. Tag blocks

### Flow 2: Turn Thought → Action
1. Convert text → task
2. Assign status
3. Navigate via backlinks

### Flow 3: Extend via API
1. Fetch blocks via API
2. Process externally (AI, analytics)
3. Write back updates

---

## 9. High-Level Architecture

### 9.1 Conceptual Model
