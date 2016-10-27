#!/usr/bin/env python
import unittest
import os
import mock

# patch reading of queue.yaml
TESTCONFIG_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "deferred_manager",
    "testconfig")

mocked_open = mock.mock_open()
with open(os.path.join(TESTCONFIG_DIR, 'queue.yaml')) as fh,\
        mock.patch('__builtin__.open', mocked_open):
    mocked_open.return_value = fh
    from deferred_manager import tests

suite = unittest.TestLoader().loadTestsFromModule(tests)
unittest.TextTestRunner(verbosity=2).run(suite)
