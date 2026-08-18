#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for helm/oran_o2 module."""

import unittest
from unittest import mock

from k8sapp_oran_o2.common import constants as app_constants
from k8sapp_oran_o2.helm.oran_o2 import Orano2Helm

from k8sapp_oran_o2.tests.test_constants import INVALID_NAMESPACE
from k8sapp_oran_o2.tests.test_helpers import create_helm_instance


class TestOrano2HelmGetNamespaces(unittest.TestCase):
    """Test Orano2Helm.get_namespaces method."""

    def setUp(self):
        """Set up test fixtures."""
        self.helm = create_helm_instance()

    def test_get_namespaces_returns_supported(self):
        """Verify get_namespaces returns supported list."""
        result = self.helm.get_namespaces()
        self.assertEqual(result, Orano2Helm.SUPPORTED_NAMESPACES)


class TestOrano2HelmGetOverrides(unittest.TestCase):
    """Test Orano2Helm.get_overrides method."""

    def setUp(self):
        """Set up test fixtures."""
        self.helm = create_helm_instance()
        # pylint: disable=protected-access
        self.helm._num_replicas_for_platform_app = (
            mock.MagicMock(return_value=2)
        )

    def test_get_overrides_no_namespace(self):
        """Test get_overrides with no namespace."""
        result = self.helm.get_overrides(namespace=None)
        self.assertIn(app_constants.HELM_NS_ORAN_O2, result)

    def test_get_overrides_valid_namespace(self):
        """Test get_overrides with valid namespace."""
        result = self.helm.get_overrides(
            namespace=app_constants.HELM_NS_ORAN_O2
        )
        self.assertIn('replicaCount', result)
        self.assertEqual(result['replicaCount'], 2)

    def test_get_overrides_invalid_namespace(self):
        """Test get_overrides with invalid namespace."""
        from sysinv.common import exception
        with self.assertRaises(exception.InvalidHelmNamespace):
            self.helm.get_overrides(namespace=INVALID_NAMESPACE)

    def test_get_overrides_replica_count_value(self):
        """Test get_overrides returns correct replicas."""
        # pylint: disable=protected-access
        self.helm._num_replicas_for_platform_app.return_value = 3
        result = self.helm.get_overrides(
            namespace=app_constants.HELM_NS_ORAN_O2
        )
        self.assertEqual(result['replicaCount'], 3)
