import warnings

import pytest
from harness.src.network import Network

from rraft import (
    MessageType,
    ProgressState,
    Snapshot,
    default_logger,
    INVALID_INDEX,
    RequestSnapshotDroppedError,
)

from harness.utils import (
    new_snapshot,
    new_storage,
    new_test_raft,
    new_message,
    new_test_raft_with_prevote,
)


def testing_snap() -> Snapshot:
    warnings.filterwarnings("ignore")
    return new_snapshot(11, 11, [1, 2])


def test_sending_snapshot_set_pending_snapshot():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    # force set the next of node 1, so that
    # node 1 needs a snapshot
    assert sm.raft.prs().get(2).get_next_idx() == sm.raft_log.first_index()

    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    voter_2 = sm.raft.prs().get(2)
    m.set_index(voter_2.get_next_idx() - 1)
    m.set_reject(True)

    sm.step(m)
    assert sm.raft.prs().get(2).get_pending_snapshot() == 11


def test_pending_snapshot_pause_replication():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()
    sm.raft.prs().get(2).become_snapshot(11)

    sm.step(new_message(2, 1, MessageType.MsgPropose, 1))
    msgs = sm.read_messages()
    assert not msgs


def test_snapshot_failure():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    sm.raft.prs().get(2).set_next_idx(1)
    sm.raft.prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.set_reject(True)
    sm.step(m)
    voter_2 = sm.raft.prs().get(2)

    assert voter_2.get_pending_snapshot() == 0
    assert voter_2.get_next_idx() == 1
    assert voter_2.get_paused()


def test_snapshot_succeed():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    sm.raft.prs().get(2).set_next_idx(1)
    sm.raft.prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.set_reject(False)
    sm.step(m)
    voter_2 = sm.raft.prs().get(2)
    assert voter_2.get_pending_snapshot() == 0
    assert voter_2.get_next_idx() == 12
    assert voter_2.get_paused()


def test_snapshot_abort():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    sm.raft.prs().get(2).set_next_idx(1)
    sm.raft.prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.set_reject(False)
    sm.step(m)

    assert sm.raft.prs().get(2).get_pending_snapshot() == 0
    assert sm.raft.prs().get(2).get_next_idx() == 12


# Initialized storage should be at term 1 instead of 0. Otherwise the case will fail.
def test_snapshot_with_min_term():
    l = default_logger()

    def do_test(pre_vote: bool):
        s1 = new_storage()
        s1.wl().apply_snapshot(new_snapshot(1, 1, [1, 2]))

        n1 = new_test_raft_with_prevote(1, [1, 2], 10, 1, s1, pre_vote, l)

        s2 = new_storage()
        n2 = new_test_raft_with_prevote(2, [], 10, 1, s2, pre_vote, l)

        nt = Network.new([n1, n2], l)
        m = new_message(1, 1, MessageType.MsgHup, 0)
        nt.send([m])

        # 1 will be elected as leader, and then send a snapshot and an empty entry to 2.
        assert nt.peers.get(2).raft_log.first_index() == 2
        assert nt.peers.get(2).raft_log.last_index() == 2

    do_test(True)
    do_test(False)


def test_request_snapshot():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(testing_snap())
    sm.persist()

    # Raft can not step request snapshot if last raft log's term mismatch current term.
    with pytest.raises(RequestSnapshotDroppedError):
        sm.raft.request_snapshot()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    # Raft can not step request snapshot if itself is a leader.
    with pytest.raises(RequestSnapshotDroppedError):
        sm.raft.request_snapshot()

    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    m.set_index(11)
    sm.step(m)

    assert sm.raft.prs().get(2).get_state() == ProgressState.Replicate

    request_snapshot_idx = sm.raft_log.get_committed()

    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    m.set_index(11)
    m.set_reject(True)
    m.set_reject_hint(INVALID_INDEX)
    m.set_request_snapshot(request_snapshot_idx)

    # Ignore out of order request snapshot messages.
    out_of_order = m.clone()
    out_of_order.set_index(9)
    sm.step(out_of_order)
    assert sm.raft.prs().get(2).get_state() == ProgressState.Replicate

    # Request snapshot.
    sm.step(m)
    assert sm.raft.prs().get(2).get_state() == ProgressState.Snapshot
    assert sm.raft.prs().get(2).get_pending_snapshot() == 11
    assert sm.raft.prs().get(2).get_next_idx() == 12
    assert sm.raft.prs().get(2).is_paused()
    snap = sm.raft.get_msgs()[-1]
    assert snap.get_msg_type() == MessageType.MsgSnapshot
    assert snap.get_snapshot().get_metadata().get_index() == request_snapshot_idx

    # Append/heartbeats does not set the state from snapshot to probe.
    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    m.set_index(11)
    sm.step(m)
    assert sm.raft.prs().get(2).get_state() == ProgressState.Snapshot
    assert sm.raft.prs().get(2).get_pending_snapshot() == 11
    assert sm.raft.prs().get(2).get_next_idx() == 12
    assert sm.raft.prs().get(2).is_paused()

    # However snapshot status report does set the stat to probe.
    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    sm.step(m)
    assert sm.raft.prs().get(2).get_state() == ProgressState.Probe
    assert sm.raft.prs().get(2).get_pending_snapshot() == 0
    assert sm.raft.prs().get(2).get_next_idx() == 12
    assert sm.raft.prs().get(2).is_paused()
