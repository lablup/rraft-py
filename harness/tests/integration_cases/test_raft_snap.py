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
    pass


def test_snapshot_succeed():
    pass


def test_snapshot_abort():
    pass


# Initialized storage should be at term 1 instead of 0. Otherwise the case will fail.
def test_snapshot_with_min_term():
    pass


def test_request_snapshot():
    pass
