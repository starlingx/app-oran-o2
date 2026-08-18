#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Tests for _dump_db_if_pg_version_changed, _dump_db,
and _cleanup_dump_resources methods."""

from string import Template
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest.mock import mock_open

from sysinv.common import constants
from sysinv.helm.lifecycle_constants import LifecycleConstants

from k8sapp_oran_o2.lifecycle.lifecycle_oran_o2 import \
    OranO2AppLifecycleOperator
from k8sapp_oran_o2.tests.base import BaseLifecycleTestCase
from k8sapp_oran_o2.tests.test_constants import APP_NAME
from k8sapp_oran_o2.tests.test_constants import PG_DUMP_LABEL_SELECTOR
from k8sapp_oran_o2.tests.test_constants import PG_DUMP_TEMPLATE_NAME
from k8sapp_oran_o2.tests.test_constants import SAMPLE_TEMPLATE_CONTENT
from k8sapp_oran_o2.tests.test_helpers import call_lifecycle_actions
from k8sapp_oran_o2.tests.test_helpers import setup_hook_info
from k8sapp_oran_o2.tests.test_helpers import setup_manifest_pre_apply
from k8sapp_oran_o2.tests.test_helpers import setup_resource_pre_downgrade


class TestDumpDbIfPgVersionChanged(BaseLifecycleTestCase):
    """Tests for _dump_db_if_pg_version_changed."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.app.inst_path = "/tmp/apps/oran-o2"

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.yaml.safe_load'
    )
    @patch('builtins.open', mock_open(read_data=""))
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_dump_db'
    )
    def test_pg_version_changed_triggers_dump(
        self, mock_dump_db, mock_glob,
        mock_yaml_load, mock_api_client,
        mock_core_v1
    ):
        """Dump triggered when postgres image differs."""
        mock_glob.return_value = [
            "/tmp/apps/oran-o2/charts/static-overrides.yaml"
        ]
        mock_yaml_load.return_value = {
            'o2ims': {'images': {'tags': {
                'postgres': 'postgres:16.0'
            }}}
        }

        mock_pod = MagicMock()
        mock_container = MagicMock()
        mock_container.image = 'postgres:15.0'
        mock_pod.spec.containers = [mock_container]
        mock_core_v1.return_value \
            .list_namespaced_pod.return_value.items = [mock_pod]

        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

        mock_dump_db.assert_called_once_with(self.app)

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.yaml.safe_load'
    )
    @patch('builtins.open', mock_open(read_data=""))
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_dump_db'
    )
    def test_pg_version_same_no_dump(
        self, mock_dump_db, mock_glob,
        mock_yaml_load, mock_api_client,
        mock_core_v1
    ):
        """No dump when postgres image is same."""
        mock_glob.return_value = [
            "/tmp/apps/oran-o2/charts/static-overrides.yaml"
        ]
        mock_yaml_load.return_value = {
            'o2ims': {'images': {'tags': {
                'postgres': 'postgres:15.0'
            }}}
        }

        mock_pod = MagicMock()
        mock_container = MagicMock()
        mock_container.image = 'postgres:15.0'
        mock_pod.spec.containers = [mock_container]
        mock_core_v1.return_value \
            .list_namespaced_pod.return_value.items = [mock_pod]

        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

        mock_dump_db.assert_not_called()

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    def test_no_static_overrides_returns(
        self, mock_glob
    ):
        """Returns early when no overrides found."""
        mock_glob.return_value = []

        # Should not raise
        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.yaml.safe_load'
    )
    @patch('builtins.open', mock_open(read_data=""))
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    def test_no_pods_returns(
        self, mock_glob, mock_yaml_load,
        mock_api_client, mock_core_v1
    ):
        """Returns when no pods found."""
        mock_glob.return_value = ["/tmp/overrides.yaml"]
        mock_yaml_load.return_value = {
            'o2ims': {'images': {'tags': {
                'postgres': 'postgres:16.0'
            }}}
        }
        mock_core_v1.return_value \
            .list_namespaced_pod.return_value.items = []

        # Should not raise
        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    def test_exception_caught(self, mock_glob):
        """Exception is caught gracefully."""
        mock_glob.side_effect = Exception("glob error")

        # Should not raise
        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.yaml.safe_load'
    )
    @patch('builtins.open', mock_open(read_data=""))
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.glob.glob'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_dump_db'
    )
    def test_non_postgres_container_skipped(
        self, mock_dump_db, mock_glob,
        mock_yaml_load, mock_api_client,
        mock_core_v1
    ):
        """Containers without postgres in name are skipped."""
        mock_glob.return_value = ["/tmp/overrides.yaml"]
        mock_yaml_load.return_value = {
            'o2ims': {'images': {'tags': {
                'postgres': 'postgres:16.0'
            }}}
        }

        mock_pod = MagicMock()
        mock_container = MagicMock()
        mock_container.image = 'redis:7.0'
        mock_pod.spec.containers = [mock_container]
        mock_core_v1.return_value \
            .list_namespaced_pod.return_value.items = [mock_pod]

        self.operator._dump_db_if_pg_version_changed(
            self.app
        )

        mock_dump_db.assert_not_called()


class TestDumpDb(BaseLifecycleTestCase):
    """Tests for _dump_db method."""

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_dump_resources'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.time.sleep'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
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
    def test_dump_db_success(
        self, mock_read_template,
        mock_create_file, mock_api_client,
        mock_create_from_yaml, mock_batch_v1,
        mock_sleep, mock_cleanup
    ):
        """Successful dump with job succeeded."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template

        mock_job = MagicMock()
        mock_job.status.succeeded = True
        mock_job.status.failed = None
        mock_batch_v1.return_value \
            .read_namespaced_job.return_value = mock_job

        self.operator._dump_db(self.app)

        mock_read_template.assert_called_once_with(
            PG_DUMP_TEMPLATE_NAME
        )
        mock_create_file.assert_called_once()
        mock_create_from_yaml.assert_called_once()
        mock_cleanup.assert_called_once()

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_dump_resources'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.time.sleep'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
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
    def test_dump_db_job_failed(
        self, mock_read_template,
        mock_create_file, mock_api_client,
        mock_create_from_yaml, mock_batch_v1,
        mock_sleep, mock_cleanup
    ):
        """Job fails - logged and cleanup called."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template

        mock_job = MagicMock()
        mock_job.status.succeeded = None
        mock_job.status.failed = True
        mock_batch_v1.return_value \
            .read_namespaced_job.return_value = mock_job

        self.operator._dump_db(self.app)

        mock_cleanup.assert_called_once()

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_dump_resources'
    )
    @patch.object(
        OranO2AppLifecycleOperator, '_read_template'
    )
    def test_dump_db_exception_caught(
        self, mock_read_template, mock_cleanup
    ):
        """Exception caught, cleanup still called."""
        mock_read_template.side_effect = (
            Exception("template error")
        )

        # Should not raise
        self.operator._dump_db(self.app)

        mock_cleanup.assert_called_once()

    @patch.object(
        OranO2AppLifecycleOperator,
        '_cleanup_dump_resources'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.time.sleep'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
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
    def test_dump_db_polls_until_succeeded(
        self, mock_read_template,
        mock_create_file, mock_api_client,
        mock_create_from_yaml, mock_batch_v1,
        mock_sleep, mock_cleanup
    ):
        """Polls job status until succeeded."""
        mock_template = MagicMock(spec=Template)
        mock_template.template = SAMPLE_TEMPLATE_CONTENT
        mock_read_template.return_value = mock_template

        # First two polls: not done. Third: succeeded.
        mock_job_pending = MagicMock()
        mock_job_pending.status.succeeded = None
        mock_job_pending.status.failed = None
        mock_job_done = MagicMock()
        mock_job_done.status.succeeded = True
        mock_job_done.status.failed = None

        mock_batch_v1.return_value \
            .read_namespaced_job.side_effect = [
                mock_job_pending, mock_job_pending,
                mock_job_done
            ]

        self.operator._dump_db(self.app)

        self.assertEqual(mock_sleep.call_count, 2)
        mock_cleanup.assert_called_once()


class TestCleanupDumpResources(BaseLifecycleTestCase):
    """Tests for _cleanup_dump_resources."""

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_calls_all_operations(
        self, mock_api_client, mock_batch_v1,
        mock_core_v1, mock_rbac_v1
    ):
        """All 5 cleanup operations called."""
        self.operator._cleanup_dump_resources()

        batch_api = mock_batch_v1.return_value
        batch_api.delete_collection_namespaced_job \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=PG_DUMP_LABEL_SELECTOR
            )
        core_api = mock_core_v1.return_value
        core_api.delete_collection_namespaced_pod \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=PG_DUMP_LABEL_SELECTOR
            )
        core_api \
            .delete_collection_namespaced_service_account \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=PG_DUMP_LABEL_SELECTOR
            )
        rbac_api = mock_rbac_v1.return_value
        rbac_api.delete_collection_namespaced_role \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=PG_DUMP_LABEL_SELECTOR
            )
        rbac_api \
            .delete_collection_namespaced_role_binding \
            .assert_called_once_with(
                namespace=APP_NAME,
                label_selector=PG_DUMP_LABEL_SELECTOR
            )

    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.RbacAuthorizationV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.CoreV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.BatchV1Api'
    )
    @patch(
        'k8sapp_oran_o2.lifecycle.lifecycle_oran_o2'
        '.client.ApiClient'
    )
    def test_cleanup_exception_caught(
        self, mock_api_client, mock_batch_v1,
        mock_core_v1, mock_rbac_v1
    ):
        """Exception during cleanup is caught."""
        mock_batch_v1.return_value \
            .delete_collection_namespaced_job \
            .side_effect = Exception("api error")

        # Should not raise
        self.operator._cleanup_dump_resources()


class TestAppLifecycleActionsNewPaths(
    BaseLifecycleTestCase
):
    """Tests for new dispatch paths in app_lifecycle_actions."""

    @patch.object(
        OranO2AppLifecycleOperator,
        '_run_db_migration'
    )
    @patch.object(
        OranO2AppLifecycleOperator,
        '_dump_db_if_pg_version_changed'
    )
    def test_pre_apply_calls_dump_then_migration(
        self, mock_dump, mock_migration
    ):
        """Pre-apply calls dump check then migration."""
        setup_manifest_pre_apply(self.hook_info)

        call_lifecycle_actions(
            self.operator, self.context,
            self.conductor_obj, self.app_op,
            self.app, self.hook_info
        )

        mock_dump.assert_called_once_with(self.app)
        mock_migration.assert_called_once()

    @patch.object(
        OranO2AppLifecycleOperator,
        '_dump_db_if_pg_version_changed'
    )
    def test_resource_pre_downgrade_calls_dump(
        self, mock_dump
    ):
        """Resource pre-downgrade calls dump check."""
        setup_resource_pre_downgrade(self.hook_info)

        call_lifecycle_actions(
            self.operator, self.context,
            self.conductor_obj, self.app_op,
            self.app, self.hook_info
        )

        mock_dump.assert_called_once_with(self.app)

    @patch(
        'sysinv.helm.lifecycle_base'
        '.AppLifecycleOperator.app_lifecycle_actions'
    )
    def test_resource_non_downgrade_falls_through(
        self, mock_super
    ):
        """Resource with non-downgrade op calls super."""
        setup_hook_info(
            self.hook_info,
            LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE,
            constants.APP_APPLY_OP,
            LifecycleConstants.APP_LIFECYCLE_TIMING_PRE,
        )

        self.operator.app_lifecycle_actions(
            self.context, self.conductor_obj,
            self.app_op, self.app, self.hook_info
        )

        mock_super.assert_called_once()
