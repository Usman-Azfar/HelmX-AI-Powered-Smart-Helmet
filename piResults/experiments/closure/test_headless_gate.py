"""Regression coverage for the kernel codec false positive and shared gate."""
import unittest
from unittest.mock import Mock, patch
from headless_gate import interactive, is_interactive


class HeadlessGateTests(unittest.TestCase):
    def test_kernel_codec_is_not_an_ide(self):
        for name in ('irq/49-feb00000.codec', 'codec', 'python', 'bash', None):
            with self.subTest(name=name):
                self.assertFalse(is_interactive(name))

    def test_desktop_and_ide_names(self):
        for name in ('code', 'code-insiders', 'vs-code-server', 'devtool',
                     'devtool-host', 'Xorg', 'Xwayland', 'labwc',
                     'wayvnc', 'rpi-connect', 'rpi-connect-way', 'lightdm'):
            with self.subTest(name=name):
                self.assertTrue(is_interactive(name))

    def test_process_report_excludes_kernel_codec(self):
        processes = [Mock(pid=397, info={'name': 'irq/49-feb00000.codec'}),
                     Mock(pid=900, info={'name': 'code'})]
        with patch('headless_gate.psutil.process_iter', return_value=processes):
            self.assertEqual(interactive(), [{'pid': 900, 'name': 'code'}])


if __name__ == '__main__':
    unittest.main()
