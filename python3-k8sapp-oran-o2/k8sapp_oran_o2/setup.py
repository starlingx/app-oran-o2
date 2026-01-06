#
# Copyright (c) 2022,2025 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#

import setuptools


setuptools.setup(
    setup_requires=['pbr>=2.0.0'],
    pbr=True,
    include_package_data=True,
    package_data={
        'k8sapp_oran_o2': ['lifecycle/templates/*.yaml']
    },)
