#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared test constants to avoid duplication across test modules."""

# App / namespace identifiers
APP_NAME = "oran-o2"
INVALID_NAMESPACE = "invalid-ns"

# Lifecycle operator constants
MIGRATION_TEMPLATE_NAME = "job-run-db-migrations.yaml"
MIGRATION_LABEL_SELECTOR = "app=oran-o2-db-migration"
PG_DUMP_TEMPLATE_NAME = "job-pg-dump.yaml"
PG_DUMP_LABEL_SELECTOR = "app=oran-o2-pg-dump"
TEMP_DIR = "/tmp"
TEMPLATES_DIR = "templates"

# Sample template content used in mock data
SAMPLE_TEMPLATE_CONTENT = "apiVersion: batch/v1"
SAMPLE_TEMPLATE_WITH_VAR = "content: $variable"
SAMPLE_TEMPLATE_MULTILINE = "apiVersion: batch/v1\nkind: Job"
