# ADR 000: Pin dependency_name to <2.0.0

## Status
Accepted

## Context
Pydantic v2.10.0 introduced a bug with langgraph integration that causes the following error:
```bash
`ConversationSummaryBufferMemory` is not fully defined; you should define `BaseCache`, then call `ConversationSummaryBufferMemory.model_rebuild()`
```

## Decision
Pinned pydantic to version 2.9.2 to avoid bug with langgraph integration.

## Consequences
- Positive: Resolves the version conflict
- Negative: Missing new features from dependency_name 2.0+
- Risk: Need to monitor for future compatibility issues

## Date
2024-11-23