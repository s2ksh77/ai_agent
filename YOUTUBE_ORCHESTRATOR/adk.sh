#!/bin/bash
# ADK command wrapper for YOUTUBE_ORCHESTRATOR project

cd "$(dirname "$0")"
source .venv/bin/activate
exec adk "$@"
