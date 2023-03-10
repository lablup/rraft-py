import os
import sys
import warnings
import pytest
from typing import Dict, List

from rraft import (
    MessageType,
    Snapshot_Owner,
    default_logger,
)

from test_utils import (
    new_snapshot,
    new_storage,
    new_test_raft,
    new_message,
    new_test_raft_with_prevote,
    # Interface,
)

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "../src"))
sys.path.append(parent_dir)

from interface import Interface
from network import Network


def testing_snap() -> Snapshot_Owner:
    warnings.filterwarnings("ignore")
    return new_snapshot(11, 11, [1, 2])


def test_sending_snapshot_set_pending_snapshot():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage.make_ref(), l.make_ref())
    sm.raft.make_ref().restore(testing_snap())
    sm.persist()

    sm.raft.make_ref().become_candidate()
    sm.raft.make_ref().become_leader()

    # force set the next of node 1, so that
    # node 1 needs a snapshot
    assert sm.raft.make_ref().prs().get(2).get_next_idx() == sm.raft_log.first_index()

    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    voter_2 = sm.raft.make_ref().prs().get(2)
    m.make_ref().set_index(voter_2.get_next_idx() - 1)
    m.make_ref().set_reject(True)

    sm.step(m)
    assert sm.raft.make_ref().prs().get(2).get_pending_snapshot() == 11


def test_pending_snapshot_pause_replication():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage.make_ref(), l.make_ref())
    sm.raft.make_ref().restore(testing_snap())
    sm.persist()

    sm.raft.make_ref().become_candidate()
    sm.raft.make_ref().become_leader()
    sm.raft.make_ref().prs().get(2).become_snapshot(11)

    sm.step(new_message(2, 1, MessageType.MsgPropose, 1))
    msgs = sm.read_messages()
    assert not msgs


def test_snapshot_failure():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage.make_ref(), l.make_ref())
    sm.raft.make_ref().restore(testing_snap())
    sm.persist()

    sm.raft.make_ref().become_candidate()
    sm.raft.make_ref().become_leader()

    sm.raft.make_ref().prs().get(2).set_next_idx(1)
    sm.raft.make_ref().prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.make_ref().set_reject(True)
    sm.step(m)
    voter_2 = sm.raft.make_ref().prs().get(2)

    assert voter_2.get_pending_snapshot() == 0
    assert voter_2.get_next_idx() == 1
    assert voter_2.get_paused()


def test_snapshot_succeed():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage.make_ref(), l.make_ref())
    sm.raft.make_ref().restore(testing_snap())
    sm.persist()

    sm.raft.make_ref().become_candidate()
    sm.raft.make_ref().become_leader()

    sm.raft.make_ref().prs().get(2).set_next_idx(1)
    sm.raft.make_ref().prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.make_ref().set_reject(False)
    sm.step(m)
    voter_2 = sm.raft.make_ref().prs().get(2)
    assert voter_2.get_pending_snapshot() == 0
    assert voter_2.get_next_idx() == 12
    assert voter_2.get_paused()


def test_snapshot_abort():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage.make_ref(), l.make_ref())
    sm.raft.make_ref().restore(testing_snap())
    sm.persist()

    sm.raft.make_ref().become_candidate()
    sm.raft.make_ref().become_leader()

    sm.raft.make_ref().prs().get(2).set_next_idx(1)
    sm.raft.make_ref().prs().get(2).become_snapshot(11)

    m = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    m.make_ref().set_reject(False)
    sm.step(m)

    assert sm.raft.make_ref().prs().get(2).get_pending_snapshot() == 0
    assert sm.raft.make_ref().prs().get(2).get_next_idx() == 12


# Initialized storage should be at term 1 instead of 0. Otherwise the case will fail.
def test_snapshot_with_min_term():
    l = default_logger()

    def do_test(pre_vote: bool):
        s1 = new_storage()
        s1.make_ref().wl(lambda core: core.apply_snapshot(new_snapshot(1, 1, [1, 2])))

        n1 = new_test_raft_with_prevote(
            1, [1, 2], 10, 1, s1.make_ref(), pre_vote, l.make_ref()
        )

        s2 = new_storage()
        n2 = new_test_raft_with_prevote(
            2, [], 10, 1, s2.make_ref(), pre_vote, l.make_ref()
        )

        nt = Network.new([n1, n2], l.make_ref())
        m = new_message(1, 1, MessageType.MsgHup, 0)
        nt.send([m])

        # 1 will be elected as leader, and then send a snapshot and an empty entry to 2.
        assert nt.peers.get(2).raft_log.first_index() == 2
        assert nt.peers.get(2).raft_log.last_index() == 2

    do_test(True)
    do_test(False)


def test_request_snapshot():
    pass
