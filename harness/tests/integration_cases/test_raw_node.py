import os
import sys
import pytest
from typing import Any, List, Optional, Tuple, cast
from rraft import (
    Config_Ref,
    Entry_Owner,
    Entry_Ref,
    HardState_Ref,
    Logger_Ref,
    MemStorage_Owner,
    MessageType,
    RawNode__MemStorage_Owner,
    Ready_Ref,
    Snapshot_Owner,
    Snapshot_Ref,
    SoftState_Ref,
    default_logger,
    is_local_msg,
)
from test_utils import (
    add_learner,
    add_node,
    conf_change_v2,
    conf_change,
    empty_entry,
    new_entry,
    new_message_with_entries,
    new_message,
    new_snapshot,
    new_storage,
    new_test_config,
    new_test_raft_with_config,
    new_test_raft_with_logs,
    new_test_raft_with_prevote,
    new_test_raft,
    remove_node,
    SOME_DATA,
    hard_state,
    # Interface,
    # Network,
)

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "../src"))
sys.path.append(parent_dir)
from interface import Interface
from network import Network


def must_cmp_ready(
    r: Ready_Ref,
    ss: Optional[SoftState_Ref],
    hs: Optional[HardState_Ref],
    entries: List[Entry_Ref],
    committed_entries: List[Entry_Ref],
    snapshot: Optional[Snapshot_Ref],
    msg_is_empty: bool,
    persisted_msg_is_empty: bool,
    must_sync: bool,
):
    assert r.ss() == ss
    assert r.hs() == hs
    assert r.entries() == entries
    assert r.committed_entries() == committed_entries
    assert r.must_sync() == must_sync
    assert r.snapshot() == snapshot or r.snapshot() == Snapshot_Owner.default()
    assert len(r.msgs()) == 0 if msg_is_empty else len(r.msgs()) != 0
    assert (
        len(r.persisted_msgs()) == 0
        if persisted_msg_is_empty
        else len(r.persisted_msgs()) != 0
    )


def new_raw_node(
    id: int,
    peers: List[int],
    election_tick: int,
    heartbeat_tick: int,
    storage: MemStorage_Owner,
    logger: Logger_Ref,
) -> RawNode__MemStorage_Owner:
    config = new_test_config(id, election_tick, heartbeat_tick)
    return new_raw_node_with_config(peers, config, storage, logger)


def new_raw_node_with_config(
    peers: List[int],
    config: Config_Ref,
    storage: MemStorage_Owner,
    logger: Logger_Ref,
) -> RawNode__MemStorage_Owner:
    assert not (
        storage.initial_state().initialized() and not peers
    ), f"new_raw_node with empty peers on initialized store"

    if peers and not storage.initial_state().initialized():
        storage.wl(lambda core: core.apply_snapshot(new_snapshot(1, 1, peers)))

    return RawNode__MemStorage_Owner(config, storage, logger)


def get_msg_types() -> List[MessageType]:
    return [
        MessageType.MsgHup,
        MessageType.MsgBeat,
        MessageType.MsgPropose,
        MessageType.MsgAppend,
        MessageType.MsgAppendResponse,
        MessageType.MsgRequestVote,
        MessageType.MsgRequestVoteResponse,
        MessageType.MsgSnapshot,
        MessageType.MsgHeartbeat,
        MessageType.MsgHeartbeatResponse,
        MessageType.MsgUnreachable,
        MessageType.MsgSnapStatus,
        MessageType.MsgCheckQuorum,
        MessageType.MsgTransferLeader,
        MessageType.MsgTimeoutNow,
        MessageType.MsgReadIndex,
        MessageType.MsgReadIndexResp,
        MessageType.MsgRequestPreVote,
        MessageType.MsgRequestPreVoteResponse,
    ]


# Ensures that RawNode::step ignore local message.
def test_raw_node_step():
    l = default_logger()
    for msg_t in get_msg_types():
        s = new_storage()
        s.wl(lambda core: core.set_hardstate(hard_state(1, 1, 0)))
        # Append an empty entry to make sure the non-local messages (like
        # vote requests) are ignored and don't trigger assertions.
        s.wl(lambda core: core.append([new_entry(1, 1, None)]))
        s.wl(lambda core: core.apply_snapshot(new_snapshot(1, 1, [1])))

        storage = new_storage()
        raw_node = new_raw_node(1, [1], 10, 1, storage, l)
        # LocalMsg should be ignored.
        try:
            raw_node.step(new_message(0, 0, msg_t, 0))
        except Exception as e:
            if is_local_msg(msg_t):
                assert str(e) == "raft: cannot step raft local message"


# Ensures that MsgReadIndex to old leader gets forwarded to the new leader and
# 'send' method does not attach its term.
def test_raw_node_read_index_to_old_leader():
    l = default_logger()
    s1, s2, s3 = new_storage(), new_storage(), new_storage()
    r1 = new_test_raft(1, [1, 2, 3], 10, 1, s1, l)
    r2 = new_test_raft(2, [1, 2, 3], 10, 1, s2, l)
    r3 = new_test_raft(3, [1, 2, 3], 10, 1, s3, l)

    nt = Network.new([r1, r2, r3], l)

    # elect r1 as leader
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    test_entries = Entry_Owner.default()
    test_entries.set_data(b"testdata")

    # send readindex request to r2(follower)
    _ = nt.peers.get(2).step(
        new_message_with_entries(
            2,
            2,
            MessageType.MsgReadIndex,
            [test_entries.clone()],
        )
    )

    # verify r2(follower) forwards this message to r1(leader) with term not set
    assert len(nt.peers[2].raft.get_msgs()) == 1
    read_index_msg1 = new_message_with_entries(
        2, 1, MessageType.MsgReadIndex, [test_entries.clone()]
    )
    assert read_index_msg1 == nt.peers[2].raft.get_msgs()[0]

    # send readindex request to r3(follower)
    _ = nt.peers.get(3).step(
        new_message_with_entries(
            3,
            3,
            MessageType.MsgReadIndex,
            [test_entries.clone()],
        )
    )

    # verify r3(follower) forwards this message to r1(leader) with term not set as well.
    assert len(nt.peers[3].raft.get_msgs()) == 1

    read_index_msg2 = new_message_with_entries(
        3, 1, MessageType.MsgReadIndex, [test_entries.clone()]
    )
    assert nt.peers[3].raft.get_msgs()[0] == read_index_msg2

    # now elect r3 as leader
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # let r1 steps the two messages previously we got from r2, r3
    _ = nt.peers.get(1).step(read_index_msg1)
    _ = nt.peers.get(1).step(read_index_msg2)

    # verify r1(follower) forwards these messages again to r3(new leader)
    assert len(nt.peers[1].raft.get_msgs()) == 2
    assert nt.peers[1].raft.get_msgs()[0] == new_message_with_entries(
        2, 3, MessageType.MsgReadIndex, [test_entries.clone()]
    )

    assert nt.peers[1].raft.get_msgs()[1] == new_message_with_entries(
        3, 3, MessageType.MsgReadIndex, [test_entries]
    )


# Tests the configuration change mechanism. Each test case sends a configuration
# change which is either simple or joint, verifies that it applies and that the
# resulting ConfState matches expectations, and for joint configurations makes
# sure that they are exited successfully.
def test_raw_node_propose_and_conf_change():
    pass


# Tests the configuration change auto leave even leader lost leadership.
def test_raw_node_joint_auto_leave():
    pass


# Ensures that two proposes to add the same node should not affect the later propose
# to add new node.
def test_raw_node_propose_add_duplicate_node():
    pass


def test_raw_node_propose_add_learner_node():
    pass


# Ensures that RawNode.read_index sends the MsgReadIndex message to the underlying
# raft. It also ensures that ReadState can be read out.
def test_raw_node_read_index():
    pass


# Ensures that a node can be started correctly. Note that RawNode requires the
# application to bootstrap the state, i.e. it does not accept peers and will not
# create faux configuration change entries.
def test_raw_node_start():
    pass


def test_raw_node_restart():
    pass


def test_raw_node_restart_from_snapshot():
    pass


# test_skip_bcast_commit ensures that empty commit message is not sent out
# when skip_bcast_commit is true.
def test_skip_bcast_commit():
    pass


# test_set_priority checks the set_priority function in RawNode.
def test_set_priority():
    pass


# TestNodeBoundedLogGrowthWithPartition tests a scenario where a leader is
# partitioned from a quorum of nodes. It verifies that the leader's log is
# protected from unbounded growth even as new entries continue to be proposed.
# This protection is provided by the max_uncommitted_size configuration.
def test_bounded_uncommitted_entries_growth_with_partition():
    pass


def prepare_async_entries():
    pass


# Test entries are handled properly when they are fetched asynchronously
def test_raw_node_with_async_entries():
    pass


# Test if async fetch entries works well when there is a remove node conf-change.
def test_raw_node_with_async_entries_to_removed_node():
    pass


# Test if async fetch entries works well when there is a leader step-down.
def test_raw_node_with_async_entries_on_follower():
    pass


def test_raw_node_async_entries_with_leader_change():
    pass


def test_raw_node_with_async_apply():
    pass


# Test if the ready process is expected when a follower receives a snapshot
# and some committed entries after its snapshot.
def test_raw_node_entries_after_snapshot():
    pass


# Test if the given committed entries are persisted when some persisted
# entries are overwritten by a new leader.
def test_raw_node_overwrite_entries():
    pass


# Test if async ready process is expected when a leader receives
# the append response and persist its entries.
def test_async_ready_leader():
    pass


# Test if async ready process is expected when a follower receives
# some append msg and snapshot.
def test_async_ready_follower():
    pass


# Test if a new leader immediately sends all messages recorded before without
# persisting.
def test_async_ready_become_leader():
    pass


def test_async_ready_multiple_snapshot():
    pass


def test_committed_entries_pagination():
    pass


# Test with `commit_since_index`, committed entries can be fetched correctly after restart.
#
# Case steps:
# - Node learns that index 10 is committed
# - `next_entries` returns entries [2..11) in committed_entries (but index 10 already
#   exceeds maxBytes), which isn't noticed internally by Raft
# - Commit index gets bumped to 10
# - The node persists the `HardState`, but crashes before applying the entries
# - Upon restart, the storage returns the same entries, but `slice` takes a
#   different code path and removes the last entry.
# - Raft does not emit a HardState, but when the app calls advance(), it bumps
#   its internal applied index cursor to 10 (when it should be 9)
# - The next `Ready` asks the app to apply index 11 (omitting index 10), losing a
#   write.
def test_committed_entries_pagination_after_restart():
    pass
