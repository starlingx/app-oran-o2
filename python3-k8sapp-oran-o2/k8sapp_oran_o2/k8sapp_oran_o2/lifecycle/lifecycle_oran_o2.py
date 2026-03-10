#
# Copyright (c) 2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

""" System inventory App lifecycle operator."""
import os
from string import Template

from kubernetes import client
from kubernetes import utils
from oslo_log import log as logging

from sysinv.common import constants
from sysinv.common import exception
from sysinv.helm import lifecycle_base as base
from sysinv.helm.lifecycle_constants import LifecycleConstants


LOG = logging.getLogger(__name__)


class OranO2AppLifecycleOperator(base.AppLifecycleOperator):
    # Class constants
    MIGRATION_TEMPLATE_NAME = "job-run-db-migrations.yaml"
    MIGRATION_LABEL_SELECTOR = "app=oran-o2-db-migration"
    NAMESPACE = "oran-o2"
    TEMP_DIR = "/tmp"
    TEMPLATES_DIR = "templates"

    def app_lifecycle_actions(
        self, context, conductor_obj, app_op, app, hook_info
    ):
        """Perform lifecycle actions for an operation

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        :param hook_info: LifecycleHookInfo object

        """
        # Manifest request
        if hook_info.lifecycle_type == LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST:
            LOG.debug(f"Executing app_lifecycle_actions for {app.name} app")
            # Pre Apply Request
            if (hook_info.operation == constants.APP_APPLY_OP
                    and hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_PRE):
                LOG.debug(f"Pre Update Request {hook_info.lifecycle_type}")
                return self._run_db_migration(context, conductor_obj, app_op, app)

            # Post Apply Request
            if (hook_info.operation == constants.APP_APPLY_OP
                    and hook_info.relative_timing == LifecycleConstants.APP_LIFECYCLE_TIMING_POST):
                LOG.debug(f"Post Apply Request {hook_info.lifecycle_type}")
                return self._cleanup_migration_resources(context, conductor_obj, app_op, app)

        super(OranO2AppLifecycleOperator, self).app_lifecycle_actions(
            context, conductor_obj, app_op, app, hook_info
        )

    def _run_db_migration(self, context, conductor_obj, app_op, app):
        """Run database migration

        Creates Kubernetes Job, ConfigMap, ServiceAccount, and RBAC resources
        to execute SQL migration scripts on the ORAN O2 database.

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        """
        try:
            migration_job_template = self._read_template(self.MIGRATION_TEMPLATE_NAME)
            resource_path = os.path.join(self.TEMP_DIR, self.MIGRATION_TEMPLATE_NAME)
            self._create_kube_resource_file(resource_path, migration_job_template.template)

            kube_client = client.ApiClient()
            utils.create_from_yaml(kube_client, resource_path)

        except Exception as e:
            LOG.error(f"Database migration failed for app {app.name}: {str(e)}")
            self._cleanup_migration_resources(context, conductor_obj, app_op, app)
            raise exception.LifecycleSemanticCheckException(
                f"Database migration failed: {str(e)}")

    def _cleanup_migration_resources(self, context, conductor_obj, app_op, app):
        """Clean up all database migration resources

        Removes Job, ConfigMap, ServiceAccount, Role, and RoleBinding resources
        created for database migration using label selector.

        :param context: request context, can be None
        :param conductor_obj: conductor object, can be None
        :param app_op: AppOperator object
        :param app: AppOperator.Application object
        """
        kube_client = client.ApiClient()
        v1 = client.CoreV1Api(kube_client)
        batch_v1 = client.BatchV1Api(kube_client)
        rbac_v1 = client.RbacAuthorizationV1Api(kube_client)

        try:
            LOG.debug(f"Starting cleanup of migration resources for app: {app.name}")

            # Delete all resources with the migration label selector
            cleanup_operations = [
                (batch_v1.delete_collection_namespaced_job, "Jobs"),
                (v1.delete_collection_namespaced_pod, "Pods"),
                (v1.delete_collection_namespaced_config_map, "ConfigMaps"),
                (v1.delete_collection_namespaced_service_account, "ServiceAccounts"),
                (rbac_v1.delete_collection_namespaced_role, "Roles"),
                (rbac_v1.delete_collection_namespaced_role_binding, "RoleBindings")
            ]

            for operation, resource_type in cleanup_operations:
                operation(
                    namespace=self.NAMESPACE,
                    label_selector=self.MIGRATION_LABEL_SELECTOR
                )

        except Exception as e:
            LOG.warning(f"Failed to cleanup migration resources for app {app.name}: {str(e)}")

    def _read_template(self, template_name):
        """Read a template file and return a Template object.

        :param template_name (str): Name of the template file to read
        """
        LOG.debug(f"Reading template: {template_name}")
        template_path = os.path.join(os.path.dirname(__file__), self.TEMPLATES_DIR, template_name)
        with open(template_path, "r") as file:
            return Template(file.read())

    def _create_kube_resource_file(self, path, value):
        """Create a Kubernetes resource file with the given value.

        :param path (str): Path to the file to be created
        :param value (str): Value to be written to the file
        """
        LOG.debug(f"Creating Kubernetes resource file: {path}")
        with open(path, 'w') as output_file:
            output_file.write(value)
