import os
import sys
import pytest
from typing import Any, List, Optional, Tuple, cast
from rraft import (
    NO_LIMIT,
    ConfChange_Owner,
    ConfChangeTransition,
    ConfChangeType,
    ConfChangeV2_Owner,
    ConfState_Owner,
    Config_Ref,
    Entry_Owner,
    Entry_Ref,
    EntryType,
    HardState_Ref,
    Logger_Ref,
    MemStorage_Owner,
    MessageType,
    RawNode__MemStorage_Owner,
    RawNode__MemStorage_Ref,
    ReadState_Owner,
    Ready_Ref,
    Snapshot_Owner,
    Snapshot_Ref,
    SoftState_Ref,
    StateRole,
    default_logger,
    new_conf_change_single,
    is_local_msg,
)
from test_utils import (
    add_learner,
    add_node,
    conf_change_v2,
    conf_change,
    conf_state,
    conf_state_v2,
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
    soft_state,
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
    assert len(r.messages()) == 0 if msg_is_empty else len(r.messages()) != 0
    assert (
        len(r.persisted_messages()) == 0
        if persisted_msg_is_empty
        else len(r.persisted_messages()) != 0
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
    l = default_logger()

    class Test:
        def __init__(
            self,
            cc: ConfChange_Owner | ConfChangeV2_Owner,
            exp: ConfState_Owner,
            exp2: Optional[ConfState_Owner],
        ) -> None:
            self.cc = cc
            self.exp = exp
            self.exp2 = exp2

    test_cases = [
        # V1 config change.b
        Test(
            conf_change(ConfChangeType.AddNode, 2),
            conf_state([1, 2], []),
            None,
        ),
    ]

    # Proposing the same as a V2 change works just the same, without entering
    # a joint config.
    single = new_conf_change_single(2, ConfChangeType.AddNode)
    test_cases.append(
        Test(
            conf_change_v2([single]),
            conf_state([1, 2], []),
            None,
        )
    )

    # Ditto if we add it as a learner instead.
    single = new_conf_change_single(2, ConfChangeType.AddLearnerNode)
    test_cases.append(
        Test(
            conf_change_v2([single]),
            conf_state([1], [2]),
            None,
        )
    )

    # We can ask explicitly for joint consensus if we want it.
    single = new_conf_change_single(2, ConfChangeType.AddLearnerNode)
    cc = conf_change_v2([single])
    cc.set_transition(ConfChangeTransition.Explicit)
    cs = conf_state_v2([1], [2], [1], [], False)
    test_cases.append(Test(cc, cs, conf_state([1], [2])))

    # Ditto, but with implicit transition (the harness checks this).
    single = new_conf_change_single(2, ConfChangeType.AddLearnerNode)
    cc = conf_change_v2([single])
    cc.set_transition(ConfChangeTransition.Implicit)
    cs = conf_state_v2([1], [2], [1], [], True)
    test_cases.append(Test(cc, cs, conf_state([1], [2])))

    # Add a new node and demote n1. This exercises the interesting case in
    # which we really need joint config changes and also need LearnersNext.
    cc = conf_change_v2(
        [
            new_conf_change_single(2, ConfChangeType.AddNode),
            new_conf_change_single(1, ConfChangeType.AddLearnerNode),
            new_conf_change_single(3, ConfChangeType.AddLearnerNode),
        ]
    )
    cs = conf_state_v2([2], [3], [1], [1], True)
    test_cases.append(Test(cc, cs, conf_state([2], [1, 3])))

    # Ditto explicit.
    cc = conf_change_v2(
        [
            new_conf_change_single(2, ConfChangeType.AddNode),
            new_conf_change_single(1, ConfChangeType.AddLearnerNode),
            new_conf_change_single(3, ConfChangeType.AddLearnerNode),
        ]
    )
    cc.set_transition(ConfChangeTransition.Explicit)
    cs = conf_state_v2([2], [3], [1], [1], False)
    test_cases.append(Test(cc, cs, conf_state([2], [1, 3])))

    # Ditto implicit.
    cc = conf_change_v2(
        [
            new_conf_change_single(2, ConfChangeType.AddNode),
            new_conf_change_single(1, ConfChangeType.AddLearnerNode),
            new_conf_change_single(3, ConfChangeType.AddLearnerNode),
        ]
    )
    cc.set_transition(ConfChangeTransition.Implicit)
    cs = conf_state_v2([2], [3], [1], [1], True)
    test_cases.append(Test(cc, cs, conf_state([2], [1, 3])))

    for v in test_cases:
        cc, exp, exp2 = v.cc, v.exp, v.exp2
        s = new_storage()

        raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
        raw_node.campaign()
        proposed = False
        ccdata = []
        # Propose the ConfChange, wait until it applies, save the resulting ConfState.
        cs: Optional[ConfState_Owner] = None

        while not cs:
            rd = raw_node.ready()
            s.wl(lambda core: core.append(rd.entries()))

            def handle_committed_entries(
                rn: RawNode__MemStorage_Ref, committed_entries: List[Entry_Owner]
            ):
                for e in committed_entries:
                    nonlocal cs

                    if e.get_entry_type() == EntryType.EntryConfChange:
                        cc = ConfChange_Owner.default()
                        cc.merge_from_bytes(e.get_data())
                        cs = rn.apply_conf_change(cc)
                    elif e.get_entry_type() == EntryType.EntryConfChangeV2:
                        cc = ConfChangeV2_Owner.default()
                        cc.merge_from_bytes(e.get_data())
                        cs = rn.apply_conf_change_v2(cc)

            handle_committed_entries(raw_node.make_ref(), rd.take_committed_entries())

            is_leader = False

            if ss := rd.ss():
                is_leader = ss.get_leader_id() == raw_node.get_raft().get_id()

            light_rd = raw_node.advance(rd.make_ref())
            handle_committed_entries(
                raw_node.make_ref(), light_rd.take_committed_entries()
            )
            raw_node.advance_apply()

            # Once we are the leader, propose a command and a ConfChange.
            if not proposed and is_leader:
                raw_node.propose([], b"somedata")

                if v1 := cc.as_v1():
                    ccdata = v1.write_to_bytes()
                    raw_node.propose_conf_change([], v1.clone())
                else:
                    v2 = cc.as_v2()
                    ccdata = v2.write_to_bytes()
                    raw_node.propose_conf_change_v2([], v2)

                proposed = True

        # Check that the last index is exactly the conf change we put in,
        # down to the bits. Note that this comes from the Storage, which
        # will not reflect any unstable entries that we'll only be presented
        # with in the next Ready.
        last_index = s.last_index()
        entries = s.entries(last_index - 1, last_index + 1, NO_LIMIT)
        assert len(entries) == 2
        assert entries[0].get_data() == b"somedata"

        if cc.as_v1():
            assert entries[1].get_entry_type() == EntryType.EntryConfChange
        else:
            assert entries[1].get_entry_type() == EntryType.EntryConfChangeV2

        assert ccdata == entries[1].get_data()
        assert cs == exp

        conf_index = last_index
        if cc.as_v2().enter_joint():
            # If this is an auto-leaving joint conf change, it will have
            # appended the entry that auto-leaves, so add one to the last
            # index that forms the basis of our expectations on
            # pendingConfIndex. (Recall that lastIndex was taken from stable
            # storage, but this auto-leaving entry isn't on stable storage
            # yet).
            conf_index += 1

        assert conf_index == raw_node.get_raft().get_pending_conf_index()

        # Move the RawNode along. If the ConfChange was simple, nothing else
        # should happen. Otherwise, we're in a joint state, which is either
        # left automatically or not. If not, we add the proposal that leaves
        # it manually.
        rd = raw_node.ready()
        context = []
        if not exp.get_auto_leave():
            assert not rd.entries()
            if not exp2:
                continue

            context = list(b"manual")
            cc = conf_change_v2([])
            cc.set_context(context)
            raw_node.propose_conf_change_v2([], cc)
            rd = raw_node.ready()

        # Check that the right ConfChange comes out.
        assert len(rd.entries()) == 1
        assert rd.entries()[0].get_entry_type() == EntryType.EntryConfChangeV2
        leave_cc = ConfChangeV2_Owner.default()
        leave_cc.merge_from_bytes(rd.entries()[0].get_data())

        assert context == list(leave_cc.get_context()), f"{cc.as_v2()}"
        # Lie and pretend the ConfChange applied. It won't do so because now
        # we require the joint quorum and we're only running one node.
        cs = raw_node.apply_conf_change_v2(leave_cc)
        assert cs == exp2


# Tests the configuration change auto leave even leader lost leadership.
def test_raw_node_joint_auto_leave():
    l = default_logger()

    single = new_conf_change_single(2, ConfChangeType.AddLearnerNode)
    test_cc = conf_change_v2([single])
    test_cc.set_transition(ConfChangeTransition.Implicit)
    exp_cs = conf_state_v2([1], [2], [1], [], True)
    exp_cs2 = conf_state([1], [2])

    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    raw_node.campaign()
    proposed = False
    ccdata = test_cc.write_to_bytes()
    # Propose the ConfChange, wait until it applies, save the resulting ConfState.
    cs = None
    while not cs:
        rd = raw_node.ready()
        s.wl(lambda core: core.append(rd.entries()))

        def handle_committed_entries(
            rn: RawNode__MemStorage_Ref, committed_entries: List[Entry_Owner]
        ):
            for e in committed_entries:
                nonlocal cs
                if e.get_entry_type() == EntryType.EntryConfChangeV2:
                    cc = ConfChangeV2_Owner.default()
                    cc.merge_from_bytes(e.get_data())

                    # Force it step down.
                    msg = new_message(1, 1, MessageType.MsgHeartbeatResponse, 0)
                    msg.set_term(rn.get_raft().get_term() + 1)
                    rn.step(msg)

                    cs = rn.apply_conf_change_v2(cc)

        handle_committed_entries(raw_node.make_ref(), rd.take_committed_entries())
        is_leader = False

        if ss := rd.ss():
            is_leader = ss.get_leader_id() == raw_node.get_raft().get_id()

        light_rd = raw_node.advance(rd.make_ref())
        handle_committed_entries(raw_node.make_ref(), light_rd.take_committed_entries())
        raw_node.advance_apply()

        # Once we are the leader, propose a command and a ConfChange.
        if not proposed and is_leader:
            raw_node.propose([], b"somedata")
            raw_node.propose_conf_change_v2([], test_cc.clone())

            proposed = True

    # Check that the last index is exactly the conf change we put in,
    # down to the bits. Note that this comes from the Storage, which
    # will not reflect any unstable entries that we'll only be presented
    # with in the next Ready.
    last_index = s.last_index()
    entries = s.entries(last_index - 1, last_index + 1, NO_LIMIT)
    assert len(entries) == 2
    assert entries[0].get_data() == b"somedata"
    assert entries[1].get_entry_type() == EntryType.EntryConfChangeV2
    assert ccdata == entries[1].get_data()
    assert exp_cs == cs
    assert raw_node.get_raft().get_pending_conf_index() == 0

    # Move the RawNode along. It should not leave joint because it's follower.
    rd = raw_node.ready()
    assert not rd.entries()
    _ = raw_node.advance(rd.make_ref())

    # Make it leader again. It should leave joint automatically after moving apply index.
    raw_node.campaign()
    rd = raw_node.ready()
    s.wl(lambda core: core.append(rd.entries()))
    _ = raw_node.advance(rd.make_ref())

    rd = raw_node.ready()
    s.wl(lambda core: core.append(rd.entries()))

    # Check that the right ConfChange comes out.
    assert len(rd.entries()) == 1
    assert rd.entries()[0].get_entry_type() == EntryType.EntryConfChangeV2
    leave_cc = ConfChangeV2_Owner.default()
    leave_cc.merge_from_bytes(rd.entries()[0].get_data())

    assert not leave_cc.get_context()

    # Lie and pretend the ConfChange applied. It won't do so because now
    # we require the joint quorum and we're only running one node.
    cs = raw_node.apply_conf_change_v2(leave_cc)
    assert cs == exp_cs2


# Ensures that two proposes to add the same node should not affect the later propose
# to add new node.
def test_raw_node_propose_add_duplicate_node():
    l = default_logger()
    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    raw_node.campaign()

    while True:
        rd = raw_node.ready()
        s.wl(lambda core: core.append(rd.entries()))

        if ss := rd.ss():
            if ss.get_leader_id() == raw_node.get_raft().get_id():
                raw_node.advance(rd.make_ref())
                break
        raw_node.advance(rd.make_ref())

    def propose_conf_change_and_apply(cc: ConfChange_Owner):
        raw_node.propose_conf_change([], cc)
        rd = raw_node.ready()
        s.wl(lambda core: core.append(rd.entries()))

        def handle_committed_entries(
            rn: RawNode__MemStorage_Ref, committed_entries: List[Entry_Owner]
        ):
            for e in committed_entries:
                if e.get_entry_type() == EntryType.EntryConfChange:
                    conf_change = ConfChange_Owner.default()
                    conf_change.merge_from_bytes(e.get_data())
                    rn.apply_conf_change(conf_change)

        handle_committed_entries(raw_node, rd.take_committed_entries())

        light_rd = raw_node.advance(rd.make_ref())
        handle_committed_entries(raw_node, light_rd.take_committed_entries())
        raw_node.advance_apply()

    cc1 = conf_change(ConfChangeType.AddNode, 1)
    ccdata1 = cc1.write_to_bytes()
    propose_conf_change_and_apply(cc1.clone())

    # try to add the same node again
    propose_conf_change_and_apply(cc1)

    # the new node join should be ok
    cc2 = conf_change(ConfChangeType.AddNode, 2)
    ccdata2 = cc2.write_to_bytes()
    propose_conf_change_and_apply(cc2)

    last_index = s.last_index()

    # the last three entries should be: ConfChange cc1, cc1, cc2
    entries = s.entries(last_index - 2, last_index + 1, None)
    assert len(entries) == 3
    assert entries[0].get_data() == ccdata1
    assert entries[2].get_data() == ccdata2


def test_raw_node_propose_add_learner_node():
    l = default_logger()
    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    rd = raw_node.ready()
    must_cmp_ready(rd.make_ref(), None, None, [], [], None, True, True, False)
    _ = raw_node.advance(rd.make_ref())

    raw_node.campaign()

    while True:
        rd = raw_node.ready()
        if ss := rd.ss():
            if ss.get_leader_id() == raw_node.get_raft().get_id():
                raw_node.advance(rd.make_ref())
                break

    # propose add learner node and check apply state
    cc = conf_change(ConfChangeType.AddLearnerNode, 2)
    raw_node.propose_conf_change([], cc)

    rd = raw_node.ready()
    s.wl(lambda core: core.append(rd.entries()))

    light_rd = raw_node.advance(rd.make_ref())

    assert (
        len(light_rd.committed_entries()) == 1
    ), f"should committed the conf change entry"

    e = light_rd.committed_entries()[0]
    assert e.get_entry_type() == EntryType.EntryConfChange
    conf_change_ = ConfChange_Owner.default()
    conf_change_.merge_from_bytes(e.get_data())
    conf_state = raw_node.apply_conf_change(conf_change_)
    assert conf_state.get_voters() == [1]
    assert conf_state.get_learners() == [2]


# Ensures that RawNode.read_index sends the MsgReadIndex message to the underlying
# raft. It also ensures that ReadState can be read out.
def test_raw_node_read_index():
    l = default_logger()
    wrequest_ctx = list(b"somedata")
    wrs = [ReadState_Owner.default()]
    wrs[0].set_index(2)
    wrs[0].set_request_ctx(wrequest_ctx)

    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    raw_node.campaign()
    while True:
        rd = raw_node.ready()
        s.wl(lambda core: core.append(rd.entries()))

        if ss := rd.ss():
            if ss.get_leader_id() == raw_node.get_raft().get_id():
                raw_node.advance(rd.make_ref())

                # Once we are the leader, issue a read index request
                raw_node.read_index(wrequest_ctx)
                break

        raw_node.advance(rd.make_ref())

    # ensure the read_states can be read out
    assert raw_node.get_raft().get_read_states()
    assert raw_node.has_ready()
    rd = raw_node.ready()
    assert rd.read_states() == wrs
    s.wl(lambda core: core.append(rd.entries()))
    raw_node.advance(rd.make_ref())

    # ensure raft.read_states is reset after advance
    assert not raw_node.has_ready()
    assert not raw_node.get_raft().get_read_states()


# Ensures that a node can be started correctly. Note that RawNode requires the
# application to bootstrap the state, i.e. it does not accept peers and will not
# create faux configuration change entries.
def test_raw_node_start():
    l = default_logger()
    store = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, store.clone(), l)

    rd = raw_node.ready()
    must_cmp_ready(rd, None, None, [], [], None, True, True, False)
    _ = raw_node.advance(rd.make_ref())

    raw_node.campaign()
    rd = raw_node.ready()
    ss = soft_state(1, StateRole.Leader)

    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(2, 1, 1),
        [new_entry(2, 2, None)],
        [],
        None,
        True,
        True,
        True,
    )
    store.wl(lambda core: core.append(rd.entries()))

    light_rd = raw_node.advance(rd.make_ref())
    assert light_rd.commit_index() == 2
    assert light_rd.committed_entries() == [new_entry(2, 2, None)]
    assert not raw_node.has_ready()

    raw_node.propose([], list(b"somedata"))
    rd = raw_node.ready()
    must_cmp_ready(
        rd.make_ref(),
        None,
        None,
        [new_entry(2, 3, SOME_DATA)],
        [],
        None,
        True,
        True,
        True,
    )
    store.wl(lambda core: core.append(rd.entries()))
    light_rd = raw_node.advance(rd.make_ref())
    assert light_rd.commit_index() == 3
    assert light_rd.committed_entries() == [new_entry(2, 3, SOME_DATA)]

    assert not raw_node.has_ready()


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
