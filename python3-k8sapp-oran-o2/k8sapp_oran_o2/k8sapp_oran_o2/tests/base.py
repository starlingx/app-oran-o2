#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Base test classes with common setUp patterns."""

import unittest
from unittest import mock

from k8sapp_oran_o2.tests.test_helpers import create_lifecycle_operator
from k8sapp_oran_o2.tests.test_helpers import create_mock_app


class BaseLifecycleTestCase(unittest.TestCase):
    """Base class for lifecycle operator tests.

    Provides common setUp with operator, context, conductor_obj,
    app_op, app, and hook_info mocks.
    """

    def setUp(self):
        """Set up common lifecycle test fixtures."""
        self.operator = create_lifecycle_operator()
        self.context = mock.MagicMock()
        self.conductor_obj = mock.MagicMock()
        self.app_op = mock.MagicMock()
        self.app = create_mock_app()
        self.hook_info = mock.MagicMock()
