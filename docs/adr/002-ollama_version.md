# ADR 002: Pinned ollama version

## Status
Accepted

## Context
Running with the latest version of ollama causes a bug with langchain-ollama where tool calls return None instead of [].
This [GitHub issue](https://github.com/langchain-ai/langchain/issues/28281) describes the bug.

## Decision
Pinned ollama to version <0.4.0 until langchain-ollama is to interface with langchain consistently.

## Consequences
- Positive: Ollama API works as expected
- Negative: Need to manually update ollama version in pyproject.toml to use latest version
- Risk: Ollama version may fall out of date from most recent updates

## Date
2024-11-24