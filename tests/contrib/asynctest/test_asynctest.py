import os
import sys

import pytest

import ddtrace
from ddtrace.contrib.pytest.plugin import is_enabled
from ddtrace.ext import test
from ddtrace.internal.ci_visibility import CIVisibility
from tests.utils import TracerTestCase


class TestPytest(TracerTestCase):
    @pytest.fixture(autouse=True)
    def fixtures(self, testdir, monkeypatch):
        self.testdir = testdir
        self.monkeypatch = monkeypatch

    def inline_run(self, *args):
        """Execute test script with test tracer."""

        class CIVisibilityPlugin:
            @staticmethod
            def pytest_configure(config):
                assert not CIVisibility.enabled
                if is_enabled(config):
                    CIVisibility.enable(tracer=self.tracer, config=ddtrace.config.pytest)

        return self.testdir.inline_run(*args, plugins=[CIVisibilityPlugin()])

    @pytest.mark.skipif(
        sys.version_info >= (3, 11, 0) or sys.version_info <= (3, 6, 0),
        reason="asynctest isn't working on Python 3.11, asynctest "
        "raisesAttributeError: module 'asyncio' has no "
        "attribute 'coroutine'",
    )
    def test_asynctest_not_raise_attribute_error_exception(self):
        """Test AttributeError exception in `ddtrace/vendor/wrapt/wrappers.py` when try to import asynctest package.
        Issue: https://github.com/DataDog/dd-trace-py/issues/4484
        """
        py_file = self.testdir.makepyfile(
            """
        import asynctest
        asynctest.CoroutineMock()

        def test_asynctest():
            assert 1 == 1
        """
        )
        file_name = os.path.basename(py_file.strpath)
        rec = self.inline_run("--ddtrace", file_name)
        rec.assertoutcome(passed=1)
        spans = self.pop_spans()

        assert len(spans) == 1
        assert spans[0].get_tag(test.STATUS) == test.Status.PASS.value
