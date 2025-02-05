import inspect
import sys
import threading
from uuid import uuid4

import mock

from ddtrace.debugging._probe.model import DDExpression
from ddtrace.debugging._signal.collector import SignalCollector
from ddtrace.debugging._signal.model import SignalState
from ddtrace.debugging._signal.snapshot import Snapshot
from tests.debugging.utils import create_snapshot_line_probe


def mock_encoder(wraps=None):
    encoder = mock.Mock(wraps=wraps)
    snapshot_encoder = mock.Mock()
    encoder._encoders = {Snapshot: snapshot_encoder}

    return encoder, snapshot_encoder


def test_collector_cond():
    encoder, _ = mock_encoder()

    collector = SignalCollector(encoder=encoder)

    def foo(a=42):
        c = True  # noqa
        snapshot = Snapshot(
            probe=create_snapshot_line_probe(
                probe_id=uuid4(),
                source_file="file.py",
                line=123,
                condition=DDExpression("a not null", lambda _: _["a"] is not None),
            ),
            frame=sys._getframe(),
            args=[("a", 42)],
            thread=threading.current_thread(),
        )
        snapshot.line()
        collector.push(snapshot)

    foo()

    def bar(b=None):
        snapshot = Snapshot(
            probe=create_snapshot_line_probe(
                probe_id=uuid4(),
                source_file="file.py",
                line=123,
                condition=DDExpression("b not null", lambda _: _["b"] is not None),
            ),
            frame=sys._getframe(),
            args=[("b", None)],
            thread=threading.current_thread(),
        )
        snapshot.line()
        collector.push(snapshot)

    bar()

    encoder.put.assert_called_once()


def test_collector_collect_enqueue_only_commit_state():
    encoder, _ = mock_encoder()

    collector = SignalCollector(encoder=encoder)
    for i in range(10):
        mocked_signal = mock.Mock()
        with collector.attach(mocked_signal):
            mocked_signal.enter.assert_called_once()
            mocked_signal.state = SignalState.DONE_AND_COMMIT if i % 2 == 0 else SignalState.SKIP_COND
        mocked_signal.exit.assert_called_once()

    assert len(encoder.put.mock_calls) == 5


def test_collector_push_enqueue():
    encoder, _ = mock_encoder()

    collector = SignalCollector(encoder=encoder)
    for _ in range(10):
        snapshot = Snapshot(
            probe=create_snapshot_line_probe(probe_id=uuid4(), source_file="file.py", line=123),
            frame=inspect.currentframe(),
            thread=threading.current_thread(),
        )
        snapshot.line()
        collector.push(snapshot)

    assert len(encoder.put.mock_calls) == 10
