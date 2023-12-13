#
# Copyright (c) 2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

from k8sapp_oran_o2.common import constants as app_constants

from sysinv.common import exception
from sysinv.helm import base


class Orano2Helm(base.BaseHelm):
    """Class to encapsulate helm operations for the oran-o2 chart"""

    SUPPORTED_NAMESPACES = base.BaseHelm.SUPPORTED_NAMESPACES + \
        [app_constants.HELM_NS_ORAN_O2]
    SUPPORTED_APP_NAMESPACES = {
        app_constants.HELM_APP_ORAN_O2:
            base.BaseHelm.SUPPORTED_NAMESPACES +
            [app_constants.HELM_NS_ORAN_O2]
    }

    CHART = app_constants.HELM_CHART_ORAN_O2

    SERVICE_NAME = app_constants.HELM_APP_ORAN_O2

    def get_namespaces(self):
        return self.SUPPORTED_NAMESPACES

    def get_overrides(self, namespace=None):
        overrides = {
            app_constants.HELM_NS_ORAN_O2: {
                'replicaCount': self._num_replicas_for_platform_app(),
            }
        }
        if namespace in self.SUPPORTED_NAMESPACES:
            return overrides[namespace]
        elif namespace:
            raise exception.InvalidHelmNamespace(chart=self.CHART,
                                                 namespace=namespace)
        else:
            return overrides
