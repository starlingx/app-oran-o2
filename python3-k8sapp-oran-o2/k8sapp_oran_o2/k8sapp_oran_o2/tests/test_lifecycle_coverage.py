#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for lifecycle_oran_o2 module."""

import os
import unittest
from string import Template
from unittest import mock

from k8sapp_oran_o2.lifecycle.lifecycle_oran_o2 import \
    OranO2AppLifecycleOperator

from k8sapp_oran_o2.tests.base import BaseLifecycleTestCase
from k8sapp_oran_o2.tests.test_constants import APP_NAME
from k8sapp_oran_o2.tests.test_constants import MIGRATION_LABEL_SELECTOR
from k8sapp_oran_o2.tests.test_constants import MIGRATION_TEMPLATE_NAME
from k8sapp_oran_o2.tests.test_constants import SAMPLE_TEMPLATE_CONTENT
from k8sapp_oran_o2.tests.test_constants import SAMPLE_TEMPLATE_MULTILINE
from k8sapp_oran_o2.tests.test_constants import SAMPLE_TEMPLATE_WITH_VAR
from k8sapp_oran_o2.tests.test_constants import TEMP_DIR
from k8sapp_oran_o2.tests.test_helpers import create_lifecycle_operator


class TestRunDbMigration(BaseLifecycleTestCase):
    """Test _run_db_migration method."""

    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2'
        '.utils.create_from_yaml'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.ApiClient'
    )
    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_read_template'
    )
    def test_run_db_migration_success(
        self,
        mock_read_template,
        mock_create_resource_file,
        mock_kube_api_client,
        mock_create_from_yaml
    ):
        """Test successful db migration."""
        mock_template = mock.MagicMock(
            spec=Template
        )
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = (
            mock_template
        )

        # pylint: disable=protected-access
        self.operator._run_db_migration(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

        mock_read_template.assert_called_once_with(
            MIGRATION_TEMPLATE_NAME
        )
        expected_path = os.path.join(
            TEMP_DIR, MIGRATION_TEMPLATE_NAME
        )
        mock_create_resource_file.assert_called_once_with(
            expected_path, SAMPLE_TEMPLATE_CONTENT
        )
        mock_kube_api_client.assert_called_once()
        mock_create_from_yaml.assert_called_once()

    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_read_template'
    )
    def test_run_db_migration_failure_cleans_up(
        self,
        mock_read_template,
        mock_cleanup_resources
    ):
        """Test failed migration triggers cleanup."""
        mock_read_template.side_effect = (
            Exception("template not found")
        )

        from sysinv.common import exception
        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ):
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context,
                self.conductor_obj,
                self.app_op, self.app
            )
        mock_cleanup_resources.assert_called_once()

    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @mock.patch.object(
        OranO2AppLifecycleOperator,
        '_read_template'
    )
    def test_run_db_migration_error_message(
        self,
        mock_read_template,
        mock_cleanup_resources
    ):
        """Test error has original exception text."""
        mock_read_template.side_effect = (
            Exception("file missing")
        )

        from sysinv.common import exception
        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ) as ctx:
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context,
                self.conductor_obj,
                self.app_op, self.app
            )
        self.assertIn(
            "file missing", str(ctx.exception)
        )
        mock_cleanup_resources.assert_called_once()


class TestCleanupMigrationResources(
    BaseLifecycleTestCase
):
    """Test _cleanup_migration_resources method."""

    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.BatchV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.CoreV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.ApiClient'
    )
    def test_cleanup_success(
        self,
        mock_kube_api_client,
        mock_core_v1_api,
        mock_batch_v1_api,
        mock_rbac_v1_api
    ):
        """Test successful cleanup of all resources."""
        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

        batch_api = mock_batch_v1_api.return_value
        batch_api.delete_collection_namespaced_job \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )

        core_api = mock_core_v1_api.return_value
        (core_api
         .delete_collection_namespaced_pod
         .assert_called_once())
        (core_api
         .delete_collection_namespaced_config_map
         .assert_called_once())
        (core_api
         .delete_collection_namespaced_service_account
         .assert_called_once())

        rbac_api = mock_rbac_v1_api.return_value
        (rbac_api
         .delete_collection_namespaced_role
         .assert_called_once())
        (rbac_api
         .delete_collection_namespaced_role_binding
         .assert_called_once())

    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.BatchV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.CoreV1Api'
    )
    @mock.patch(
        'k8sapp_oran_o2.lifecycle'
        '.lifecycle_oran_o2.client.ApiClient'
    )
    def test_cleanup_handles_exception(
        self,
        mock_kube_api_client,
        mock_core_v1_api,
        mock_batch_v1_api,
        mock_rbac_v1_api
    ):
        """Test cleanup handles exceptions gracefully."""
        (mock_batch_v1_api.return_value
         .delete_collection_namespaced_job
         .side_effect) = Exception("api error")
        # Should not raise
        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )


class TestReadTemplate(unittest.TestCase):
    """Test _read_template method."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = create_lifecycle_operator()

    @mock.patch(
        'builtins.open',
        mock.mock_open(
            read_data=SAMPLE_TEMPLATE_MULTILINE
        )
    )
    def test_read_template_returns_template(self):
        """Test _read_template returns Template."""
        # pylint: disable=protected-access
        result = self.operator._read_template(
            MIGRATION_TEMPLATE_NAME
        )
        self.assertIsInstance(result, Template)

    @mock.patch(
        'builtins.open',
        mock.mock_open(
            read_data=SAMPLE_TEMPLATE_WITH_VAR
        )
    )
    def test_read_template_content(self):
        """Test _read_template preserves content."""
        # pylint: disable=protected-access
        result = self.operator._read_template(
            "test.yaml"
        )
        self.assertEqual(
            result.template,
            SAMPLE_TEMPLATE_WITH_VAR
        )

    def test_read_template_file_not_found(self):
        """Test _read_template raises on missing file."""
        with self.assertRaises(FileNotFoundError):
            # pylint: disable=protected-access
            self.operator._read_template(
                "nonexistent.yaml"
            )


class TestCreateKubeResourceFile(unittest.TestCase):
    """Test _create_kube_resource_file method."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = create_lifecycle_operator()

    @mock.patch('builtins.open', mock.mock_open())
    def test_create_kube_resource_file(self):
        """Test file creation with correct content."""
        # pylint: disable=protected-access
        self.operator._create_kube_resource_file(
            "/tmp/test.yaml", "apiVersion: v1"
        )
        # pylint: disable=consider-using-with
        mock_file = open
        mock_file.assert_called_once_with(
            "/tmp/test.yaml", 'w'
        )
        mock_file().write.assert_called_once_with(
            "apiVersion: v1"
        )

    @mock.patch(
        'builtins.open',
        side_effect=PermissionError("denied")
    )
    def test_create_kube_resource_file_perm_error(
        self,
        mock_open_file  # pylint: disable=unused-argument
    ):
        """Test file creation raises on permission."""
        with self.assertRaises(PermissionError):
            # pylint: disable=protected-access
            self.operator._create_kube_resource_file(
                "/root/test.yaml", "content"
            )


class TestReadTemplateWithRealFile(
    unittest.TestCase
):
    """Test _read_template with actual template."""

    def setUp(self):
        """Set up test fixtures."""
        self.operator = create_lifecycle_operator()

    def test_read_actual_migration_template(self):
        """Test reading the actual migration template."""
        # pylint: disable=protected-access
        result = self.operator._read_template(
            MIGRATION_TEMPLATE_NAME
        )
        self.assertIsInstance(result, Template)
        self.assertIn(
            "apiVersion", result.template
        )
        self.assertIn(
            "oran-o2-db-migration",
            result.template
        )
