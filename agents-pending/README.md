# GitHub Agent Prompts for CFMS Client NEXT

This directory contains specialized prompts for GitHub Agents (like GitHub Copilot) to assist with development tasks in the CFMS Client NEXT repository.

## Purpose

These prompts provide comprehensive documentation about different aspects of the codebase, enabling AI assistants to:
- Understand the architecture and design patterns
- Follow established coding conventions
- Implement features correctly
- Maintain consistency across the codebase
- Avoid common pitfalls

## Available Agent Prompts

### 1. Architecture & Core Systems (`architecture-core-systems.md`)
- Overall application architecture
- Design patterns (Singleton, MVC, Generic Controllers)
- Core system components and their interactions
- Directory structure and organization
- Best practices for state management

**Use when**: Understanding the overall codebase structure, implementing core features, or refactoring major components.

### 2. UI/UX Development (`ui-ux-development.md`)
- Flet framework usage and patterns
- UI components, views, and models
- Navigation and routing (Flet-Model)
- Dialog and notification patterns
- Layout and styling guidelines

**Use when**: Creating or modifying UI components, implementing new views, or working with Flet controls.

### 3. WebSocket Communication (`websocket-communication.md`)
- WebSocket connection management
- Request/response protocol
- SSL/TLS configuration
- File transfer protocol
- Error handling and retry logic

**Use when**: Implementing client-server communication, handling network requests, or debugging connection issues.

### 4. File Management & Explorer (`file-management-explorer.md`)
- File explorer architecture
- Upload/download operations
- Directory management
- Sorting and filtering
- Batch operations

**Use when**: Working on file operations, improving the file explorer, or implementing file-related features.

### 5. Authentication & Security (`authentication-security.md`)
- Login and logout flows
- Token management
- Permission system (RBAC)
- SSL/TLS security
- File encryption and hash verification

**Use when**: Implementing authentication features, managing permissions, or addressing security concerns.

### 6. Configuration & Preferences (`configuration-preferences.md`)
- AppShared singleton usage
- User preferences (YAML)
- Settings UI implementation
- State persistence strategies
- Migration handling

**Use when**: Adding new settings, managing application state, or implementing preference-related features.

### 7. Localization & Internationalization (`localization-i18n.md`)
- Gettext integration
- Translation workflow
- Language switching
- Best practices for i18n
- Adding new languages

**Use when**: Translating the application, adding new languages, or ensuring strings are properly internationalized.

## Using These Prompts

### For Developers

When working on a specific area of the codebase:
1. Review the relevant agent prompt(s)
2. Follow the patterns and conventions described
3. Use the code examples as templates
4. Refer to the best practices section

### For AI Assistants

When asked to help with CFMS Client NEXT:
1. Read the relevant prompt(s) based on the task
2. Follow the architectural patterns described
3. Use the established conventions and code styles
4. Reference the examples and best practices

### Context for AI

To help an AI assistant with a task, you can:
```
Please review the {prompt-name}.md in .github/agents/ and help me {task description}.
```

Example:
```
Please review the ui-ux-development.md in .github/agents/ and help me create a new dialog for user profile editing.
```

## Frontmatter Format

Each prompt file includes YAML frontmatter:

```yaml
---
name: Agent Name
description: Brief description of the agent's expertise
---
```

This metadata helps identify the purpose and scope of each prompt.

## Maintaining These Prompts

### When to Update

Update the relevant prompt(s) when:
- Architecture or design patterns change
- New major features are added
- Dependencies are upgraded with breaking changes
- Best practices evolve
- Common issues or patterns emerge

### How to Update

1. Identify which prompt(s) need updating
2. Update the relevant sections
3. Add new examples if needed
4. Update version-specific information
5. Commit with a clear message

### Contributing

When adding new features or making significant changes:
- Consider if agent prompts need updates
- Update relevant sections to reflect new patterns
- Add examples for new functionality
- Document any new best practices

## Repository Information

- **Repository**: Creeper19472/cfms_client_next
- **Framework**: Flet (Python UI framework)
- **Python Version**: ≥3.12
- **Protocol Version**: 9
- **Current Version**: 0.2.36

## Related Documentation

- Main README: `/README.md`
- PyProject Configuration: `/pyproject.toml`
- Application Constants: `/src/include/constants.py`

## Support

For questions or issues related to these prompts:
- Open an issue on GitHub
- Contact the development team
- Refer to the main repository documentation
