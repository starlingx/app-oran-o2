#
# Copyright (c) 2026 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
"""Shared helper functions for test modules."""

from unittest import mock

from sysinv.common import constants
from sysinv.helm.lifecycle_constants import LifecycleConstants

from k8sapp_oran_o2.helm.oran_o2 import Orano2Helm
from k8sapp_oran_o2.lifecycle.lifecycle_oran_o2 import \
    OranO2AppLifecycleOperator

from k8sapp_oran_o2.tests.test_constants import APP_NAME


def create_lifecycle_operator():
    """Create an OranO2AppLifecycleOperator without __init__."""
    return OranO2AppLifecycleOperator.__new__(
        OranO2AppLifecycleOperator
    )


def create_helm_instance():
    """Create an Orano2Helm instance without __init__."""
    return Orano2Helm.__new__(Orano2Helm)


def create_mock_app():
    """Create a mock app object with standard name."""
    app = mock.MagicMock()
    app.name = APP_NAME
    return app


def setup_hook_info(hook_info, lifecycle_type, operation,
                    timing):
    """Configure hook_info mock with lifecycle parameters.

    :param hook_info: MagicMock hook_info object
    :param lifecycle_type: LifecycleConstants type
    :param operation: constants operation (APP_APPLY_OP, etc.)
    :param timing: LifecycleConstants timing (PRE/POST)
    """
    hook_info.lifecycle_type = lifecycle_type
    hook_info.operation = operation
    hook_info.relative_timing = timing


def setup_manifest_pre_apply(hook_info):
    """Configure hook_info for manifest pre-apply."""
    setup_hook_info(
        hook_info,
        LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST,
        constants.APP_APPLY_OP,
        LifecycleConstants.APP_LIFECYCLE_TIMING_PRE,
    )


def setup_manifest_post_apply(hook_info):
    """Configure hook_info for manifest post-apply."""
    setup_hook_info(
        hook_info,
        LifecycleConstants.APP_LIFECYCLE_TYPE_MANIFEST,
        constants.APP_APPLY_OP,
        LifecycleConstants.APP_LIFECYCLE_TIMING_POST,
    )


def setup_resource_pre_downgrade(hook_info):
    """Configure hook_info for resource pre-downgrade."""
    setup_hook_info(
        hook_info,
        LifecycleConstants.APP_LIFECYCLE_TYPE_RESOURCE,
        constants.APP_DOWNGRADE_OP,
        LifecycleConstants.APP_LIFECYCLE_TIMING_PRE,
    )


def call_lifecycle_actions(operator, context,
                           conductor_obj, app_op,
                           app, hook_info):
    """Invoke app_lifecycle_actions with standard args."""
    return operator.app_lifecycle_actions(
        context, conductor_obj, app_op, app, hook_info
    )
