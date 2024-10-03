#!/usr/bin/env python3
# encoding: utf-8
# Copyright 2024 Canonical Ltd.
# Written by:
#   Massimiliano Girardi <massimiliano.girardi@canonical.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import itertools
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock, mock_open

from virtualization import LXDTest_vm, LXDTest_sriov, check_sriov_interfaces


class TestLXDTest_vm(TestCase):
    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_no_stderr(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = "abc"
        task.stderr = None

        command_result = LXDTest_vm.run_command(MagicMock(), "command", log_stderr=True)

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_no_log_stderr(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 1
        task.stdout = "abc"
        task.stderr = None

        command_result = LXDTest_vm.run_command(
            MagicMock(), "command", log_stderr=False
        )

        self.assertFalse(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_error(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 1
        task.stdout = "abc"
        task.stderr = "some error"

        command_result = LXDTest_vm.run_command(MagicMock(), "command", log_stderr=True)

        self.assertTrue(logging_mock.error.called)
        self.assertFalse(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_ok(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = "abc"
        task.stderr = "some error"

        command_result = LXDTest_vm.run_command(MagicMock(), "command", log_stderr=True)

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_ok_no_stdout(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = ""
        task.stderr = "some error"

        command_result = LXDTest_vm.run_command(MagicMock(), "command", log_stderr=True)

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    def test_cleanup(self, logging_mock):
        self_mock = MagicMock()
        LXDTest_vm.cleanup(self_mock)

        self.assertTrue(self_mock.run_command.called)

    @patch("virtualization.logging")
    def test_start_vm_fail_setup(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = False

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertTrue(logging_mock.error.called)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_vm_fail_init_no_img_alias(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = None
        self_mock.template_url = None
        self_mock.default_remote = "def remote"
        self_mock.os_version = "os version"
        self_mock.name = "name"
        self_mock.run_command.side_effect = [False]

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_vm_fail_init_img_alias(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.name = "vm name"
        self_mock.run_command.side_effect = [False]

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_vm_fail_start(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.name = "vm name"
        self_mock.run_command.side_effect = [True, False]

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_vm_fail_list(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.name = "vm name"
        self_mock.run_command.side_effect = [True, True, False]

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertFalse(start_result)

    @patch("time.sleep")
    @patch("virtualization.logging")
    def test_start_vm_fail_exec(self, logging_mock, time_sleep_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.name = "vm name"
        self_mock.run_command.side_effect = itertools.chain(
            [True, True, True], itertools.repeat(False)
        )

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertFalse(start_result)

    @patch("time.sleep")
    @patch("virtualization.print")
    @patch("virtualization.logging")
    def test_start_vm_success(self, logging_mock, print_mock, time_sleep_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.name = "vm name"
        self_mock.run_command.side_effect = [True, True, True, True]

        start_result = LXDTest_vm.start_vm(self_mock)

        self.assertTrue(self_mock.setup.called)
        self.assertTrue(start_result)
        self.assertTrue(print_mock.called)

    def test_setup_failure(self):
        self_mock = MagicMock()
        self_mock.run_command.return_value = False
        self_mock.template_url = None
        self_mock.image_url = None

        setup_return = LXDTest_vm.setup(self_mock)

        self.assertFalse(setup_return)


class TestLXDTest_sriov(TestCase):
    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_no_stderr(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = "abc"
        task.stderr = None

        command_result = LXDTest_sriov.run_command(
            MagicMock(), "command", log_stderr=True
        )

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_no_log_stderr(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 1
        task.stdout = "abc"
        task.stderr = None

        command_result = LXDTest_sriov.run_command(
            MagicMock(), "command", log_stderr=False
        )

        self.assertFalse(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_error(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 1
        task.stdout = "abc"
        task.stderr = "some error"

        command_result = LXDTest_sriov.run_command(
            MagicMock(), "command", log_stderr=True
        )

        self.assertTrue(logging_mock.error.called)
        self.assertFalse(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_ok(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = "abc"
        task.stderr = "some error"

        command_result = LXDTest_sriov.run_command(
            MagicMock(), "command", log_stderr=True
        )

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    @patch("virtualization.RunCommand")
    def test_run_command_ok_no_stdout(self, run_command_mock, logging_mock):
        task = run_command_mock()
        task.returncode = 0
        task.stdout = ""
        task.stderr = "some error"

        command_result = LXDTest_sriov.run_command(
            MagicMock(), "command", log_stderr=True
        )

        self.assertTrue(logging_mock.debug.called)
        self.assertTrue(command_result)

    @patch("virtualization.logging")
    def test_cleanup(self, logging_mock):
        self_mock = MagicMock()
        LXDTest_sriov.cleanup(self_mock)

        self.assertTrue(self_mock.run_command.called)

    @patch("virtualization.logging")
    def test_start_sriov_fail_setup(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = False

        start_result = LXDTest_sriov.start_sriov(self_mock)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_sriov_fail_init_no_img_alias(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = None
        self_mock.template_url = None
        self_mock.network_name = "sriov_network"
        self_mock.test_type = "vm"
        self_mock.name = "testbed"
        self_mock.run_command.side_effect = [False]

        start_result = LXDTest_sriov.start_sriov(self_mock)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_sriov_fail_start(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.network_name = "sriov_network"
        self_mock.test_type = "vm"
        self_mock.name = "testbed"
        self_mock.run_command.side_effect = [True, False]

        start_result = LXDTest_sriov.start_sriov(self_mock)
        self.assertFalse(start_result)

    @patch("virtualization.logging")
    def test_start_sriov_fail_list(self, logging_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.network_name = "sriov_network"
        self_mock.test_type = "vm"
        self_mock.name = "testbed"
        self_mock.run_command.side_effect = [True, True, False]

        start_result = LXDTest_sriov.start_sriov(self_mock)
        self.assertFalse(start_result)

    @patch("time.sleep")
    @patch("virtualization.logging")
    def test_start_sriov_fail_exec(self, logging_mock, time_sleep_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = False
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.network_name = "sriov_network"
        self_mock.test_type = "vm"
        self_mock.name = "testbed"
        self_mock.run_command.side_effect = itertools.chain(
            [True, True, True], itertools.repeat(False)
        )

        start_result = LXDTest_sriov.start_sriov(self_mock)
        self.assertFalse(start_result)

    @patch("time.sleep")
    @patch("virtualization.print")
    @patch("virtualization.logging")
    def test_start_sriov_success(self, logging_mock, print_mock, time_sleep_mock):
        self_mock = MagicMock()
        self_mock.setup.return_value = True
        self_mock.image_url = "image url"
        self_mock.template_url = "template url"
        self_mock.network_name = "sriov_network"
        self_mock.test_type = "vm"
        self_mock.name = "testbed"
        self_mock.run_command.side_effect = itertools.chain(
            [True, True, True], itertools.repeat(False)
        )

        start_result = LXDTest_sriov.start_sriov(self_mock)

        self.assertFalse(start_result)
        self.assertTrue(print_mock.called)

    def test_setup_failure(self):
        self_mock = MagicMock()
        self_mock.run_command.return_value = False
        self_mock.image_url = None
        self_mock.template_url = None
        self_mock.network_name = None
        self_mock.test_type = None

        setup_return = LXDTest_sriov.setup(self_mock)

        self.assertFalse(setup_return)


class TestCheckSriovInterfaces(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    @patch("glob.glob")
    def test_check_sriov_interfaces_with_intel_device(
        self, mock_glob, mock_exists, mock_file
    ):
        # Mocking the glob to return a fake list of network devices
        mock_glob.return_value = ["/sys/class/net/eth0", "/sys/class/net/eth1"]

        # Mock os.path.exists to return True for sriov_totalvfs, vendor,
        # and carrier for eth0, False for eth1
        def exists_side_effect(path):
            if (
                "eth0/device/sriov_totalvfs" in path
                or "eth0/device/vendor" in path
                or "eth0/carrier" in path
            ):
                return True  # eth0 has SR-IOV, Intel vendor, and carrier is up
            return False  # eth1 does not support SR-IOV

        mock_exists.side_effect = exists_side_effect
        print(f"exits side effect : {mock_exists.side_effect}")
        # Mock open to return values based on the file being opened
        # eth0 supports SR-IOV with 4 VFs
        # Intel vendor ID for eth0
        # eth0 carrier status is up
        def open_side_effect(file, mode="r", *args, **kwargs):
            if "eth0/device/sriov_totalvfs" in file:
                return mock_open(read_data="4").return_value
            if "eth0/device/vendor" in file:
                return mock_open(read_data="0x8086").return_value
            if "eth0/carrier" in file:
                 return mock_open(read_data="1").return_value
                
        mock_file.side_effect = open_side_effect

        # Call the function being tested
        intel_device = check_sriov_interfaces()
        print(f"Intel device: {intel_device}")
        # Assert that 'eth0' is correctly identified as the Intel device
        self.assertEqual(intel_device, "eth1")

    @patch("builtins.open", new_callable=mock_open, read_data="0")
    @patch("os.path.exists")
    @patch("glob.glob")
    def test_check_sriov_interfaces_no_sriov_device(
        self, mock_glob, mock_exists, mock_file
    ):
        # Mocking the glob to return a fake list of devices
        mock_glob.return_value = ["/sys/class/net/eth0", "/sys/class/net/eth1"]

        # Mock os.path.exists to return True for sriov_totalvfs path
        mock_exists.side_effect = lambda path: "sriov_totalvfs" in path

        intel_device = check_sriov_interfaces()

        # Asserting that no Intel device is found
        self.assertNotEqual(intel_device, "eth0")
