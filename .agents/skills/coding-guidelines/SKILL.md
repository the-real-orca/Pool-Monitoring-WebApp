---
name: coding-guidelines
description: Coding standards and architectural guidelines. Use this when performing AI-driven code modifications to ensure stability, performance, and consistency.
---

# Coding Guidelines

These guidelines ensure high-quality, stable, and maintainable code for all projects.

## Core Architectural Principles

- **Separation of Concerns (SoC):** Decouple hardware abstraction (BLE/WiFi), logic (decoding), and I/O (Web/Serial).
- **Encapsulation:** Use `static` for module-internal functions.
- **Non-blocking Design:** Never use `delay()` in main loops; use `millis()`-based state machines.
- **Memory Management:** Avoid heap allocation (`malloc`, `new`) at runtime. Use static buffers and prefer `NimBLE` and Arduino `String`.

## Style Rules (C++)

- **Naming:** 
  - `PascalCase`: Classes, Structs (e.g., `BLEHandler`)
  - `camelCase`: Methods, Functions, Variables (e.g., `decodeData()`, `rawData`)
  - `UPPER_SNAKE_CASE`: Constants, Macros (e.g., `MAX_BLE_RETRY`)
- **Formatting:** 4 spaces indentation, K&R brace style. Use only `#ifndef` include guards.

## Error Handling & Robustness

- **Input Validation:** Mandatory for all external data (Serial, Web, BLE).
- **Logging:** Use `DEBUG_print` and `DEBUG_println` macros exclusively. No raw `Serial.print`.

## AI-Agent Specific Workflow

1. **Source-First:** Read existing code before proposing changes.
2. **Surgical Updates:** Only change what is absolutely necessary. Avoid gratuitous refactoring.
3. **No "Ghost Code" Deletions:** Preserve relevant side effects and logging.
4. **Validation:** Every change must be covered by a `pytest/` test case.
5. **Zero-Trust Secrets:** Never write or log credentials.
6. **No Auto-Commits:** Always ask for explicit confirmation for each commit.

## Python Test Suite (pytest)

- Follow PEP 8 strictly.
- Use `WorkbenchDriver` for hardware interaction.
- Ensure test isolation using fixtures.
