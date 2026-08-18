#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Branch coverage tests for lifecycle_oran_o2 module.

These tests exercise conditional branch paths in
app_lifecycle_actions and _cleanup_migration_resources
to ensure full branch coverage.
"""

import os
from string import Template
from unittest.mock import MagicMock
from unittest.mock import patch

from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm.lifecycle_constants import LifecycleConstants

from k8sapp_oran_o2.lifecycle.lifecycle_oran_o2 import \
    OranO2AppLifecycleOperator
from k8sapp_oran_o2.tests.base import BaseLifecycleTestCase
from k8sapp_oran_o2.tests.test_constants import APP_NAME
from k8sapp_oran_o2.tests.test_constants import MIGRATION_LABEL_SELECTOR
from k8sapp_oran_o2.tests.test_constants import MIGRATION_TEMPLATE_NAME
from k8sapp_oran_o2.tests.test_constants import SAMPLE_TEMPLATE_CONTENT
from k8sapp_oran_o2.tests.test_constants import TEMP_DIR


class TestAppLifecycleActionsBranches(BaseLifecycleTestCase):
    """Test all branch paths in app_lifecycle_actions.

    Exercises every combination of lifecycle_type, operation,
    and relative_timing to cover all if/and conditions.
    """

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.OranO2AppLifecycleOperator._run_db_migration'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.OranO2AppLifecycleOperator'
        '._dump_db_if_pg_version_changed'
    )
    def test_manifest_apply_pre_returns_migration(
        self, mock_dump, mock_migration
    ):
        """Branch: manifest AND apply AND pre -> _run_db_migration."""
        mock_migration.return_value = "migration_result"
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        result = self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        self.assertEqual(result, "migration_result")
        mock_migration.assert_called_once()
        mock_dump.assert_called_once()

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.OranO2AppLifecycleOperator'
        '._cleanup_migration_resources'
    )
    def test_manifest_apply_post_returns_cleanup(
        self, mock_cleanup
    ):
        """Branch: manifest AND apply AND post -> _cleanup."""
        mock_cleanup.return_value = "cleanup_result"
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_POST
        )

        result = self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        self.assertEqual(result, "cleanup_result")
        mock_cleanup.assert_called_once()

    @patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.app_lifecycle_actions'
    )
    def test_manifest_apply_other_timing_falls_through(
        self, mock_super
    ):
        """Branch: manifest AND apply but NOT pre/post -> super."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = "other_timing"

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_super.assert_called_once_with(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

    @patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.app_lifecycle_actions'
    )
    def test_manifest_remove_op_falls_through(
        self, mock_super
    ):
        """Branch: manifest AND remove_op -> super."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_REMOVE_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_super.assert_called_once()

    @patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.app_lifecycle_actions'
    )
    def test_non_manifest_type_falls_through(
        self, mock_super
    ):
        """Branch: non-manifest lifecycle_type -> super."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_super.assert_called_once()

    @patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.app_lifecycle_actions'
    )
    def test_rbd_type_falls_through(
        self, mock_super
    ):
        """Branch: rbd lifecycle_type -> super."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_RBD
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_super.assert_called_once()


class TestCleanupMigrationResourcesBranches(
    BaseLifecycleTestCase
):
    """Test branch paths in _cleanup_migration_resources.

    Exercises the for loop iteration and per-operation calls
    to ensure all 6 cleanup operations are covered.
    """

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_calls_all_six_operations(
        self,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Verify all 6 cleanup operations are invoked."""
        core_api = mock_core_v1.return_value
        batch_api = mock_batch_v1.return_value
        rbac_api = mock_rbac_v1.return_value

        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

        # Verify each operation called with correct args
        batch_api.delete_collection_namespaced_job \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )
        core_api.delete_collection_namespaced_pod \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )
        core_api.delete_collection_namespaced_config_map \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )
        core_api.delete_collection_namespaced_service_account \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )
        rbac_api.delete_collection_namespaced_role \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )
        rbac_api.delete_collection_namespaced_role_binding \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=MIGRATION_LABEL_SELECTOR
            )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_exception_in_first_op_caught(
        self,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Branch: exception raised inside for loop is caught."""
        batch_api = mock_batch_v1.return_value
        batch_api.delete_collection_namespaced_job \
            .side_effect = Exception("connection refused")

        # Should not raise - exception is caught
        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_exception_in_middle_op(
        self,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Branch: exception in middle operation is caught."""
        core_api = mock_core_v1.return_value
        core_api.delete_collection_namespaced_config_map \
            .side_effect = Exception("timeout")

        # Should not raise
        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_exception_in_rbac_op(
        self,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Branch: exception in RBAC cleanup is caught."""
        rbac_api = mock_rbac_v1.return_value
        rbac_api.delete_collection_namespaced_role_binding \
            .side_effect = Exception("forbidden")

        # Should not raise
        # pylint: disable=protected-access
        self.operator._cleanup_migration_resources(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )


class TestRunDbMigrationBranches(BaseLifecycleTestCase):
    """Test branch paths in _run_db_migration.

    Exercises the try/except branches with different
    failure points to ensure all paths are covered.
    """

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.utils.create_from_yaml'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_success_path_no_exception(
        self,
        mock_read_template,
        mock_create_file,
        mock_api_client,
        mock_create_from_yaml
    ):
        """Branch: try block completes without exception."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template

        # pylint: disable=protected-access
        self.operator._run_db_migration(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

        expected_path = os.path.join(
            TEMP_DIR, MIGRATION_TEMPLATE_NAME
        )
        mock_read_template.assert_called_once_with(
            MIGRATION_TEMPLATE_NAME
        )
        mock_create_file.assert_called_once_with(
            expected_path, SAMPLE_TEMPLATE_CONTENT
        )
        mock_api_client.assert_called_once()
        mock_create_from_yaml.assert_called_once_with(
            mock_api_client.return_value, expected_path
        )

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_exception_in_read_template(
        self, mock_read_template, mock_cleanup
    ):
        """Branch: exception in _read_template -> cleanup + raise."""
        mock_read_template.side_effect = (
            FileNotFoundError("template missing")
        )

        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ):
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context, self.conductor_obj,
                self.app_op, self.app
            )

        mock_cleanup.assert_called_once_with(
            self.context, self.conductor_obj,
            self.app_op, self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_exception_in_create_resource_file(
        self,
        mock_read_template,
        mock_create_file,
        mock_cleanup,
        mock_api_client
    ):
        """Branch: exception in _create_kube_resource_file."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template
        mock_create_file.side_effect = (
            PermissionError("write denied")
        )

        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ):
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context, self.conductor_obj,
                self.app_op, self.app
            )

        mock_cleanup.assert_called_once()

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.utils.create_from_yaml'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_exception_in_create_from_yaml(
        self,
        mock_read_template,
        mock_create_file,
        mock_cleanup,
        mock_api_client,
        mock_create_from_yaml
    ):
        """Branch: exception in create_from_yaml -> cleanup + raise."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template
        mock_create_from_yaml.side_effect = (
            Exception("invalid yaml")
        )

        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ):
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context, self.conductor_obj,
                self.app_op, self.app
            )

        mock_cleanup.assert_called_once()

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_migration_resources'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_exception_message_preserved(
        self, mock_read_template, mock_cleanup
    ):
        """Branch: original error message in raised exception."""
        mock_read_template.side_effect = (
            RuntimeError("specific error detail")
        )

        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ) as ctx:
            # pylint: disable=protected-access
            self.operator._run_db_migration(
                self.context, self.conductor_obj,
                self.app_op, self.app
            )

        self.assertIn(
            "specific error detail", str(ctx.exception)
        )


class TestAppLifecycleActionsIntegration(
    BaseLifecycleTestCase
):
    """Integration tests exercising app_lifecycle_actions
    without mocking the internal methods (except k8s calls).

    These tests hit the actual code paths through the
    dispatching logic into the real methods.
    """

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.utils.create_from_yaml'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_dump_db_if_pg_version_changed'
    )
    def test_pre_apply_runs_full_migration_path(
        self,
        mock_dump,
        mock_read_template,
        mock_create_file,
        mock_api_client,
        mock_create_from_yaml
    ):
        """Integration: pre-apply dispatches to real _run_db_migration."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template

        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_read_template.assert_called_once_with(
            MIGRATION_TEMPLATE_NAME
        )
        mock_create_file.assert_called_once()
        mock_create_from_yaml.assert_called_once()

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_post_apply_runs_full_cleanup_path(
        self,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Integration: post-apply dispatches to real _cleanup."""
        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_POST
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        # Verify actual cleanup was called through
        batch_api = mock_batch_v1.return_value
        batch_api.delete_collection_namespaced_job \
            .assert_called_once()
        core_api = mock_core_v1.return_value
        core_api.delete_collection_namespaced_pod \
            .assert_called_once()

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_create_kube_resource_file'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_dump_db_if_pg_version_changed'
    )
    def test_pre_apply_failure_triggers_cleanup(
        self,
        mock_dump,
        mock_read_template,
        mock_create_file,
        mock_api_client,
        mock_core_v1,
        mock_batch_v1,
        mock_rbac_v1
    ):
        """Integration: pre-apply failure triggers real cleanup."""
        mock_read_template.side_effect = (
            Exception("template error")
        )

        self.hook_info.lifecycle_type = (
            LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST
        )
        self.hook_info.operation = constants.APP_APPLY_OP
        self.hook_info.relative_timing = (
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE
        )

        with self.assertRaises(
            exception.LifecycleSemanticCheckException
        ):
            self.operator.app_lifecycle_actions(
                self.context, self.conductor_obj,
                self.app_op, self.app, self.hook_info
            )

        # Verify cleanup was triggered
        batch_api = mock_batch_v1.return_value
        batch_api.delete_collection_namespaced_job \
            .assert_called_once()
