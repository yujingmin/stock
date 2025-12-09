<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md
请始终使用简体中文与我对话，并在回答时保持专业、简洁。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This is a monorepo containing:
- `backend/` - Backend application (currently empty)
- `frontend/` - Frontend application (currently empty)

## Development Setup

No build, test, or development commands have been configured yet. When adding package.json or similar configuration files, update this document with:
- Build commands
- Test commands
- Development server commands
- Linting/formatting commands

## Architecture

The codebase structure is being established. Update this section as the architecture develops to document:
- Key architectural patterns
- Module organization
- Data flow between frontend and backend
- Authentication/authorization approach
- Database schema and ORM usage
