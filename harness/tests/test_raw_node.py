import random
import pytest
from typing import List, Optional
from harness.src.network import Network
from rraft import (
    NO_LIMIT,
    ConfChange,
    ConfChangeTransition,
    ConfChangeType,
    ConfChangeV2,
    ConfState,
    Config,
    ConfigRef,
    Entry,
    EntryRef,
    EntryType,
    GetEntriesContext,
    HardStateRef,
    LoggerRef,
    MemStorage,
    Message,
    MessageType,
    InMemoryRawNode,
    InMemoryRawNodeRef,
    ProposalDroppedError,
    ReadState,
    ReadyRef,
    Snapshot,
    SnapshotRef,
    SoftStateRef,
    StateRole,
    default_logger,
    new_conf_change_single,
    is_local_msg,
)
from harness.utils import (
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
    new_test_raft,
    SOME_DATA,
    hard_state,
    remove_node,
    soft_state,
)


MAX_UINT64 = (1 << 64) - 1


def must_cmp_ready(
    r: ReadyRef,
    ss: Optional[SoftStateRef],
    hs: Optional[HardStateRef],
    entries: List[EntryRef],
    committed_entries: List[EntryRef],
    snapshot: Optional[SnapshotRef],
    msg_is_empty: bool,
    persisted_msg_is_empty: bool,
    must_sync: bool,
):
    assert r.ss() == ss
    assert r.hs() == hs
    assert r.entries() == entries
    assert r.committed_entries() == committed_entries
    assert r.must_sync() == must_sync
    assert r.snapshot() == snapshot or r.snapshot() == Snapshot.default()
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
    storage: MemStorage,
    logger: LoggerRef,
) -> InMemoryRawNode:
    config = new_test_config(id, election_tick, heartbeat_tick)
    return new_raw_node_with_config(peers, config, storage, logger)


def new_raw_node_with_config(
    peers: List[int],
    config: ConfigRef,
    storage: MemStorage,
    logger: LoggerRef,
) -> InMemoryRawNode:
    initial_state = storage.initial_state()
    assert not (
        initial_state.initialized() and not peers
    ), f"new_raw_node with empty peers on initialized store"

    if peers and not initial_state.initialized():
        storage.wl().apply_snapshot(new_snapshot(1, 1, peers))

    return InMemoryRawNode(config, storage, logger)


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
        s.wl().set_hardstate(hard_state(1, 1, 0))
        # Append an empty entry to make sure the non-local messages (like
        # vote requests) are ignored and don't trigger assertions.
        s.wl().append([new_entry(1, 1, None)])
        s.wl().apply_snapshot(new_snapshot(1, 1, [1]))

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

    test_entries = Entry.default()
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
    nt.peers.get(1).step(read_index_msg1)
    nt.peers.get(1).step(read_index_msg2)

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
            cc: ConfChange | ConfChangeV2,
            exp: ConfState,
            exp2: Optional[ConfState],
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
        cs: Optional[ConfState] = None

        while not cs:
            rd = raw_node.ready()
            s.wl().append(rd.entries())

            def handle_committed_entries(
                rn: InMemoryRawNodeRef, committed_entries: List[Entry]
            ):
                for e in committed_entries:
                    nonlocal cs

                    if e.get_entry_type() == EntryType.EntryConfChange:
                        cc = ConfChange.default()
                        cc.merge_from_bytes(e.get_data())
                        cs = rn.apply_conf_change(cc)
                    elif e.get_entry_type() == EntryType.EntryConfChangeV2:
                        cc = ConfChangeV2.default()
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
                    ccdata = v1.encode()
                    raw_node.propose_conf_change([], v1.clone())
                else:
                    v2 = cc.as_v2()
                    ccdata = v2.encode()
                    raw_node.propose_conf_change_v2([], v2)

                proposed = True

        # Check that the last index is exactly the conf change we put in,
        # down to the bits. Note that this comes from the Storage, which
        # will not reflect any unstable entries that we'll only be presented
        # with in the next Ready.
        last_index = s.last_index()
        ctx = GetEntriesContext.empty(False)
        entries = s.entries(last_index - 1, last_index + 1, ctx.make_ref(), NO_LIMIT)
        assert len(entries) == 2
        assert entries[0].get_data() == b"somedata"

        if cc.as_v1():
            assert entries[1].get_entry_type() == EntryType.EntryConfChange
        else:
            assert entries[1].get_entry_type() == EntryType.EntryConfChangeV2

        assert ccdata == entries[1].get_data()
        assert cs == exp

        conf_index = last_index
        v2 = cc.as_v2()
        if v2.enter_joint():
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
        leave_cc = ConfChangeV2.default()
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
    ccdata = test_cc.encode()
    # Propose the ConfChange, wait until it applies, save the resulting ConfState.
    cs = None
    while not cs:
        rd = raw_node.ready()
        s.wl().append(rd.entries())

        def handle_committed_entries(
            rn: InMemoryRawNodeRef, committed_entries: List[Entry]
        ):
            for e in committed_entries:
                nonlocal cs
                if e.get_entry_type() == EntryType.EntryConfChangeV2:
                    cc = ConfChangeV2.default()
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
    ctx = GetEntriesContext.empty(False)
    entries = s.entries(last_index - 1, last_index + 1, ctx.make_ref(), NO_LIMIT)
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
    s.wl().append(rd.entries())
    _ = raw_node.advance(rd.make_ref())

    rd = raw_node.ready()
    s.wl().append(rd.entries())

    # Check that the right ConfChange comes out.
    assert len(rd.entries()) == 1
    assert rd.entries()[0].get_entry_type() == EntryType.EntryConfChangeV2
    leave_cc = ConfChangeV2.default()
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
        s.wl().append(rd.entries())

        if ss := rd.ss():
            if ss.get_leader_id() == raw_node.get_raft().get_id():
                raw_node.advance(rd.make_ref())
                break
        raw_node.advance(rd.make_ref())

    def propose_conf_change_and_apply(cc: ConfChange):
        raw_node.propose_conf_change([], cc)
        rd = raw_node.ready()
        s.wl().append(rd.entries())

        def handle_committed_entries(
            rn: InMemoryRawNodeRef, committed_entries: List[Entry]
        ):
            for e in committed_entries:
                if e.get_entry_type() == EntryType.EntryConfChange:
                    conf_change = ConfChange.default()
                    conf_change.merge_from_bytes(e.get_data())
                    rn.apply_conf_change(conf_change)

        handle_committed_entries(raw_node, rd.take_committed_entries())

        light_rd = raw_node.advance(rd.make_ref())
        handle_committed_entries(raw_node, light_rd.take_committed_entries())
        raw_node.advance_apply()

    cc1 = conf_change(ConfChangeType.AddNode, 1)
    ccdata1 = cc1.encode()
    propose_conf_change_and_apply(cc1.clone())

    # try to add the same node again
    propose_conf_change_and_apply(cc1)

    # the new node join should be ok
    cc2 = conf_change(ConfChangeType.AddNode, 2)
    ccdata2 = cc2.encode()
    propose_conf_change_and_apply(cc2)

    last_index = s.last_index()

    # the last three entries should be: ConfChange cc1, cc1, cc2
    ctx = GetEntriesContext.empty(False)
    entries = s.entries(last_index - 2, last_index + 1, ctx.make_ref(), None)
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
    s.wl().append(rd.entries())

    light_rd = raw_node.advance(rd.make_ref())

    assert (
        len(light_rd.committed_entries()) == 1
    ), f"should committed the conf change entry"

    e = light_rd.committed_entries()[0]
    assert e.get_entry_type() == EntryType.EntryConfChange
    conf_change_ = ConfChange.default()
    conf_change_.merge_from_bytes(e.get_data())
    conf_state = raw_node.apply_conf_change(conf_change_)
    assert conf_state.get_voters() == [1]
    assert conf_state.get_learners() == [2]


# Ensures that RawNode.read_index sends the MsgReadIndex message to the underlying
# raft. It also ensures that ReadState can be read out.
def test_raw_node_read_index():
    l = default_logger()
    wrequest_ctx = list(b"somedata")
    wrs = [ReadState.default()]
    wrs[0].set_index(2)
    wrs[0].set_request_ctx(wrequest_ctx)

    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    raw_node.campaign()
    while True:
        rd = raw_node.ready()
        s.wl().append(rd.entries())

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
    s.wl().append(rd.entries())
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
    store.wl().append(rd.entries())

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
    store.wl().append(rd.entries())
    light_rd = raw_node.advance(rd.make_ref())
    assert light_rd.commit_index() == 3
    assert light_rd.committed_entries() == [new_entry(2, 3, SOME_DATA)]

    assert not raw_node.has_ready()


def test_raw_node_restart():
    l = default_logger()
    entries = [empty_entry(1, 1), new_entry(1, 2, "foo")]

    store = new_storage()
    store.wl().set_hardstate(hard_state(1, 1, 0))
    store.wl().append(entries)
    raw_node = new_raw_node(1, [], 10, 1, store, l)

    rd = raw_node.ready()
    must_cmp_ready(
        rd,
        None,
        None,
        [],
        entries[:1],
        None,
        True,
        True,
        False,
    )
    raw_node.advance(rd.make_ref())
    assert not raw_node.has_ready()


def test_raw_node_restart_from_snapshot():
    l = default_logger()
    snap = new_snapshot(2, 1, [1, 2])
    entries = [new_entry(1, 3, "foo")]

    store = new_storage()
    store.wl().apply_snapshot(snap)
    store.wl().append(entries)
    store.wl().set_hardstate(hard_state(1, 3, 0))
    raw_node = InMemoryRawNode(new_test_config(1, 10, 1), store, l)

    rd = raw_node.ready()
    must_cmp_ready(rd.make_ref(), None, None, [], entries, None, True, True, False)
    raw_node.advance(rd.make_ref())
    assert not raw_node.has_ready()


# test_skip_bcast_commit ensures that empty commit message is not sent out
# when skip_bcast_commit is true.
def test_skip_bcast_commit():
    l = default_logger()
    config = new_test_config(1, 10, 1)
    config.set_skip_bcast_commit(True)
    s1 = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
    r1 = new_test_raft_with_config(config, s1, l)
    s2 = new_storage()
    r2 = new_test_raft(2, [1, 2, 3], 10, 1, s2, l)
    s3 = new_storage()
    r3 = new_test_raft(3, [1, 2, 3], 10, 1, s3, l)
    nt = Network.new([r1, r2, r3], l)

    # elect r1 as leader
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # Without bcast commit, followers will not update its commit index immediately.
    test_entries = Entry.default()
    test_entries.set_data(b"testdata")
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.send([msg.clone()])

    assert nt.peers[1].raft_log.get_committed() == 2
    assert nt.peers[2].raft_log.get_committed() == 1
    assert nt.peers[3].raft_log.get_committed() == 1

    # After bcast heartbeat, followers will be informed the actual commit index.
    for _ in range(0, nt.peers[1].raft.randomized_election_timeout()):
        nt.peers.get(1).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers[2].raft_log.get_committed() == 2
    assert nt.peers[3].raft_log.get_committed() == 2

    # The feature should be able to be adjusted at run time.
    nt.peers.get(1).raft.skip_bcast_commit(False)
    nt.send([msg.clone()])
    assert nt.peers[1].raft_log.get_committed() == 3
    assert nt.peers[2].raft_log.get_committed() == 3
    assert nt.peers[3].raft_log.get_committed() == 3

    nt.peers.get(1).raft.skip_bcast_commit(True)

    # Later proposal should commit former proposal.
    nt.send([msg.clone()])
    nt.send([msg])
    assert nt.peers[1].raft_log.get_committed() == 5
    assert nt.peers[2].raft_log.get_committed() == 4
    assert nt.peers[3].raft_log.get_committed() == 4

    # When committing conf change, leader should always bcast commit.
    cc = ConfChange.default()
    cc.set_change_type(ConfChangeType.RemoveNode)
    cc.set_node_id(3)
    data = cc.encode()
    cc_entry = Entry.default()
    cc_entry.set_entry_type(EntryType.EntryConfChange)
    cc_entry.set_data(data)
    nt.send(
        [
            new_message_with_entries(
                1,
                1,
                MessageType.MsgPropose,
                [cc_entry],
            )
        ]
    )

    assert nt.peers[1].raft.should_bcast_commit()
    assert nt.peers[2].raft.should_bcast_commit()
    assert nt.peers[3].raft.should_bcast_commit()

    assert nt.peers[1].raft_log.get_committed() == 6
    assert nt.peers[2].raft_log.get_committed() == 6
    assert nt.peers[3].raft_log.get_committed() == 6


# test_set_priority checks the set_priority function in RawNode.
def test_set_priority():
    l = default_logger()
    s = new_storage()
    raw_node = new_raw_node(1, [1], 10, 1, s, l)
    priorities = [0, 1, 5, 10, 10000]
    for p in priorities:
        raw_node.set_priority(p)
        assert raw_node.get_raft().get_priority() == p


# TestNodeBoundedLogGrowthWithPartition tests a scenario where a leader is
# partitioned from a quorum of nodes. It verifies that the leader's log is
# protected from unbounded growth even as new entries continue to be proposed.
# This protection is provided by the max_uncommitted_size configuration.
def test_bounded_uncommitted_entries_growth_with_partition():
    l = default_logger()
    config = Config(id=1, max_uncommitted_size=12)
    s = new_storage()
    raw_node = new_raw_node_with_config([1], config, s.clone(), l)

    # wait raw_node to be leader
    raw_node.campaign()
    while True:
        rd = raw_node.ready()
        s.wl().set_hardstate(rd.hs().clone())
        s.wl().append(rd.entries())

        if rd.ss():
            raw_node.advance(rd.make_ref())
            break

        raw_node.advance(rd.make_ref())

    # should be accepted
    data = b"hello world!"
    raw_node.propose([], data)

    # should be dropped
    with pytest.raises(ProposalDroppedError):
        raw_node.propose([], data)

    # should be accepted when previous data has been committed
    rd = raw_node.ready()
    s.wl().append(rd.entries())
    raw_node.advance(rd.make_ref())

    data = list(b"hello world!")
    raw_node.propose([], data)


def prepare_async_entries(raw_node: InMemoryRawNode, s: MemStorage):
    raw_node.get_raft().become_candidate()
    raw_node.get_raft().become_leader()

    rd = raw_node.ready()
    s.wl().append(rd.entries())
    raw_node.advance(rd.make_ref())

    data = [1] * 1000
    for _ in range(0, 10):
        raw_node.propose([], data)

    rd = raw_node.ready()
    entries = rd.entries()
    assert len(entries) == 10
    s.wl().append(entries)
    msgs = rd.messages()
    # First append has two entries: the empty entry to confirm the
    # election, and the first proposal (only one proposal gets sent
    # because we're in probe state).
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
    assert len(msgs[0].get_entries()) == 2
    raw_node.advance_append(rd.make_ref())

    s.wl().trigger_log_unavailable(True)

    # Become replicate state
    append_response = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    append_response.set_term(2)
    append_response.set_index(2)
    raw_node.step(append_response)


# Test entries are handled properly when they are fetched asynchronously
def test_raw_node_with_async_entries():
    l = default_logger()
    cfg = new_test_config(1, 10, 1)
    cfg.set_max_size_per_msg(2048)
    s = new_storage()
    raw_node = new_raw_node_with_config([1, 2], cfg, s, l)

    prepare_async_entries(raw_node, s)

    # No entries are sent because the entries are temporarily unavailable
    rd = raw_node.ready()
    entries = rd.entries()
    s.wl().append(entries)
    msgs = rd.messages()
    assert not msgs
    raw_node.advance_append(rd.make_ref())

    # Entries are sent when the entries are ready which is informed by `on_entries_fetched`.
    s.wl().trigger_log_unavailable(False)
    context = s.wl().take_get_entries_context()
    raw_node.on_entries_fetched(context.make_ref())
    rd = raw_node.ready()
    entries = rd.entries()
    s.wl().append(entries)
    msgs = rd.messages()
    assert len(msgs) == 5
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
    assert len(msgs[0].get_entries()) == 2
    raw_node.advance_append(rd.make_ref())


# Test if async fetch entries works well when there is a remove node conf-change.
def test_raw_node_with_async_entries_to_removed_node():
    l = default_logger()
    cfg = new_test_config(1, 10, 1)
    cfg.set_max_size_per_msg(2048)
    s = new_storage()
    raw_node = new_raw_node_with_config([1, 2], cfg, s.clone(), l)

    prepare_async_entries(raw_node, s)

    raw_node.apply_conf_change_v2(remove_node(2))

    # Entries are not sent due to the node is removed.
    s.wl().trigger_log_unavailable(False)
    context = s.wl().take_get_entries_context()
    raw_node.on_entries_fetched(context.make_ref())
    rd = raw_node.ready()
    assert not rd.entries()
    assert not rd.messages()
    raw_node.advance_append(rd.make_ref())


# Test if async fetch entries works well when there is a leader step-down.
def test_raw_node_with_async_entries_on_follower():
    l = default_logger()
    cfg = new_test_config(1, 10, 1)
    cfg.set_max_size_per_msg(2048)
    s = new_storage()
    raw_node = new_raw_node_with_config([1, 2], cfg, s.clone(), l)

    prepare_async_entries(raw_node, s)

    # Set recent inactive to step down leader
    raw_node.get_raft().prs().get(2).set_recent_active(False)
    msg = Message()
    msg.set_to(1)
    msg.set_msg_type(MessageType.MsgCheckQuorum)
    raw_node.get_raft().step(msg)
    assert raw_node.get_raft().get_state() != StateRole.Leader

    # Entries are not sent due to the leader is changed.
    s.wl().trigger_log_unavailable(False)
    context = s.wl().take_get_entries_context()
    raw_node.on_entries_fetched(context.make_ref())
    rd = raw_node.ready()
    assert not rd.entries()
    assert not rd.messages()
    raw_node.advance_append(rd.make_ref())


def test_raw_node_async_entries_with_leader_change():
    l = default_logger()
    cfg = new_test_config(1, 10, 1)
    cfg.set_max_size_per_msg(2048)
    s = new_storage()
    raw_node = new_raw_node_with_config([1, 2], cfg, s.clone(), l)

    raw_node.get_raft().become_candidate()
    raw_node.get_raft().become_leader()

    rd = raw_node.ready()
    s.wl().append(rd.entries())
    raw_node.advance(rd.make_ref())

    data = [1] * 1000
    for _ in range(0, 10):
        raw_node.propose([], data)

    rd = raw_node.ready()
    entries = rd.entries()
    assert len(entries) == 10
    s.wl().append(entries)
    msgs = rd.messages()
    # election, and the first proposal (only one proposal gets sent
    # First append has two entries: the empty entry to confirm the
    # because we're in probe state).
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
    assert len(msgs[0].get_entries()) == 2
    raw_node.advance_append(rd.make_ref())

    s.wl().trigger_log_unavailable(True)

    # Become replicate state
    append_response = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    append_response.set_term(2)
    append_response.set_index(2)
    raw_node.step(append_response)

    raw_node.get_raft().become_follower(raw_node.get_raft().get_term() + 1, 2)
    raw_node.get_raft().become_candidate()
    raw_node.get_raft().become_leader()

    # Entries are not sent due to the leadership or the term is changed.
    s.wl().trigger_log_unavailable(False)
    context = s.wl().take_get_entries_context()
    raw_node.on_entries_fetched(context.make_ref())
    rd = raw_node.ready()
    # no-op entry
    assert len(rd.entries()) == 1
    assert not rd.messages()
    raw_node.advance_append(rd.make_ref())


def test_raw_node_with_async_apply():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1]))

    raw_node = new_raw_node(1, [1], 10, 1, s.clone(), l)
    raw_node.campaign()
    rd = raw_node.ready()

    # Single node should become leader.
    if ss := rd.ss():
        assert ss.get_leader_id() == raw_node.get_raft().get_leader_id()
    else:
        assert False

    s.wl().append(rd.entries())
    raw_node.advance(rd.make_ref())

    last_index = raw_node.get_raft().get_raft_log().last_index()

    data = b"hello world!"

    for _ in range(1, 10):
        cnt = random.randint(0, MAX_UINT64) % 10 + 1

        for _ in range(0, cnt):
            raw_node.propose([], data)

        rd = raw_node.ready()
        entries = list(map(lambda entry: entry.clone(), rd.entries()))
        assert entries[0].get_index() == last_index + 1
        assert entries[-1].get_index() == last_index + cnt
        must_cmp_ready(rd.make_ref(), None, None, entries, [], None, True, True, True)

        s.wl().append(entries)

        light_rd = raw_node.advance_append(rd.make_ref())
        assert entries == light_rd.committed_entries()
        assert light_rd.commit_index() == last_index + cnt

        # No matter how applied index changes, the index of next committed
        # entries should be the same.
        raw_node.advance_apply_to(last_index + 1)
        assert not raw_node.has_ready()

        last_index += cnt


# Test if the ready process is expected when a follower receives a snapshot
# and some committed entries after its snapshot.
def test_raw_node_entries_after_snapshot():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1, 2]))

    raw_node = new_raw_node(1, [1, 2], 10, 1, s.clone(), l)

    entries = []
    for i in range(2, 20):
        entries.append(new_entry(2, i, "hello"))

    append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
    append_msg.set_term(2)
    append_msg.set_index(1)
    append_msg.set_log_term(1)
    append_msg.set_commit(5)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    ss = soft_state(2, StateRole.Follower)

    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(2, 5, 0),
        entries,
        [],
        None,
        True,
        False,
        True,
    )

    s.wl().set_hardstate(rd.hs().clone())
    s.wl().append(rd.entries())
    light_rd = raw_node.advance(rd.make_ref())
    assert not light_rd.commit_index()
    assert light_rd.committed_entries() == entries[:4]
    assert not light_rd.messages()

    snapshot = new_snapshot(10, 3, [1, 2])
    snapshot_msg = new_message(2, 1, MessageType.MsgSnapshot, 0)
    snapshot_msg.set_term(3)
    snapshot_msg.set_snapshot(snapshot.clone())
    raw_node.step(snapshot_msg)

    entries = []
    for i in range(11, 14):
        entries.append(new_entry(3, i, "hello"))

    append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
    append_msg.set_term(3)
    append_msg.set_index(10)
    append_msg.set_log_term(3)
    append_msg.set_commit(12)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    # If there is a snapshot, the committed entries should be empty.
    must_cmp_ready(
        rd.make_ref(),
        None,
        hard_state(3, 12, 0),
        entries,
        [],
        snapshot,
        True,
        False,
        True,
    )
    # Should have a MsgAppendResponse
    assert rd.persisted_messages()[0].get_msg_type() == MessageType.MsgAppendResponse

    s.wl().set_hardstate(rd.hs().clone())
    s.wl().apply_snapshot(rd.snapshot().clone())
    s.wl().append(rd.entries())

    light_rd = raw_node.advance(rd.make_ref())
    assert not light_rd.commit_index()
    assert light_rd.committed_entries() == entries[:2]
    assert not light_rd.messages()


# Test if the given committed entries are persisted when some persisted
# entries are overwritten by a new leader.
def test_raw_node_overwrite_entries():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1, 2, 3]))

    raw_node = new_raw_node(1, [1, 2, 3], 10, 1, s.clone(), l)

    entries = [
        new_entry(2, 2, "hello"),
        new_entry(2, 3, "hello"),
        new_entry(2, 4, "hello"),
    ]
    append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
    append_msg.set_term(2)
    append_msg.set_index(1)
    append_msg.set_log_term(1)
    append_msg.set_commit(1)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    ss = soft_state(2, StateRole.Follower)
    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(2, 1, 0),
        entries,
        [],
        None,
        True,
        False,
        True,
    )
    # Should have a MsgAppendResponse
    assert rd.persisted_messages()[0].get_msg_type() == MessageType.MsgAppendResponse
    s.wl().set_hardstate(rd.hs().clone())
    s.wl().append(rd.entries())

    light_rd = raw_node.advance(rd.make_ref())
    assert not light_rd.commit_index()
    assert not light_rd.committed_entries()
    assert not light_rd.messages()

    entries_2 = [
        new_entry(3, 4, "hello"),
        new_entry(3, 5, "hello"),
        new_entry(3, 6, "hello"),
    ]
    append_msg = new_message_with_entries(3, 1, MessageType.MsgAppend, entries_2)
    append_msg.set_term(3)
    append_msg.set_index(3)
    append_msg.set_log_term(2)
    append_msg.set_commit(5)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    ss = soft_state(3, StateRole.Follower)
    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(3, 5, 0),
        entries_2,
        entries[:2],
        None,
        True,
        False,
        True,
    )
    # Should have a MsgAppendResponse
    assert rd.persisted_messages()[0].get_msg_type() == MessageType.MsgAppendResponse
    s.wl().set_hardstate(rd.hs().clone())
    s.wl().append(rd.entries())

    light_rd = raw_node.advance(rd.make_ref())
    assert not light_rd.commit_index()
    assert light_rd.committed_entries() == entries_2[:2]
    assert not light_rd.messages()


# Test if async ready process is expected when a leader receives
# the append response and persist its entries.
def test_async_ready_leader():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1, 2, 3]))

    raw_node = new_raw_node(1, [1, 2, 3], 10, 1, s.clone(), l)
    raw_node.get_raft().become_candidate()
    raw_node.get_raft().become_leader()
    rd = raw_node.ready()

    if ss := rd.ss():
        assert ss.get_leader_id() == raw_node.get_raft().get_leader_id()
    else:
        assert False

    s.wl().append(rd.entries())
    raw_node.advance(rd.make_ref())

    assert raw_node.get_raft().get_term() == 2
    first_index = raw_node.get_raft().get_raft_log().last_index()

    data = b"hello world!"

    # Set node 2 progress to replicate
    raw_node.get_raft().prs().get(2).set_matched(1)
    raw_node.get_raft().prs().get(2).become_replicate()

    for i in range(0, 10):
        for _ in range(0, 10):
            raw_node.propose([], data)

        rd = raw_node.ready()
        assert rd.number() == i + 2
        entries = list(map(lambda entry: entry.clone(), rd.entries()))
        assert entries[0].get_index() == first_index + i * 10 + 1
        assert entries[-1].get_index() == first_index + i * 10 + 10

        # Leader‘s msg can be sent immediately.
        must_cmp_ready(rd.make_ref(), None, None, entries, [], None, False, True, True)
        for msg in rd.take_messages():
            assert msg.get_msg_type() == MessageType.MsgAppend

        s.wl().append(entries)
        raw_node.advance_append_async(rd.make_ref())

    # Unpersisted Ready number in range [2, 11]
    raw_node.on_persist_ready(4)
    # No new committed entries due to two nodes in this cluster
    assert not raw_node.has_ready()

    # The index of uncommitted entries in range [first_index, first_index + 100]
    append_response = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    append_response.set_term(2)
    append_response.set_index(first_index + 100)

    raw_node.step(append_response)

    # Forward commit index due to append response
    rd = raw_node.ready()
    assert rd.hs() == hard_state(2, first_index + 30, 1)
    assert rd.committed_entries()[0].get_index() == first_index
    assert rd.committed_entries()[-1].get_index() == first_index + 30
    assert rd.messages()

    s.wl().set_hardstate(rd.hs().clone())
    raw_node.advance_append_async(rd.make_ref())

    # Forward commit index due to persist ready
    raw_node.on_persist_ready(8)
    rd = raw_node.ready()
    assert rd.hs() == hard_state(2, first_index + 70, 1)
    assert rd.committed_entries()[0].get_index() == first_index + 31
    assert rd.committed_entries()[-1].get_index() == first_index + 70
    assert rd.messages()
    assert not rd.persisted_messages()
    s.wl().set_hardstate(rd.hs().clone())

    # Forward commit index due to persist last ready
    light_rd = raw_node.advance_append(rd.make_ref())
    assert light_rd.commit_index() == first_index + 100
    assert light_rd.committed_entries()[0].get_index() == first_index + 71
    assert light_rd.committed_entries()[-1].get_index() == first_index + 100
    assert light_rd.messages()

    # Test when 2 followers response the append entries msg and leader has
    # not persisted them yet.
    first_index += 100
    for _ in range(0, 10):
        raw_node.propose([], data)

    rd = raw_node.ready()
    assert rd.number() == 14
    entries = list(map(lambda entry: entry.clone(), rd.entries()))
    assert entries[0].get_index(), first_index + 1
    assert entries[-1].get_index(), first_index + 10
    # Leader‘s msg can be sent immediately.
    must_cmp_ready(rd.make_ref(), None, None, entries, [], None, False, True, True)
    for msg in rd.take_messages():
        assert msg.get_msg_type() == MessageType.MsgAppend

    s.wl().append(entries)
    raw_node.advance_append_async(rd.make_ref())

    append_response = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    append_response.set_term(2)
    append_response.set_index(first_index + 9)

    raw_node.step(append_response)

    append_response = new_message(3, 1, MessageType.MsgAppendResponse, 0)
    append_response.set_term(2)
    append_response.set_index(first_index + 10)

    raw_node.step(append_response)

    rd = raw_node.ready()
    # It should has some append msgs and its commit index should be first_index + 9.
    must_cmp_ready(
        rd.make_ref(),
        None,
        hard_state(2, first_index + 9, 1),
        [],
        [],
        None,
        False,
        True,
        False,
    )
    for msg in rd.take_messages():
        assert msg.get_msg_type() == MessageType.MsgAppend
        assert msg.get_commit() == first_index + 9

    # Forward commit index due to peer 1's append response and persisted entries
    light_rd = raw_node.advance_append(rd.make_ref())
    assert light_rd.commit_index() == first_index + 10
    assert light_rd.committed_entries()[0].get_index() == first_index + 1
    assert light_rd.committed_entries()[-1].get_index() == first_index + 10
    assert light_rd.messages()


# Test if async ready process is expected when a follower receives
# some append msg and snapshot.
def test_async_ready_follower():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1, 2]))

    raw_node = new_raw_node(1, [1, 2], 10, 1, s.clone(), l)
    first_index = 1
    rd_number = 0
    for cnt in range(0, 3):
        for i in range(0, 10):
            entries = [
                new_entry(2, first_index + i * 3 + 1, "hello"),
                new_entry(2, first_index + i * 3 + 2, "hello"),
                new_entry(2, first_index + i * 3 + 3, "hello"),
            ]
            append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
            append_msg.set_term(2)
            append_msg.set_index(first_index + i * 3)
            if cnt == 0 and i == 0:
                append_msg.set_log_term(1)
            else:
                append_msg.set_log_term(2)

            append_msg.set_commit(first_index + i * 3 + 3)
            raw_node.step(append_msg)

            rd = raw_node.ready()
            assert rd.number() == rd_number + i + 1
            assert rd.hs() == hard_state(2, first_index + i * 3 + 3, 0)
            assert rd.entries() == entries
            assert rd.committed_entries() == []
            assert not rd.messages()
            assert (
                rd.persisted_messages()[0].get_msg_type()
                == MessageType.MsgAppendResponse
            )

            s.wl().set_hardstate(rd.hs())
            s.wl().append(rd.entries())
            raw_node.advance_append_async(rd.make_ref())

        # Unpersisted Ready number in range [1, 10]
        raw_node.on_persist_ready(rd_number + 4)
        rd = raw_node.ready()
        assert not rd.hs()
        assert rd.committed_entries()[0].get_index() == first_index + 1
        assert rd.committed_entries()[-1].get_index() == first_index + 3 * 3 + 3
        assert not rd.messages()
        assert not rd.persisted_messages()

        light_rd = raw_node.advance_append(rd.make_ref())
        assert not light_rd.commit_index()
        assert light_rd.committed_entries()[0].get_index() == first_index + 3 * 3 + 4
        assert light_rd.committed_entries()[-1].get_index() == first_index + 10 * 3
        assert not light_rd.messages()

        first_index += 10 * 3
        rd_number += 11

    snapshot = new_snapshot(first_index + 5, 2, [1, 2])
    snapshot_msg = new_message(2, 1, MessageType.MsgSnapshot, 0)
    snapshot_msg.set_term(2)
    snapshot_msg.set_snapshot(snapshot.clone())
    raw_node.step(snapshot_msg)

    rd = raw_node.ready()
    assert rd.number() == rd_number + 1
    must_cmp_ready(
        rd.make_ref(),
        None,
        hard_state(2, first_index + 5, 0),
        [],
        [],
        snapshot.clone(),
        True,
        False,
        True,
    )

    s.wl().set_hardstate(rd.hs().clone())
    s.wl().apply_snapshot(snapshot)
    s.wl().append(rd.entries())
    raw_node.advance_append_async(rd.make_ref())

    entries = []
    for i in range(1, 10):
        entries.append(new_entry(2, first_index + 5 + i, "hello"))

    append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
    append_msg.set_term(2)
    append_msg.set_index(first_index + 5)
    append_msg.set_log_term(2)
    append_msg.set_commit(first_index + 5 + 3)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    assert rd.number() == rd_number + 2
    must_cmp_ready(
        rd.make_ref(),
        None,
        hard_state(2, first_index + 5 + 3, 0),
        entries,
        [],
        None,
        True,
        False,
        True,
    )
    s.wl().set_hardstate(rd.hs().clone())
    s.wl().append(rd.entries())
    raw_node.advance_append_async(rd.make_ref())

    raw_node.on_persist_ready(rd_number + 1)
    assert raw_node.get_raft().get_raft_log().get_persisted() == first_index + 5
    raw_node.advance_apply_to(first_index + 5)

    raw_node.on_persist_ready(rd_number + 2)

    rd = raw_node.ready()
    must_cmp_ready(
        rd.make_ref(),
        None,
        None,
        [],
        entries[:3],
        None,
        True,
        True,
        False,
    )


# Test if a new leader immediately sends all messages recorded before without
# persisting.
def test_async_ready_become_leader():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(5, 5, [1, 2, 3]))

    raw_node = new_raw_node(1, [1, 2, 3], 10, 1, s.clone(), l)
    for _ in range(1, raw_node.get_raft().election_timeout() * 2):
        raw_node.get_raft().tick_election()

    rd = raw_node.ready()
    assert rd.number() == 1

    ss = soft_state(0, StateRole.Candidate)
    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(6, 5, 1),
        [],
        [],
        None,
        True,
        False,
        True,
    )
    s.wl().set_hardstate(rd.hs().clone())

    for msg in rd.persisted_messages():
        assert msg.get_msg_type() == MessageType.MsgRequestVote

    raw_node.advance_append(rd.make_ref())

    # Peer 1 should reject to vote to peer 2
    vote_request_2 = new_message(2, 1, MessageType.MsgRequestVote, 0)
    vote_request_2.set_term(6)
    vote_request_2.set_log_term(4)
    vote_request_2.set_index(4)
    raw_node.step(vote_request_2)

    rd = raw_node.ready()
    assert rd.number() == 2
    must_cmp_ready(rd.make_ref(), None, None, [], [], None, True, False, False)
    assert (
        rd.persisted_messages()[0].get_msg_type() == MessageType.MsgRequestVoteResponse
    )
    raw_node.advance_append_async(rd.make_ref())

    # Peer 1 should reject to vote to peer 3
    vote_request_3 = new_message(3, 1, MessageType.MsgRequestVote, 0)
    vote_request_3.set_term(6)
    vote_request_3.set_log_term(4)
    vote_request_3.set_index(4)
    raw_node.step(vote_request_3)

    rd = raw_node.ready()
    assert rd.number() == 3
    must_cmp_ready(rd.make_ref(), None, None, [], [], None, True, False, False)
    assert (
        rd.persisted_messages()[0].get_msg_type() == MessageType.MsgRequestVoteResponse
    )

    raw_node.advance_append_async(rd.make_ref())

    # Peer 1 receives the vote from peer 2
    vote_response_2 = new_message(2, 1, MessageType.MsgRequestVoteResponse, 0)
    vote_response_2.set_term(6)
    vote_response_2.set_reject(False)
    raw_node.step(vote_response_2)

    rd = raw_node.ready()
    assert rd.number() == 4
    assert len(rd.entries()) == 1

    ss = soft_state(1, StateRole.Leader)
    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        None,
        rd.entries(),
        [],
        None,
        False,
        True,
        True,
    )
    assert len(rd.messages()) == 2
    for msg in rd.take_messages():
        assert msg.get_msg_type() == MessageType.MsgAppend

    s.wl().append(rd.entries())
    s.wl().append(rd.entries())

    light_rd = raw_node.advance_append(rd.make_ref())
    assert not light_rd.commit_index()
    assert not light_rd.committed_entries()
    assert not light_rd.messages()


def test_async_ready_multiple_snapshot():
    l = default_logger()
    s = new_storage()
    s.wl().apply_snapshot(new_snapshot(1, 1, [1, 2]))

    raw_node = new_raw_node(1, [1, 2], 10, 1, s.clone(), l)

    snapshot = new_snapshot(10, 2, [1, 2])
    snapshot_msg = new_message(2, 1, MessageType.MsgSnapshot, 0)
    snapshot_msg.set_term(2)
    snapshot_msg.set_snapshot(snapshot.clone())
    raw_node.step(snapshot_msg)

    entries = []
    for i in range(11, 14):
        entries.append(new_entry(2, i, "hello"))

    append_msg = new_message_with_entries(2, 1, MessageType.MsgAppend, entries)
    append_msg.set_term(2)
    append_msg.set_index(10)
    append_msg.set_log_term(2)
    append_msg.set_commit(12)
    raw_node.step(append_msg)

    rd = raw_node.ready()
    assert rd.number() == 1
    # If there is a snapshot, the committed entries should be empty.
    ss = soft_state(2, StateRole.Follower)
    must_cmp_ready(
        rd.make_ref(),
        ss.make_ref(),
        hard_state(2, 12, 0),
        entries,
        [],
        snapshot,
        True,
        False,
        True,
    )
    s.wl().set_hardstate(rd.hs().clone())
    s.wl().apply_snapshot(rd.snapshot().clone())
    s.wl().append(rd.entries())

    raw_node.advance_append_async(rd.make_ref())

    snapshot = new_snapshot(20, 1, [1, 2])
    snapshot_msg = new_message(2, 1, MessageType.MsgSnapshot, 0)
    snapshot_msg.set_term(2)
    snapshot_msg.set_snapshot(snapshot.clone())
    raw_node.step(snapshot_msg)

    raw_node.on_persist_ready(1)

    assert raw_node.get_raft().get_raft_log().get_persisted() == 13

    raw_node.advance_apply_to(10)

    rd = raw_node.ready()
    assert rd.number() == 2
    must_cmp_ready(
        rd.make_ref(),
        None,
        hard_state(2, 20, 0),
        [],
        [],
        snapshot,
        True,
        False,
        True,
    )
    s.wl().set_hardstate(rd.hs().clone())
    s.wl().apply_snapshot(rd.snapshot().clone())

    light_rd = raw_node.advance_append(rd.make_ref())
    assert not light_rd.commit_index()
    assert not light_rd.committed_entries()
    assert not light_rd.messages()

    raw_node.advance_apply_to(20)


def test_committed_entries_pagination():
    l = default_logger()
    s = new_storage()
    raw_node = new_raw_node(1, [1, 2, 3], 10, 1, s, l)

    entries = []
    for i in range(2, 10):
        entries.append(new_entry(1, i, None))

    msg = new_message_with_entries(3, 1, MessageType.MsgAppend, entries)
    msg.set_term(1)
    msg.set_index(1)
    msg.set_log_term(1)
    msg.set_commit(9)
    raw_node.step(msg)

    # Test unpersisted entries won't be fetched.
    # NOTE: maybe it's better to allow fetching unpersisted committed entries.
    rd = raw_node.ready()
    assert not rd.committed_entries()
    assert raw_node.has_ready()

    # Persist entries.
    assert rd.entries()
    raw_node.store().wl().append(rd.entries())

    # Advance the ready, and we can get committed_entries as expected.
    # Test using 0 as `committed_entries_max_size` works as expected.
    raw_node.get_raft().set_max_committed_size_per_ready(0)
    rd = raw_node.advance(rd.make_ref())
    # `MemStorage::entries` uses `util::limit_size` to limit size of committed entries.
    # So there will be at least one entry.
    assert len(rd.committed_entries()) == 1

    # Fetch a `Ready` again without size limit for committed entries.
    assert raw_node.has_ready()
    raw_node.get_raft().set_max_committed_size_per_ready(MAX_UINT64)
    rd = raw_node.ready()
    assert len(rd.committed_entries()) == 7

    # No more `Ready`s.
    assert not raw_node.has_ready()


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
    class IgnoreSizeHintMemStorage:
        def __init__(self, store: MemStorage) -> None:
            self.inner = store

        def entries(self, low: int, high: int, _max_size: int) -> List[Entry]:
            return self.inner.entries(low, high, MAX_UINT64)

        def term(self, idx: int) -> int:
            return self.inner.term(idx)

        def first_index(self) -> int:
            return self.inner.first_index()

        def last_index(self) -> int:
            return self.inner.last_index()

        def snapshot(self, request_index: int) -> Snapshot:
            return self.inner.snapshot(request_index)

    l = default_logger()
    s = IgnoreSizeHintMemStorage(MemStorage.default())
    s.inner.wl().apply_snapshot(new_snapshot(1, 1, [1, 2, 3]))

    entries, size = ([], 0)
    for i in range(2, 10 + 1):
        e = new_entry(1, i, "test data")
        size += e.compute_size()
        entries.append(e)

    s.inner.wl().append(entries)
    s.inner.wl().hard_state().set_commit(10)

    s.inner.wl().append([new_entry(1, 11, "boom")])

    config = new_test_config(1, 10, 1)
    raw_node = InMemoryRawNode(config, s.inner, l)

    # `IgnoreSizeHintMemStorage` will ignore `max_committed_size_per_ready` but
    # `RaftLog::slice won't.`
    raw_node.get_raft().set_max_committed_size_per_ready(size - 1)

    highest_applied = 1
    while highest_applied != 11:
        rd = raw_node.ready()
        committed_entries = rd.take_committed_entries()
        next = committed_entries[0].get_index()
        assert highest_applied + 1 == next

        highest_applied = committed_entries[-1].get_index()
        raw_node.get_raft().get_raft_log().commit_to(11)
