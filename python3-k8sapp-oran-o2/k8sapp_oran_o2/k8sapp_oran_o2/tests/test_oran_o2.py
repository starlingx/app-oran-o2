# Copyright (c) 2022 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
from k8sapp_oran_o2.tests import test_plugins

from sysinv.db import api as dbapi
from sysinv.tests.db import utils as dbutils
from sysinv.tests.helm import base


class Orano2TestCase(test_plugins.K8SAppOrano2AppMixin,
                          base.HelmTestCaseMixin):

    def setUp(self):
        super(Orano2TestCase, self).setUp()
        self.app = dbutils.create_test_app(name='oran-o2')
        self.dbapi = dbapi.get_instance()
