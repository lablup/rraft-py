import math
import pytest
from typing import Any, List, Optional, Tuple, cast
from harness.src.interface import Interface
from harness.src.network import Network
from harness.utils import (
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
)

from harness.tests.test_raft_paper import (
    commit_noop_entry,
)

from rraft import (
    INVALID_INDEX,
    ConfChange,
    ConfChangeError,
    ConfChangeTransition,
    ConfChangeType,
    ConfState,
    Config,
    ConfigInvalidError,
    Entry,
    EntryType,
    GetEntriesContext,
    HardState,
    Logger,
    LoggerRef,
    MemStorage,
    MemStorageRef,
    Message,
    MessageType,
    ProgressState,
    InMemoryRaft,
    InMemoryRaftRef,
    InMemoryRaftLogRef,
    ProposalDroppedError,
    ReadOnlyOption,
    Snapshot,
    StateRole,
    default_logger,
    vote_resp_msg_type,
    new_conf_change_single,
    INVALID_ID,
)


def read_messages(raft: InMemoryRaft) -> List[Message]:
    return raft.take_msgs()


def ents_with_config(
    terms: List[int],
    pre_vote: bool,
    id: int,
    peers: List[int],
    l: Logger | LoggerRef,
) -> Interface:
    store = MemStorage.new_with_conf_state(ConfState(peers, []))

    for i, term in enumerate(terms):
        e = Entry.default()
        e.set_index(i + 1)
        e.set_term(term)
        store.wl().append([e])

    raft = new_test_raft_with_prevote(id, peers, 5, 1, store, pre_vote, l)
    raft.raft.reset(terms[-1])
    return raft


def assert_raft_log(
    prefix: str,
    raft_log: InMemoryRaftLogRef,
    committed: int,
    applied: int,
    last: int,
) -> None:
    assert (
        raft_log.get_committed() == committed
    ), f"{prefix} committed = {raft_log.get_committed()}, want = {committed}"
    assert (
        raft_log.get_applied() == applied
    ), f"{prefix} applied = {raft_log.get_applied()}, want = {applied}"
    assert (
        raft_log.last_index() == last
    ), f"{prefix} last = {raft_log.last_index()}, want = {last}"


# voted_with_config creates a raft state machine with vote and term set
# to the given value but no log entries (indicating that it voted in
# the given term but has not receive any logs).
def voted_with_config(
    vote: int,
    term: int,
    pre_vote: bool,
    id: int,
    peers: List[int],
    l: Logger | LoggerRef,
) -> Interface:
    cs = ConfState(peers, [])
    store = MemStorage.new_with_conf_state(cs)

    store.wl().hard_state().set_vote(vote)
    store.wl().hard_state().set_term(term)

    raft = new_test_raft_with_prevote(id, peers, 5, 1, store, pre_vote, l)
    raft.raft.reset(term)
    return raft


# Persist committed index and fetch next entries.
def next_ents(r: InMemoryRaftRef, s: MemStorageRef) -> List[Entry]:
    unstable_refs = r.get_raft_log().unstable_entries()
    unstable = list(map(lambda e: e.clone(), unstable_refs))

    if unstable:
        e = unstable[-1]
        last_idx, last_term = e.get_index(), e.get_term()
        r.get_raft_log().stable_entries(last_idx, last_term)
        s.wl().append(unstable)
        r.on_persist_entries(last_idx, last_term)

    ents = r.get_raft_log().next_entries(None)
    r.commit_apply(r.get_raft_log().get_committed())

    if ents is None:
        return []

    return ents


def test_progress_committed_index():
    l = default_logger()
    nt = Network.new([None, None, None], l)

    # set node 1 as Leader
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft.get_raft_log(), 1, 0, 1)
    assert_raft_log("#2: ", nt.peers.get(2).raft.get_raft_log(), 1, 0, 1)
    assert_raft_log("#3: ", nt.peers.get(3).raft.get_raft_log(), 1, 0, 1)

    assert nt.peers.get(1).raft.prs().get(1).get_committed_index() == 1
    assert nt.peers.get(1).raft.prs().get(2).get_committed_index() == 1
    assert nt.peers.get(1).raft.prs().get(3).get_committed_index() == 1

    # #1 test append entries
    # append entries between 1 and 2
    test_entries = Entry.default()
    test_entries.set_data(b"testdata")
    m = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.cut(1, 3)
    nt.send([m.clone(), m])
    nt.recover()

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 3, 0, 3)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 3, 0, 3)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 1, 0, 1)

    assert nt.peers.get(1).raft.prs().get(1).get_committed_index() == 3
    assert nt.peers.get(1).raft.prs().get(2).get_committed_index() == 3
    assert nt.peers.get(1).raft.prs().get(3).get_committed_index() == 1

    # #2 test heartbeat
    heartbeat = new_message(1, 1, MessageType.MsgBeat, 0)
    nt.send([heartbeat])

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 3, 0, 3)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 3, 0, 3)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 3, 0, 3)

    # set node 2 as Leader
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])
    assert nt.peers.get(2).raft.get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 4, 0, 4)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 4, 0, 4)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 4, 0, 4)

    assert nt.peers.get(2).raft.prs().get(1).get_committed_index() == 4
    assert nt.peers.get(2).raft.prs().get(2).get_committed_index() == 4
    assert nt.peers.get(2).raft.prs().get(3).get_committed_index() == 4

    # #3 test append entries rejection (fails to update committed index)
    nt.isolate(2)
    nt.send([new_message(2, 2, MessageType.MsgPropose, 2)])
    nt.recover()
    nt.dispatch([new_message(2, 2, MessageType.MsgPropose, 1)])

    # [msg_type: MsgAppend to: 1 from: 2 term: 2 log_term: 2 index: 6 entries {term: 2 index: 7 data: "somedata"} commit: 4,
    # msg_type: MsgAppend to: 3 from: 2 term: 2 log_term: 2 index: 6 entries {term: 2 index: 7 data: "somedata"} commit: 4]
    msg_append = nt.read_messages()
    nt.dispatch(msg_append)

    # [msg_type: MsgAppendResponse to: 2 from: 1 term: 2 index: 6 commit: 4 reject: true reject_hint: 4,
    # msg_type: MsgAppendResponse to: 2 from: 3 term: 2 index: 6 commit: 4 reject: true reject_hint: 4]
    msg_append_response = nt.read_messages()
    nt.dispatch(msg_append)

    # [msg_type: MsgAppend to: 3 from: 2 term: 2 log_term: 2 index: 4 entries {term: 2 index: 5 data: "somedata"} entries {term: 2 index: 6 data: "somedata"} entries {term: 2 index: 7 data: "somedata"} commit: 4,
    # msg_type: MsgAppend to: 1 from: 2 term: 2 log_term: 2 index: 4 entries {term: 2 index: 5 data: "somedata"} entries {term: 2 index: 6 data: "somedata"} entries {term: 2 index: 7 data: "somedata"} commit: 4]
    msg_append = nt.read_messages()

    # committed index remain the same
    assert nt.peers.get(2).raft.prs().get(1).get_committed_index() == 4
    assert nt.peers.get(2).raft.prs().get(2).get_committed_index() == 4
    assert nt.peers.get(2).raft.prs().get(3).get_committed_index() == 4

    # resend append
    nt.send(msg_append)

    # log is up-to-date
    assert nt.peers.get(2).raft.prs().get(1).get_committed_index() == 7
    assert nt.peers.get(2).raft.prs().get(2).get_committed_index() == 7
    assert nt.peers.get(2).raft.prs().get(3).get_committed_index() == 7

    # set node 1 as Leader again
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 8, 0, 8)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 8, 0, 8)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 8, 0, 8)

    # update to 8
    assert nt.peers.get(1).raft.prs().get(1).get_committed_index() == 8
    assert nt.peers.get(1).raft.prs().get(2).get_committed_index() == 8
    assert nt.peers.get(1).raft.prs().get(3).get_committed_index() == 8

    # #4 pass a smaller committed index, it occurs when the append response delay
    nt.dispatch(
        [
            new_message(1, 1, MessageType.MsgPropose, 1),
            new_message(1, 1, MessageType.MsgPropose, 1),
        ]
    )

    msg_append = nt.read_messages()
    nt.dispatch(msg_append)
    msg_append_response = nt.read_messages()
    nt.dispatch(msg_append_response)
    msg_append = nt.read_messages()
    nt.dispatch(msg_append)
    msg_append_response = nt.read_messages()
    # m1: msg_type: MsgAppendResponse to: 1 from: 3 term: 3 index: 10 commit: 10
    # m2: msg_type: MsgAppendResponse to: 1 from: 2 term: 3 index: 10 commit: 10
    m1 = msg_append_response.pop(1)
    m2 = msg_append_response.pop(2)
    nt.send([m1, m2])

    assert nt.peers.get(1).raft.prs().get(1).get_committed_index() == 10
    assert nt.peers.get(1).raft.prs().get(2).get_committed_index() == 10
    assert nt.peers.get(1).raft.prs().get(3).get_committed_index() == 10

    # committed index remain 10

    # msg_type: MsgAppendResponse to: 1 from: 2 term: 3 index: 10 commit: 9,
    # msg_type: MsgAppendResponse to: 1 from: 3 term: 3 index: 10 commit: 9
    nt.send(msg_append_response)
    assert nt.peers.get(1).raft.prs().get(1).get_committed_index() == 10
    assert nt.peers.get(1).raft.prs().get(2).get_committed_index() == 10
    assert nt.peers.get(1).raft.prs().get(3).get_committed_index() == 10


def test_progress_leader():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2], 5, 1, storage, l)
    raft.raft.become_candidate()
    raft.raft.become_leader()
    # For no-op entry
    raft.persist()
    raft.raft.prs().get(2).become_replicate()

    prop_msg = new_message(1, 1, MessageType.MsgPropose, 1)
    for i in range(0, 5):
        assert raft.raft.prs().get(1).get_state() == ProgressState.Replicate

        matched = raft.raft.prs().get(1).get_matched()
        next_idx = raft.raft.prs().get(1).get_next_idx()
        assert matched == i + 1
        assert next_idx == matched + 1

        # Should not throw exception
        raft.step(prop_msg.clone())
        raft.persist()


# test_progress_resume_by_heartbeat_resp ensures raft.heartbeat reset progress.paused by
# heartbeat response.
def test_progress_resume_by_heartbeat_resp():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2], 5, 1, storage, l)
    raft.raft.become_candidate()
    raft.raft.become_leader()
    raft.raft.prs().get(2).set_paused(True)

    raft.step(new_message(1, 1, MessageType.MsgBeat, 0))
    assert raft.raft.prs().get(2).get_paused()
    raft.raft.prs().get(2).become_replicate()
    raft.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
    assert not raft.raft.prs().get(2).get_paused()


def test_progress_paused():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2], 5, 1, storage, l)
    raft.raft.become_candidate()
    raft.raft.become_leader()

    m = Message.default()
    m.set_from(1)
    m.set_to(1)
    m.set_msg_type(MessageType.MsgPropose)

    e = Entry.default()
    e.set_data(b"some_data")
    m.set_entries([e])

    raft.step(m.clone())
    raft.step(m.clone())
    raft.step(m)

    ms = read_messages(raft.raft)
    assert len(ms) == 1


def test_progress_flow_control():
    l = default_logger()
    cfg = new_test_config(1, 5, 1)
    cfg.set_max_inflight_msgs(3)
    cfg.set_max_size_per_msg(2048)
    cs = ConfState([1, 2], [])
    s = MemStorage.new_with_conf_state(cs)

    r = new_test_raft_with_config(cfg, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()

    # Throw away all the messages relating to the initial election.
    r.read_messages()

    # While node 2 is in probe state, propose a bunch of entries.
    r.raft.prs().get(2).become_probe()
    data = "a" * 1000
    for _ in range(0, 10):
        msg = new_message_with_entries(
            1, 1, MessageType.MsgPropose, [new_entry(0, 0, data)]
        )
        r.step(msg)

    ms = r.read_messages()
    # First append has two entries: the empty entry to confirm the
    # election, and the first proposal (only one proposal gets sent
    # because we're in probe state).
    assert len(ms) == 1
    assert ms[0].get_msg_type() == MessageType.MsgAppend
    assert len(ms[0].get_entries()) == 2
    assert len(ms[0].get_entries()[0].get_data()) == 0
    assert len(ms[0].get_entries()[1].get_data()) == 1000

    # When this append is acked, we change to replicate state and can
    # send multiple messages at once.
    msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    msg.set_index(ms[0].get_entries()[1].get_index())
    r.step(msg)
    ms = r.read_messages()
    assert len(ms) == 3

    for i, m in enumerate(ms):
        assert (
            m.get_msg_type() == MessageType.MsgAppend
        ), f"{i}: expected MsgAppend, got {m.get_msg_type()}"

        assert (
            len(m.get_entries()) == 2
        ), f"{i}: expected 2 entries, got {len(m.get_entries())}"

    # Ack all three of those messages together and get the last two
    # messages (containing three entries).
    msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    msg.set_index(ms[2].get_entries()[1].get_index())
    r.step(msg)
    ms = r.read_messages()
    assert len(ms) == 2

    for i, m in enumerate(ms):
        assert (
            m.get_msg_type() == MessageType.MsgAppend
        ), f"{i}: expected MsgAppend, got {m.get_msg_type()}"

    assert len(ms[0].get_entries()) == 2
    assert len(ms[1].get_entries()) == 1


# test_leader_election
# test_leader_election_pre_vote
@pytest.mark.parametrize("pre_vote", [True, False])
def test_leader_election_with_config(pre_vote: bool):
    l = default_logger()
    config = Network.default_config()
    config.set_pre_vote(pre_vote)

    class Test:
        def __init__(self, network: Any, state: StateRole, term: int) -> None:
            self.network = network
            self.state = state
            self.term = term

    NOP_STEPPER = Interface(None)

    tests = [
        Test(
            Network.new_with_config([None, None, None], config, l),
            StateRole.Leader,
            1,
        ),
        Test(
            Network.new_with_config([None, None, NOP_STEPPER], config, l),
            StateRole.Leader,
            1,
        ),
        Test(
            Network.new_with_config([None, NOP_STEPPER, NOP_STEPPER], config, l),
            StateRole.Candidate,
            1,
        ),
        Test(
            Network.new_with_config([None, NOP_STEPPER, NOP_STEPPER, None], config, l),
            StateRole.Candidate,
            1,
        ),
        Test(
            Network.new_with_config(
                [None, NOP_STEPPER, NOP_STEPPER, None, None], config, l
            ),
            StateRole.Leader,
            1,
        ),
        # three logs further along than 0, but in the same term so rejection
        # are returned instead of the votes being ignored.
        Test(
            Network.new_with_config(
                [
                    None,
                    ents_with_config([1], pre_vote, 2, [1, 2, 3, 4, 5], l),
                    ents_with_config([1], pre_vote, 3, [1, 2, 3, 4, 5], l),
                    ents_with_config([1, 1], pre_vote, 4, [1, 2, 3, 4, 5], l),
                    None,
                ],
                config,
                l,
            ),
            StateRole.Follower,
            1,
        ),
    ]

    for i, v in enumerate(tests):
        network, state, term = v.network, v.state, v.term
        m = Message.default()
        m.set_from(1)
        m.set_to(1)
        m.set_msg_type(MessageType.MsgHup)
        network.send([m])
        raft = network.peers.get(1)

        exp_state, exp_term = state, term
        if state == StateRole.Candidate and pre_vote:
            # In pre-vote mode, an election that fails to complete
            # leaves the node in pre-candidate state without advancing
            # the term.
            exp_state, exp_term = StateRole.PreCandidate, 0

        assert (
            raft.raft.get_state() == exp_state
        ), f"#{i}: state = {raft.raft.get_state()}, want {exp_state}"

        assert (
            raft.raft.get_term() == exp_term
        ), f"#{i}: term = {raft.raft.get_term()}, want {exp_term}"


# test_leader_cycle verifies that each node in a cluster can campaign
# and be elected in turn. This ensures that elections (including
# pre-vote) work when not starting from a clean state (as they do in
# test_leader_election)
#
# test_leader_cycle
# test_leader_cycle_pre_vote
@pytest.mark.parametrize("pre_vote", [True, False])
def test_leader_cycle_with_config(pre_vote: bool):
    l = default_logger()
    config = Network.default_config()
    config.set_pre_vote(pre_vote)

    network = Network.new_with_config([None, None, None], config, l)

    for campaigner_id in range(1, 4):
        network.send([new_message(campaigner_id, campaigner_id, MessageType.MsgHup, 0)])

        for sm in network.peers.values():
            assert not (
                sm.raft.get_id() == campaigner_id
                and sm.raft.get_state() != StateRole.Leader
            ), f"pre_vote={pre_vote}: campaigning node {sm.raft.get_id()} state = {sm.raft.get_state()}, want Leader"

            assert not (
                sm.raft.get_id() != campaigner_id
                and sm.raft.get_state() != StateRole.Follower
            ), f"pre_vote={pre_vote}: after campaign of node {campaigner_id}, node {sm.raft.get_id()} had state = {sm.raft.get_state()}, want \
                     Follower"


# test_leader_election_overwrite_newer_logs tests a scenario in which a
# newly-elected leader does *not* have the newest (i.e. highest term)
# log entries, and must overwrite higher-term log entries with
# lower-term ones.
#
# test_leader_election_overwrite_newer_logs
# test_leader_election_overwrite_newer_logs_pre_vote
@pytest.mark.parametrize("pre_vote", [True, False])
def test_leader_election_overwrite_newer_logs_with_config(pre_vote: bool):
    # This network represents the results of the following sequence of
    # events:
    # - Node 1 won the election in term 1.
    # - Node 1 replicated a log entry to node 2 but died before sending
    #   it to other nodes.
    # - Node 3 won the second election in term 2.
    # - Node 3 wrote an entry to its logs but died without sending it
    #   to any other nodes.
    #
    # At this point, nodes 1, 2, and 3 all have uncommitted entries in
    # their logs and could win an election at term 3. The winner's log
    # entry overwrites the loser's. (test_leader_sync_follower_log tests
    # the case where older log entries are overwritten, so this test
    # focuses on the case where the newer entries are lost).
    l = default_logger()
    peers = [1, 2, 3, 4, 5]
    config = Network.default_config()
    config.set_pre_vote(pre_vote)
    network = Network.new_with_config(
        [
            # Node 1: Won first election
            ents_with_config([1], pre_vote, 1, peers, l),
            # Node 2: Get logs from node 1
            ents_with_config([1], pre_vote, 2, peers, l),
            # Node 3: Won second election
            ents_with_config([2], pre_vote, 3, peers, l),
            # Node 4: Voted but didn't get logs
            voted_with_config(3, 2, pre_vote, 4, peers, l),
            # Node 5: Voted but didn't get logs
            voted_with_config(3, 2, pre_vote, 5, peers, l),
        ],
        config,
        l,
    )

    # Node 1 campaigns. The election fails because a quorum of nodes
    # know about the election that already happened at term 2. Node 1's
    # term is pushed ahead to 2.
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert network.peers.get(1).raft.get_state() == StateRole.Follower
    assert network.peers.get(1).raft.get_term() == 2

    # Node 1 campaigns again with a higher term. this time it succeeds.
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert network.peers.get(1).raft.get_state() == StateRole.Leader
    assert network.peers.get(1).raft.get_term() == 3

    # Now all nodes agree on a log entry with term 1 at index 1 (and
    # term 3 at index 2).
    for id, sm in network.peers.items():
        entries = sm.raft_log.all_entries()
        assert len(entries) == 2, f"node {id}: entries.len() == {len(entries)}, want 2"

        assert (
            entries[0].get_term() == 1
        ), f"node {id}: term at index 1 == {entries[0].get_term()}, want 1"

        assert (
            entries[1].get_term() == 3
        ), f"node {id}: term at index 2 == {entries[1].get_term()}, want 3"


# test_vote_from_any_state
# test_prevote_from_any_state
@pytest.mark.parametrize(
    "vt", [MessageType.MsgRequestVote, MessageType.MsgRequestPreVote]
)
def test_vote_from_any_state_for_type(vt: MessageType):
    l = default_logger()
    all_states = [
        StateRole.Follower,
        StateRole.Candidate,
        StateRole.PreCandidate,
        StateRole.Leader,
    ]

    for state in all_states:
        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
        r.raft.set_term(1)
        if state == StateRole.Follower:
            term = r.raft.get_term()
            r.raft.become_follower(term, 3)
        elif state == StateRole.PreCandidate:
            r.raft.become_pre_candidate()
        elif state == StateRole.Candidate:
            r.raft.become_candidate()
        else:
            r.raft.become_candidate()
            r.raft.become_leader()

        # Note that setting our state above may have advanced r.term
        # past its initial value.
        orig_term = r.raft.get_term()
        new_term = r.raft.get_term() + 1

        msg = new_message(2, 1, vt, 0)
        msg.set_term(new_term)
        msg.set_log_term(orig_term)
        msg.set_index(42)
        r.step(msg)

        assert (
            len(r.raft.get_msgs()) == 1
        ), f"{vt},{state}: {len(r.raft.get_msgs())} response messages, want 1: {r.raft.get_msgs()}"

        resp = r.raft.get_msgs()[0]

        assert resp.get_msg_type() == vote_resp_msg_type(
            vt
        ), f"{vt},{state}: response message is {resp.get_msg_type()}, want {vote_resp_msg_type(vt)}"

        assert not resp.get_reject(), f"{vt},{state}: unexpected rejection"

        # If this was a real vote, we reset our state and term.
        if vt == MessageType.MsgRequestVote:
            assert (
                r.raft.get_state() == StateRole.Follower
            ), f"{vt},{state}, state is {r.raft.get_state()}, want {StateRole.Follower}"

            assert (
                r.raft.get_term() == new_term
            ), f"{vt},{state}, term is {r.raft.get_term()}, want {new_term}"

            assert (
                r.raft.get_vote() == 2
            ), f"{vt},{state}, vote {r.raft.get_vote()}, want 2"
        else:
            # In a pre-vote, nothing changes.
            assert (
                r.raft.get_state() == state
            ), f"{vt},{state}, state {r.raft.get_state()}, want {state}"

            assert (
                r.raft.get_term() == orig_term
            ), f"{vt},{state}, term {r.raft.get_term()}, want {orig_term}"

            # If state == Follower or PreCandidate, r hasn't voted yet.
            # In Candidate or Leader, it's voted for itself.
            assert (
                r.raft.get_vote() == INVALID_ID or r.raft.get_vote() == 1
            ), f"{vt},{state}, vote {r.raft.get_vote()}, want {INVALID_ID} or 1"


def test_log_replication():
    l = default_logger()

    class Test:
        def __init__(
            self, network: Network, msgs: List[Message], wcommitted: int
        ) -> None:
            self.network = network
            self.msgs = msgs
            self.wcommitted = wcommitted

    tests = [
        Test(
            Network.new([None, None, None], l),
            [new_message(1, 1, MessageType.MsgPropose, 1)],
            2,
        ),
        Test(
            Network.new([None, None, None], l),
            [
                new_message(1, 1, MessageType.MsgPropose, 1),
                new_message(1, 2, MessageType.MsgHup, 0),
                new_message(1, 2, MessageType.MsgPropose, 1),
            ],
            4,
        ),
    ]

    for i, v in enumerate(tests):
        network, msgs, wcommitted = v.network, v.msgs, v.wcommitted
        network.send([new_message(1, 1, MessageType.MsgHup, 0)])
        for m in msgs:
            network.send([m.clone()])

        for j, x in network.peers.items():
            assert (
                x.raft_log.get_committed() == wcommitted
            ), f"#{i}.{j}: committed = {x.raft_log.get_commited()}, want {wcommitted}"

            ents = next_ents(x.raft, network.storage.get(j))
            ents = list(filter(lambda x: len(x.get_data()) != 0, ents))

            for k, m in enumerate(
                filter(
                    lambda msg: msg.get_msg_type() == MessageType.MsgPropose,
                    msgs,
                )
            ):
                assert (
                    ents[k].get_data() == m.get_entries()[0].get_data()
                ), f"#{i}.{j}: data = {ents[k].get_data()}, want {m.get_entries()[0].get_data()}"


def test_single_node_commit():
    l = default_logger()
    tt = Network.new([None], l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    assert tt.peers.get(1).raft_log.get_committed() == 3


# test_cannot_commit_without_new_term_entry tests the entries cannot be committed
# when leader changes, no new proposal comes in and ChangeTerm proposal is
# filtered.
def test_cannot_commit_without_new_term_entry():
    l = default_logger()
    tt = Network.new([None, None, None, None, None], l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # 0 cannot reach 2, 3, 4
    tt.cut(1, 3)
    tt.cut(1, 4)
    tt.cut(1, 5)

    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    assert tt.peers.get(1).raft_log.get_committed() == 1

    # network recovery
    tt.recover()
    # avoid committing ChangeTerm proposal
    tt.ignore(MessageType.MsgAppend)

    # elect 2 as the new leader with term 2
    tt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # no log entries from previous term should be committed
    tt.peers.get(2).raft_log.get_committed() == 1

    tt.recover()
    # send heartbeat; reset wait
    tt.send([new_message(2, 2, MessageType.MsgBeat, 0)])
    # append an entry at current term
    tt.send([new_message(2, 2, MessageType.MsgPropose, 1)])
    # expect the committed to be advanced
    assert tt.peers.get(2).raft_log.get_committed() == 5


# test_commit_without_new_term_entry tests the entries could be committed
# when leader changes, no new proposal comes in.
def test_commit_without_new_term_entry():
    l = default_logger()
    tt = Network.new([None, None, None, None, None], l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # 0 cannot reach 2, 3, 4
    tt.cut(1, 3)
    tt.cut(1, 4)
    tt.cut(1, 5)

    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    assert tt.peers.get(1).raft_log.get_committed() == 1

    # network recovery
    tt.recover()

    # elect 1 as the new leader with term 2
    # after append a ChangeTerm entry from the current term, all entries
    # should be committed
    tt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    assert tt.peers.get(1).raft_log.get_committed() == 4


def test_dueling_candidates():
    l = default_logger()
    storage_a = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, storage_a, l)
    storage_b = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, storage_b, l)
    storage_c = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, storage_c, l)

    nt = Network.new([a, b, c], l)
    nt.cut(1, 3)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # 1 becomes leader since it receives votes from 1 and 2
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    # 3 stays as candidate since it receives a vote from 3 and a rejection from 2
    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate

    nt.recover()

    # Candidate 3 now increases its term and tries to vote again, we except it to
    # disrupt the leader 1 since it has a higher term, 3 will be follower again
    # since both 1 and 2 rejects its vote request since 3 does not have a long
    # enough log.
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    class Test:
        def __init__(
            self, state: StateRole, term: int, raft_log: Tuple[int, int, int]
        ) -> None:
            self.state = state
            self.term = term
            self.raft_log = raft_log

    tests = [
        # role, term, committed, applied, last index.
        Test(StateRole.Follower, 2, (1, 0, 1)),
        Test(StateRole.Follower, 2, (1, 0, 1)),
        Test(StateRole.Follower, 2, (0, 0, 0)),
    ]

    for i, v in enumerate(tests):
        state, term, raft_log = v.state, v.term, v.raft_log
        id = i + 1

        assert (
            nt.peers.get(id).raft.get_state() == state
        ), f"#{i}: state = {nt.peers.get(id).raft.get_state()}, want {state}"

        assert (
            nt.peers.get(id).raft.get_term() == term
        ), f"#{i}: term = {nt.peers.get(id).raft.get_term()}, want {term}"

        prefix = f"#{i}: "
        assert_raft_log(
            prefix,
            nt.peers.get(id).raft_log,
            raft_log[0],
            raft_log[1],
            raft_log[2],
        )


def test_dueling_pre_candidates():
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft_with_prevote(1, [1, 2, 3], 10, 1, a_storage, True, l)
    b_storage = new_storage()
    b = new_test_raft_with_prevote(2, [1, 2, 3], 10, 1, b_storage, True, l)
    c_storage = new_storage()
    c = new_test_raft_with_prevote(3, [1, 2, 3], 10, 1, c_storage, True, l)

    config = Network.default_config()
    config.set_pre_vote(True)
    nt = Network.new_with_config([a, b, c], config, l)
    nt.cut(1, 3)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # 1 becomes leader since it receives votes from 1 and 2
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    # 3 campaigns then reverts to follower when its pre_vote is rejected
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    nt.recover()

    # Candidate 3 now increases its term and tries to vote again.
    # With pre-vote, it does not disrupt the leader.
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    class Test:
        def __init__(
            self, id: int, state: StateRole, term: int, raft_log: Tuple[int, int, int]
        ) -> None:
            self.id = id
            self.state = state
            self.term = term
            self.raft_log = raft_log

    tests = [
        Test(1, StateRole.Leader, 1, (1, 0, 1)),
        Test(2, StateRole.Follower, 1, (1, 0, 1)),
        Test(3, StateRole.Follower, 1, (0, 0, 0)),
    ]

    for i, v in enumerate(tests):
        id, state, term, raft_log = v.id, v.state, v.term, v.raft_log
        assert (
            nt.peers.get(id).raft.get_state() == state
        ), f"#{i}: state = {nt.peers.get(id).raft.get_state()}, want {state}"

        assert (
            nt.peers.get(id).raft.get_term() == term
        ), f"#{i}: term = {nt.peers.get(id).raft.get_term()}, want {term}"

        prefix = f"#{i}: "
        assert_raft_log(
            prefix, nt.peers.get(id).raft_log, raft_log[0], raft_log[1], raft_log[2]
        )


def test_candidate_concede():
    l = default_logger()
    tt = Network.new([None, None, None], l)
    tt.isolate(1)

    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    tt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # heal the partition
    tt.recover()
    # send heartbeat; reset wait
    tt.send([new_message(3, 3, MessageType.MsgBeat, 0)])

    # send a proposal to 3 to flush out a MsgAppend to 1
    data = "force follower"
    m = new_message(3, 3, MessageType.MsgPropose, 0)
    m.set_entries([new_entry(0, 0, data)])
    tt.send([m])
    # send heartbeat; flush out commit
    tt.send([new_message(3, 3, MessageType.MsgBeat, 0)])

    assert tt.peers.get(1).raft.get_state() == StateRole.Follower
    assert tt.peers.get(1).raft.get_term() == 1

    for p in tt.peers.values():
        assert p.raft_log.get_committed() == 2
        assert p.raft_log.get_applied() == 0
        assert p.raft_log.last_index() == 2


def test_single_node_candidate():
    l = default_logger()
    tt = Network.new([None], l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert tt.peers.get(1).raft.get_state() == StateRole.Leader


def test_sinle_node_pre_candidate():
    l = default_logger()
    config = Network.default_config()
    config.set_pre_vote(True)
    tt = Network.new_with_config([None], config, l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert tt.peers.get(1).raft.get_state() == StateRole.Leader


def test_old_messages():
    l = default_logger()
    tt = Network.new([None, None, None], l)
    # make 0 leader @ term 3
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    tt.send([new_message(2, 2, MessageType.MsgHup, 0)])
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    # pretend we're an old leader trying to make progress; this entry is expected to be ignored.
    m = new_message(2, 1, MessageType.MsgPropose, 0)
    m.set_term(2)
    m.set_entries([empty_entry(2, 3)])
    tt.send([m])
    # commit a new entry
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    for p in tt.peers.values():
        assert p.raft_log.get_committed() == 4
        assert p.raft_log.get_applied() == 0
        assert p.raft_log.last_index() == 4


# test_old_messages_reply - optimization - reply with new term.


def test_proposal():
    l = default_logger()

    class Test:
        def __init__(self, nw: Network, success: bool) -> None:
            self.nw = nw
            self.success = success

    NOP_STEPPER = Interface(None)

    tests = [
        Test(Network.new([None, None, None], l), True),
        Test(Network.new([None, None, NOP_STEPPER], l), True),
        Test(Network.new([None, NOP_STEPPER, NOP_STEPPER], l), False),
        Test(Network.new([None, NOP_STEPPER, NOP_STEPPER, None], l), False),
        Test(Network.new([None, NOP_STEPPER, NOP_STEPPER, None, None], l), True),
    ]

    for j, v in enumerate(tests):
        nw, success = v.nw, v.success

        def send(nw: Network, m: Message) -> None:
            try:
                nw.send([m])
                assert success
            except Exception:
                assert not success

        # promote 0 the leader
        send(nw, new_message(1, 1, MessageType.MsgHup, 0))
        send(nw, new_message(1, 1, MessageType.MsgPropose, 1))
        # committed index, applied index and last index.
        want_log = (2, 0, 2) if success else (0, 0, 0)

        for p in nw.peers.values():
            if p.raft:
                prefix = f"#{j}: "
                assert_raft_log(
                    prefix, p.raft_log, want_log[0], want_log[1], want_log[2]
                )
        assert (
            nw.peers.get(1).raft.get_term() == 1
        ), f"#{j}: term = {nw.peers.get(1).raft.get_term()}, want: {1}"


def test_proposal_by_proxy():
    l = default_logger()

    NOP_STEPPER = Interface(None)

    tests = [
        Network.new([None, None, None], l),
        Network.new([None, None, NOP_STEPPER], l),
    ]

    for j, tt in enumerate(tests):
        # promote 0 the leader
        tt.send([new_message(1, 1, MessageType.MsgHup, 0)])
        # propose via follower
        tt.send([new_message(2, 2, MessageType.MsgPropose, 1)])

        for p in tt.peers.values():
            if p.raft:
                prefix = f"#{j}: "
                assert_raft_log(prefix, p.raft_log, 2, 0, 2)
        assert (
            tt.peers.get(1).raft.get_term() == 1
        ), f"#{j}: term = {tt.peers.get(1).raft.get_term()}, want: {1}"


def test_commit():
    l = default_logger()

    class Test:
        def __init__(
            self, matches: List[int], logs: List[Entry], sm_term: int, w: int
        ) -> None:
            self.matches = matches
            self.logs = logs
            self.sm_term = sm_term
            self.w = w

    tests = [
        # single
        Test([1], [empty_entry(1, 1)], 1, 1),
        Test([1], [empty_entry(1, 1)], 2, 0),
        Test([2], [empty_entry(1, 1), empty_entry(2, 2)], 2, 2),
        Test([1], [empty_entry(2, 1)], 2, 1),
        # odd
        Test([2, 1, 1], [empty_entry(1, 1), empty_entry(2, 2)], 1, 1),
        Test([2, 1, 1], [empty_entry(1, 1), empty_entry(1, 2)], 2, 0),
        Test([2, 1, 2], [empty_entry(1, 1), empty_entry(2, 2)], 2, 2),
        Test([2, 1, 2], [empty_entry(1, 1), empty_entry(1, 2)], 2, 0),
        # even
        Test([2, 1, 1, 1], [empty_entry(1, 1), empty_entry(2, 2)], 1, 1),
        Test([2, 1, 1, 1], [empty_entry(1, 1), empty_entry(1, 2)], 2, 0),
        Test([2, 1, 1, 2], [empty_entry(1, 1), empty_entry(2, 2)], 1, 1),
        Test([2, 1, 1, 2], [empty_entry(1, 1), empty_entry(1, 2)], 2, 0),
        Test([2, 1, 2, 2], [empty_entry(1, 1), empty_entry(2, 2)], 2, 2),
        Test([2, 1, 2, 2], [empty_entry(1, 1), empty_entry(1, 2)], 2, 0),
    ]

    for i, v in enumerate(tests):
        matches, logs, sm_term, w = v.matches, v.logs, v.sm_term, v.w
        cs = ConfState([1], [])
        store = MemStorage.new_with_conf_state(cs)
        store.wl().append(logs)
        hs = HardState.default()
        hs.set_term(sm_term)
        store.wl().set_hardstate(hs)
        cfg = new_test_config(1, 5, 1)
        sm = new_test_raft_with_config(cfg, store, l)

        for j, v in enumerate(matches):
            id = j + 1
            if not sm.raft.prs().get(id):
                sm.raft.apply_conf_change(add_node(id))
                pr = sm.raft.prs().get(id)
                pr.set_matched(v)
                pr.set_next_idx(v + 1)

        sm.raft.maybe_commit()
        assert (
            sm.raft_log.get_committed() == w
        ), f"#{i}: committed = {sm.raft_log.get_committed()}, want {w}"


def test_pass_election_timeout():
    l = default_logger()

    class Test:
        def __init__(self, elapse: int, wprobability: float, round: bool) -> None:
            self.elapse = elapse
            self.wprobability = wprobability
            self.round = round

    tests = [
        Test(5, 0.0, False),
        Test(10, 0.1, True),
        Test(13, 0.4, True),
        Test(15, 0.6, True),
        Test(18, 0.9, True),
        Test(20, 1.0, False),
    ]

    for i, v in enumerate(tests):
        elapse, wprobability, round = v.elapse, v.wprobability, v.round
        storage = new_storage()
        sm = new_test_raft(1, [1], 10, 1, storage, l)
        sm.raft.set_election_elapsed(elapse)
        c = 0
        for _ in range(0, 10000):
            sm.raft.reset_randomized_election_timeout()
            if sm.raft.pass_election_timeout():
                c += 1
        got = c / 10000.0
        if round:
            got = math.floor(got * 10.0 + 0.5) / 10.0
        if got - wprobability > 0.000001:
            assert False, f"#{i}: probability = {got}, want {wprobability}"


# test_handle_msg_append ensures:
# 1. Reply false if log doesn’t contain an entry at prevLogIndex whose term matches prevLogTerm.
# 2. If an existing entry conflicts with a new one (same index but different terms),
#    delete the existing entry and all that follow it; append any new entries not already in the
#    log.
# 3. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry).
def test_handle_msg_append():
    l = default_logger()

    def nm(
        term: int,
        log_term: int,
        index: int,
        commit: int,
        ents: Optional[List[Tuple[int, int]]],
    ) -> Message:
        m = Message.default()
        m.set_msg_type(MessageType.MsgAppend)
        m.set_term(term)
        m.set_log_term(log_term)
        m.set_index(index)
        m.set_commit(commit)

        if ents:
            m.set_entries(
                cast(
                    List[Entry],
                    list(map(lambda item: empty_entry(item[1], item[0]), ents)),
                )
            )
        return m

    class Test:
        def __init__(
            self, m: Message, w_index: bool, w_commit: int, w_reject: int
        ) -> None:
            self.m = m
            self.w_index = w_index
            self.w_commit = w_commit
            self.w_reject = w_reject

    tests = [
        # Ensure 1: previous log mismatch
        Test(nm(2, 3, 2, 3, None), 2, 0, True),
        # Ensure 1: previous log non-exist
        Test(nm(2, 3, 3, 3, None), 2, 0, True),
        # Ensure 2
        Test(nm(2, 1, 1, 1, None), 2, 1, False),
        Test(nm(2, 0, 0, 1, [(1, 2)]), 1, 1, False),
        Test(nm(2, 2, 2, 3, [(3, 2), (4, 2)]), 4, 3, False),
        Test(nm(2, 2, 2, 4, [(3, 2)]), 3, 3, False),
        Test(nm(2, 1, 1, 4, [(2, 2)]), 2, 2, False),
        # Ensure 3: match entry 1, commit up to last new entry 1
        Test(nm(1, 1, 1, 3, None), 2, 1, False),
        # Ensure 3: match entry 1, commit up to last new
        Test(nm(1, 1, 1, 3, [(2, 2)]), 2, 2, False),
        # entry 2: match entry 2, commit up to last new entry 2
        Test(nm(2, 2, 2, 3, None), 2, 2, False),
        # entry 2: commit up to log.last()
        Test(nm(2, 2, 2, 4, None), 2, 2, False),
    ]

    for j, v in enumerate(tests):
        m, w_index, w_commit, w_reject = v.m, v.w_index, v.w_commit, v.w_reject
        storage = MemStorage()
        sm = new_test_raft_with_logs(
            1,
            [1],
            10,
            1,
            storage,
            [empty_entry(1, 1), empty_entry(2, 2)],
            l,
        )

        sm.raft.become_follower(2, INVALID_ID)
        sm.raft.handle_append_entries(m)

        assert (
            sm.raft_log.last_index() == w_index
        ), f"#{j}: last_index = {sm.raft_log.last_index()}, want {w_index}"

        assert (
            sm.raft_log.get_committed() == w_commit
        ), f"#{j}: committed = {sm.raft_log.get_committed()}, want {w_commit}"

        m = sm.read_messages()
        assert len(m) == 1, f"#{j}: msg count = {len(m)}, want 1"

        assert (
            m[0].get_reject() == w_reject
        ), f"#{j}: reject = {m[0].get_reject()}, want {w_reject}"


# test_handle_heartbeat ensures that the follower commits to the commit in the message.
def test_handle_heartbeat():
    l = default_logger()
    commit = 2

    def nm(
        f: int,
        to: int,
        term: int,
        commit: int,
    ) -> Message:
        m = new_message(f, to, MessageType.MsgHeartbeat, 0)
        m.set_term(term)
        m.set_commit(commit)

        return m

    class Test:
        def __init__(self, m: Message, w_commit: int) -> None:
            self.m = m
            self.w_commit = w_commit

    tests = [
        Test(nm(2, 1, 2, commit + 1), commit + 1),
        Test(nm(2, 1, 2, commit - 1), commit),
    ]

    for i, v in enumerate(tests):
        m, w_commit = v.m, v.w_commit
        cs = ConfState([1, 2], [])
        store = MemStorage.new_with_conf_state(cs)
        store.wl().append(
                [
                    empty_entry(1, 1),
                    empty_entry(2, 2),
                    empty_entry(3, 3),
                ]
            )

        cfg = new_test_config(1, 5, 1)
        sm = new_test_raft_with_config(cfg, store, l)
        sm.raft.become_follower(2, 2)
        sm.raft_log.commit_to(commit)
        sm.raft.handle_heartbeat(m)
        assert (
            sm.raft_log.get_committed() == w_commit
        ), f"#{i}: committed = {sm.raft_log.get_committed()}, want {w_commit}"

        m = sm.read_messages()
        assert len(m) == 1, f"#{i}: msg count = {len(m)}, want 1"
        assert (
            m[0].get_msg_type() == MessageType.MsgHeartbeatResponse
        ), f"#{i}: msg type = {m[0].get_msg_type()}, want {MessageType.MsgHeartbeatResponse}"


# test_handle_heartbeat_resp ensures that we re-send log entries when we get a heartbeat response.
def test_handle_heartbeat_resp():
    l = default_logger()
    store = new_storage()
    store.wl().append(
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(3, 3),
            ]
        )

    sm = new_test_raft(1, [1, 2], 5, 1, store, l)
    sm.raft.become_candidate()
    sm.raft.become_leader()

    last_index = sm.raft_log.last_index()
    sm.raft_log.commit_to(last_index)

    # A heartbeat response from a node that is behind; re-send MsgApp
    sm.step(new_message(2, 0, MessageType.MsgHeartbeatResponse, 0))
    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend

    # A second heartbeat response generates another MsgApp re-send
    sm.step(new_message(2, 0, MessageType.MsgHeartbeatResponse, 0))
    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend

    # Once we have an MsgAppResp, heartbeats no longer send MsgApp.
    m = new_message(2, 0, MessageType.MsgAppendResponse, 0)
    m.set_index(msgs[0].get_index() + len(msgs[0].get_entries()))

    sm.step(m)
    # Consume the message sent in response to MsgAppResp
    sm.read_messages()

    sm.step(new_message(2, 0, MessageType.MsgHeartbeatResponse, 0))
    msgs = sm.read_messages()
    assert not msgs


# test_raft_frees_read_only_mem ensures raft will free read request from
# ReadOnly read_index_queue and pending_read_index map.
# related issue: https://github.com/coreos/etcd/issues/7571
def test_raft_frees_read_only_mem():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 5, 1, storage, l)

    sm.raft.become_candidate()
    sm.raft.become_leader()
    last_index = sm.raft_log.last_index()
    sm.raft_log.commit_to(last_index)

    ctx = "ctx"
    vec_ctx = bytes(ctx, "utf-8")
    # leader starts linearizable read request.
    # more info: raft dissertation 6.4, step 2.
    m = new_message_with_entries(2, 1, MessageType.MsgReadIndex, [new_entry(0, 0, ctx)])
    sm.step(m)
    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgHeartbeat
    assert msgs[0].get_context() == vec_ctx
    assert len(sm.raft.get_readonly_read_index_queue()) == 1
    # TODO: Resolve below tests
    # assert sm.raft.get_read_only_pending_read_index() == 1

    # heartbeat responses from majority of followers (1 in this case)
    # acknowledge the authority of the leader.
    # more info: raft dissertation 6.4, step 3.
    m = new_message(2, 1, MessageType.MsgHeartbeatResponse, 0)
    m.set_context(vec_ctx)
    sm.step(m)
    assert len(sm.raft.get_readonly_read_index_queue()) == 0
    # TODO: Resolve below tests
    # assert sm.raft.get_read_only_pending_read_index() == 0


# test_msg_append_response_wait_reset verifies the waitReset behavior of a leader
# MsgAppResp.
def test_msg_append_response_wait_reset():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2, 3], 5, 1, storage, l)
    sm.raft.become_candidate()
    sm.raft.become_leader()
    # For no-op entry
    sm.persist()
    # The new leader has just emitted a new Term 4 entry; consume those messages
    # from the outgoing queue.
    sm.raft.bcast_append()
    sm.read_messages()

    # Node 2 acks the first entry, making it committed.
    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    m.set_index(1)
    sm.step(m)
    assert sm.raft_log.get_committed() == 1
    # Also consume the MsgApp messages that update Commit on the followers.
    sm.read_messages()

    # A new command is now proposed on node 1.
    m = new_message(1, 1, MessageType.MsgPropose, 0)
    m.set_entries([empty_entry(0, 0)])
    sm.step(m)
    sm.persist()

    # The command is broadcast to all nodes not in the wait state.
    # Node 2 left the wait state due to its MsgAppResp, but node 3 is still waiting.
    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
    assert msgs[0].get_to() == 2
    assert len(msgs[0].get_entries()) == 1
    assert msgs[0].get_entries()[0].get_index() == 2

    # Now Node 3 acks the first entry. This releases the wait and entry 2 is sent.
    m = new_message(3, 0, MessageType.MsgAppendResponse, 0)
    m.set_index(1)
    sm.step(m)
    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
    assert msgs[0].get_to() == 3
    assert len(msgs[0].get_entries()) == 1
    assert msgs[0].get_entries()[0].get_index() == 2


# test_recv_msg_request_vote
@pytest.mark.parametrize("msg_type", [MessageType.MsgRequestVote])
def test_recv_msg_request_vote_for_type(msg_type: MessageType):
    l = default_logger()

    class Test:
        def __init__(
            self,
            state: StateRole,
            index: int,
            log_term: int,
            vote_for: int,
            w_reject: bool,
        ) -> None:
            self.state = state
            self.index = index
            self.log_term = log_term
            self.vote_for = vote_for
            self.w_reject = w_reject

    tests = [
        Test(StateRole.Follower, 0, 0, INVALID_ID, True),
        Test(StateRole.Follower, 0, 1, INVALID_ID, True),
        Test(StateRole.Follower, 0, 2, INVALID_ID, True),
        Test(StateRole.Follower, 0, 3, INVALID_ID, False),
        Test(StateRole.Follower, 1, 0, INVALID_ID, True),
        Test(StateRole.Follower, 1, 1, INVALID_ID, True),
        Test(StateRole.Follower, 1, 2, INVALID_ID, True),
        Test(StateRole.Follower, 1, 3, INVALID_ID, False),
        Test(StateRole.Follower, 2, 0, INVALID_ID, True),
        Test(StateRole.Follower, 2, 1, INVALID_ID, True),
        Test(StateRole.Follower, 2, 2, INVALID_ID, False),
        Test(StateRole.Follower, 2, 3, INVALID_ID, False),
        Test(StateRole.Follower, 3, 0, INVALID_ID, True),
        Test(StateRole.Follower, 3, 1, INVALID_ID, True),
        Test(StateRole.Follower, 3, 2, INVALID_ID, False),
        Test(StateRole.Follower, 3, 3, INVALID_ID, False),
        Test(StateRole.Follower, 3, 2, 2, False),
        Test(StateRole.Follower, 3, 2, 1, True),
        Test(StateRole.Leader, 3, 3, 1, True),
        Test(StateRole.PreCandidate, 3, 3, 1, True),
        Test(StateRole.Candidate, 3, 3, 1, True),
    ]

    for j, v in enumerate(tests):
        state, index, log_term, vote_for, w_reject = (
            v.state,
            v.index,
            v.log_term,
            v.vote_for,
            v.w_reject,
        )
        cs = ConfState([1], [])
        store = MemStorage.new_with_conf_state(cs)
        ents = [empty_entry(2, 1), empty_entry(2, 2)]
        store.wl().append(ents)

        sm = new_test_raft(1, [1], 10, 1, store, l)
        sm.raft.set_state(state)
        sm.raft.set_vote(vote_for)

        m = new_message(2, 0, msg_type, 0)
        m.set_index(index)
        m.set_log_term(log_term)
        # raft.Term is greater than or equal to raft.raftLog.lastTerm. In this
        # test we're only testing MsgVote responses when the campaigning node
        # has a different raft log compared to the recipient node.
        # Additionally we're verifying behaviour when the recipient node has
        # already given out its vote for its current term. We're not testing
        # what the recipient node does when receiving a message with a
        # different term number, so we simply initialize both term numbers to
        # be the same.
        term = max(sm.raft_log.last_term(), log_term)
        m.set_term(term)
        sm.raft.set_term(term)
        sm.step(m)

        msgs = sm.read_messages()
        assert len(msgs) == 1, f"#{j}: msgs count = {len(msgs)}, want 1"

        assert msgs[0].get_msg_type() == vote_resp_msg_type(
            msg_type
        ), f"#{j}: m.type = {msgs[0].get_msg_type()}, want {vote_resp_msg_type(msg_type)}"

        assert (
            msgs[0].get_reject() == w_reject
        ), f"#{j}: m.reject = {msgs[0].get_reject()}, want {w_reject}"


def test_state_transition():
    l = default_logger()

    class Test:
        def __init__(
            self, from_: int, to: StateRole, wallow: bool, wterm: int, wlead: int
        ) -> None:
            self.from_ = from_
            self.to = to
            self.wallow = wallow
            self.wterm = wterm
            self.wlead = wlead

    tests = [
        Test(StateRole.Follower, StateRole.Follower, True, 1, INVALID_ID),
        Test(StateRole.Follower, StateRole.PreCandidate, True, 0, INVALID_ID),
        Test(StateRole.Follower, StateRole.Candidate, True, 1, INVALID_ID),
        Test(StateRole.Follower, StateRole.Leader, False, 0, INVALID_ID),
        Test(StateRole.PreCandidate, StateRole.Follower, True, 0, INVALID_ID),
        Test(StateRole.PreCandidate, StateRole.PreCandidate, True, 0, INVALID_ID),
        Test(StateRole.PreCandidate, StateRole.Candidate, True, 1, INVALID_ID),
        Test(StateRole.PreCandidate, StateRole.Leader, True, 0, 1),
        Test(StateRole.Candidate, StateRole.Follower, True, 0, INVALID_ID),
        Test(StateRole.Candidate, StateRole.PreCandidate, True, 0, INVALID_ID),
        Test(StateRole.Candidate, StateRole.Candidate, True, 1, INVALID_ID),
        Test(StateRole.Candidate, StateRole.Leader, True, 0, 1),
        Test(StateRole.Leader, StateRole.Follower, True, 1, INVALID_ID),
        Test(StateRole.Leader, StateRole.PreCandidate, False, 1, INVALID_ID),
        Test(StateRole.Leader, StateRole.Leader, True, 0, 1),
    ]

    for i, v in enumerate(tests):
        from_, to, wallow, wterm, wlead = v.from_, v.to, v.wallow, v.wterm, v.wlead
        storage = new_storage()
        sm = new_test_raft(1, [1], 10, 1, storage, l)
        sm.raft.set_state(from_)

        is_ok = False

        try:
            if to == StateRole.Follower:
                sm.become_follower(wterm, wlead)
            elif to == StateRole.PreCandidate:
                sm.become_pre_candidate()
            elif to == StateRole.Candidate:
                sm.become_candidate()
            elif to == StateRole.Leader:
                sm.become_leader()

            is_ok = True
        except Exception:
            continue

        assert is_ok ^ wallow, f"#{i}: allow = {is_ok}, want {wallow}"

        assert (
            sm.raft.get_term() == wterm
        ), f"#{i}: state = {sm.raft.get_term()}, want {wterm}"

        assert (
            sm.raft.get_leader_id() == wlead
        ), f"#{i}: state = {sm.raft.get_leader_id()}, want {wlead}"


def test_all_server_stepdown():
    l = default_logger()

    class Test:
        def __init__(
            self,
            state: StateRole,
            wstate: StateRole,
            wterm: int,
            windex: int,
            entries: int,
        ):
            self.state = state
            self.wstate = wstate
            self.wterm = wterm
            self.windex = windex
            self.entries = entries

    tests = [
        # state, want_state, term, last_index, entry count.
        Test(StateRole.Follower, StateRole.Follower, 3, 0, 0),
        Test(StateRole.PreCandidate, StateRole.Follower, 3, 0, 0),
        Test(StateRole.Candidate, StateRole.Follower, 3, 0, 0),
        Test(StateRole.Leader, StateRole.Follower, 3, 1, 1),
    ]

    tmsg_types = [
        MessageType.MsgRequestVote,
        MessageType.MsgAppend,
    ]

    tterm = 3

    for i, v in enumerate(tests):
        state, wstate, wterm, windex, entries = (
            v.state,
            v.wstate,
            v.wterm,
            v.windex,
            v.entries,
        )
        storage = new_storage()
        sm = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)

        if state == StateRole.Follower:
            sm.raft.become_follower(1, INVALID_ID)
        elif state == StateRole.PreCandidate:
            sm.raft.become_pre_candidate()
        elif state == StateRole.Candidate:
            sm.raft.become_candidate()
        elif state == StateRole.Leader:
            sm.raft.become_candidate()
            sm.raft.become_leader()

        for j, msg_type in enumerate(tmsg_types):
            m = new_message(2, 0, msg_type, 0)
            m.set_term(tterm)
            m.set_log_term(tterm)
            sm.step(m)

            assert (
                sm.raft.get_state() == wstate
            ), f"{i}.{j} state = {sm.raft.get_state()}, want {wstate}"

            assert (
                sm.raft.get_term() == wterm
            ), f"{i}.{j} term = {sm.raft.get_term()}, want {wterm}"

            assert (
                sm.raft_log.last_index() == windex
            ), f"{i}.{j} index = {sm.raft_log.last_index()}, want {windex}"

            entry_count = len(sm.raft_log.all_entries())
            assert (
                entry_count == entries
            ), f"{i}.{j} entries = {entry_count}, want {entries}"

            wlead = INVALID_ID if msg_type == MessageType.MsgRequestVote else 2

            assert (
                sm.raft.get_leader_id() == wlead
            ), f"{i}.{j} lead = {sm.raft.get_leader_id()}, want {INVALID_ID}"


# test_candidate_reset_term tests when a candidate receives a
# MsgHeartbeat or MsgAppend from leader, "step" resets the term
# with leader's and reverts back to follower.
#
# test_candidate_reset_term_msg_heartbeat
# test_candidate_reset_term_msg_append
@pytest.mark.parametrize(
    "message_type", [MessageType.MsgHeartbeat, MessageType.MsgAppend]
)
def test_candidate_reset_term(message_type: MessageType):
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_storage, l)
    b_storage = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_storage, l)
    c_storage = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_storage, l)

    nt = Network.new([a, b, c], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    # isolate 3 and increase term in rest
    nt.isolate(3)
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    # trigger campaign in isolated c
    nt.peers.get(3).raft.reset_randomized_election_timeout()
    timeout = nt.peers.get(3).raft.randomized_election_timeout()
    for _ in range(0, timeout):
        nt.peers.get(3).raft.tick()

    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate

    nt.recover()

    # leader sends to isolated candidate
    # and expects candidate to revert to follower
    msg = new_message(1, 3, message_type, 0)
    msg.set_term(nt.peers.get(1).raft.get_term())
    nt.send([msg])

    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    # follower c term is reset with leader's
    assert (
        nt.peers.get(3).raft.get_term() == nt.peers.get(1).raft.get_term()
    ), f"follower term expected same term as leader's {nt.peers.get(1).raft.get_term()}, got {nt.peers.get(3).raft.get_term()}"


def test_leader_stepdown_when_quorum_active():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2, 3], 5, 1, storage, l)
    sm.raft.set_check_quorum(True)
    sm.raft.become_candidate()
    sm.raft.become_leader()

    for _ in range(0, sm.raft.election_timeout()):
        m = new_message(2, 0, MessageType.MsgHeartbeatResponse, 0)
        m.set_term(sm.raft.get_term())
        sm.step(m)
        sm.raft.tick()

    assert sm.raft.get_state() == StateRole.Leader


def test_leader_stepdown_when_quorum_lost():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1, 2, 3], 5, 1, storage, l)
    sm.raft.set_check_quorum(True)
    sm.raft.become_candidate()
    sm.raft.become_leader()

    for _ in range(0, sm.raft.election_timeout()):
        sm.raft.tick()

    assert sm.raft.get_state() == StateRole.Follower


def test_leader_superseding_with_check_quorum():
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_storage, l)
    b_storage = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_storage, l)
    c_storage = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_storage, l)

    a.raft.set_check_quorum(True)
    b.raft.set_check_quorum(True)
    c.raft.set_check_quorum(True)

    nt = Network.new([a, b, c], l)
    b_election_timeout = nt.peers.get(2).raft.election_timeout()

    # prevent campaigning from b
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    # Peer b rejected c's vote since its electionElapsed had not reached to electionTimeout

    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate

    # Letting b's electionElapsed reach to electionTimeout
    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    assert nt.peers.get(3).raft.get_state() == StateRole.Leader


def test_leader_election_with_check_quorum():
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_storage, l)
    b_storage = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_storage, l)
    c_storage = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_storage, l)

    a.raft.set_check_quorum(True)
    b.raft.set_check_quorum(True)
    c.raft.set_check_quorum(True)

    nt = Network.new([a, b, c], l)

    # we can not let system choosing the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    a_election_timeout = nt.peers.get(1).raft.election_timeout()
    b_election_timeout = nt.peers.get(2).raft.election_timeout()
    nt.peers.get(1).raft.set_randomized_election_timeout(a_election_timeout + 1)
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 2)

    # Immediately after creation, votes are cast regardless of the election timeout

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    # need to reset randomizedElectionTimeout larger than electionTimeout again,
    # because the value might be reset to electionTimeout since the last state changes
    a_election_timeout = nt.peers.get(1).raft.election_timeout()
    b_election_timeout = nt.peers.get(2).raft.election_timeout()
    nt.peers.get(1).raft.set_randomized_election_timeout(a_election_timeout + 1)
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 2)

    for _ in range(0, a_election_timeout):
        nt.peers.get(1).raft.tick()

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Leader


# test_free_stuck_candidate_with_check_quorum ensures that a candidate with a higher term
# can disrupt the leader even if the leader still "officially" holds the lease, The
# leader is expected to step down and adopt the candidate's term
def test_free_stuck_candidate_with_check_quorum():
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_storage, l)
    b_storage = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_storage, l)
    c_storage = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_storage, l)

    a.raft.set_check_quorum(True)
    b.raft.set_check_quorum(True)
    c.raft.set_check_quorum(True)

    nt = Network.new([a, b, c], l)

    # we can not let system choosing the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    b_election_timeout = nt.peers.get(2).raft.election_timeout()
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    nt.isolate(1)
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate
    assert nt.peers.get(3).raft.get_term() == nt.peers.get(2).raft.get_term() + 1

    # Vote again for safety
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate
    assert nt.peers.get(3).raft.get_term() == nt.peers.get(2).raft.get_term() + 2

    nt.recover()
    msg = new_message(1, 3, MessageType.MsgHeartbeat, 0)
    msg.set_term(nt.peers.get(3).raft.get_term())
    nt.send([msg])

    # Disrupt the leader so that the stuck peer is freed
    assert nt.peers.get(1).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_term() == nt.peers.get(1).raft.get_term()

    # Vote again, should become leader this time
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    assert nt.peers.get(3).raft.get_state() == StateRole.Leader


def test_non_promotable_voter_with_check_quorum():
    l = default_logger()
    a_storage = new_storage()
    a = new_test_raft(1, [1, 2], 10, 1, a_storage, l)
    b_storage = new_storage()
    b = new_test_raft(2, [1], 10, 1, b_storage, l)

    a.raft.set_check_quorum(True)
    b.raft.set_check_quorum(True)

    nt = Network.new([a, b], l)

    # we can not let system choosing the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    b_election_timeout = nt.peers.get(2).raft.election_timeout()
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    # Need to remove 2 again to make it a non-promotable node since newNetwork
    # overwritten some internal states
    nt.peers.get(1).raft.apply_conf_change(remove_node(2))

    assert not nt.peers.get(2).raft.promotable()

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(1).raft.get_leader_id() == 1


# `test_disruptive_follower` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a candidate with an increased term. Then, the
# candiate's response to late leader heartbeat forces the leader
def test_disruptive_follower():
    l = default_logger()
    n1_storage = new_storage()
    n1 = new_test_raft(1, [1, 2, 3], 10, 1, n1_storage, l)
    n2_storage = new_storage()
    n2 = new_test_raft(2, [1, 2, 3], 10, 1, n2_storage, l)
    n3_storage = new_storage()
    n3 = new_test_raft(3, [1, 2, 3], 10, 1, n3_storage, l)

    n1.raft.set_check_quorum(True)
    n2.raft.set_check_quorum(True)
    n3.raft.set_check_quorum(True)

    n1.raft.become_follower(1, INVALID_ID)
    n2.raft.become_follower(1, INVALID_ID)
    n3.raft.become_follower(1, INVALID_ID)

    nt = Network.new([n1, n2, n3], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # check state
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    # etcd server "advanceTicksForElection" on restart;
    # this is to expedite campaign trigger when given larger
    # election timeouts (e.g. multi-datacenter deploy)
    # Or leader messages are being delayed while ticks elapse
    timeout = nt.peers.get(3).raft.election_timeout()
    nt.peers.get(3).raft.set_randomized_election_timeout(timeout + 2)
    timeout = nt.peers.get(3).raft.randomized_election_timeout()

    for _ in range(0, timeout - 1):
        nt.peers.get(3).raft.tick()

    # ideally, before last election tick elapses,
    # the follower n3 receives "pb.MsgApp" or "pb.MsgHeartbeat"
    # from leader n1, and then resets its "electionElapsed"
    # however, last tick may elapse before receiving any
    # messages from leader, thus triggering campaign
    nt.peers.get(3).raft.tick()

    # n1 is still leader yet
    # while its heartbeat to candidate n3 is being delayed
    # check state
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate

    # check term
    # n1.Term == 2
    # n2.Term == 2
    # n3.Term == 3
    assert nt.peers.get(1).raft.get_term() == 2
    assert nt.peers.get(2).raft.get_term() == 2
    assert nt.peers.get(3).raft.get_term() == 3

    # while outgoing vote requests are still queued in n3,
    # leader heartbeat finally arrives at candidate n3
    # however, due to delayed network from leader, leader
    # heartbeat was sent with lower term than candidate's
    msg = new_message(1, 3, MessageType.MsgHeartbeat, 0)
    msg.set_term(2)
    nt.send([msg])

    # then candidate n3 responds with "pb.MsgAppResp" of higher term
    # and leader steps down from a message with higher term
    # this is to disrupt the current leader, so that candidate
    # with higher term can be freed with following election

    # check state
    assert nt.peers.get(1).raft.get_state() == StateRole.Follower
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Candidate

    # check term
    # n1.Term == 3
    # n2.Term == 2
    # n3.Term == 3
    assert nt.peers.get(1).raft.get_term() == 3
    assert nt.peers.get(2).raft.get_term() == 2
    assert nt.peers.get(3).raft.get_term() == 3


# `test_disruptive_follower_pre_vote` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a pre-candidate with less log than current leader.
# Then pre-vote phase prevents this isolated node from forcing
# current leader to step down, thus less disruptions.
def test_disruptive_follower_pre_vote():
    l = default_logger()
    n1_storage = new_storage()
    n1 = new_test_raft_with_prevote(1, [1, 2, 3], 10, 1, n1_storage, True, l)
    n2_storage = new_storage()
    n2 = new_test_raft_with_prevote(2, [1, 2, 3], 10, 1, n2_storage, True, l)
    n3_storage = new_storage()
    n3 = new_test_raft_with_prevote(3, [1, 2, 3], 10, 1, n3_storage, True, l)

    n1.raft.set_check_quorum(True)
    n2.raft.set_check_quorum(True)
    n3.raft.set_check_quorum(True)

    n1.raft.become_follower(1, INVALID_ID)
    n2.raft.become_follower(1, INVALID_ID)
    n3.raft.become_follower(1, INVALID_ID)

    nt = Network.new([n1, n2, n3], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # check state
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.Follower

    nt.isolate(3)
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    nt.recover()
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # check state
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower
    assert nt.peers.get(3).raft.get_state() == StateRole.PreCandidate

    # check term
    # n1.Term == 2
    # n2.Term == 2
    # n3.Term == 2
    assert nt.peers.get(1).raft.get_term() == 2
    assert nt.peers.get(2).raft.get_term() == 2
    assert nt.peers.get(3).raft.get_term() == 2

    # delayed leader heartbeat does not force current leader to step down
    msg = new_message(1, 3, MessageType.MsgHeartbeat, 0)
    msg.set_term(nt.peers.get(1).raft.get_term())
    nt.send([msg])
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader


def test_read_only_option_safe():
    l = default_logger()

    storage_a = new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, storage_a, l)
    storage_b = new_storage()
    b = new_test_raft(2, [1, 2, 3], 10, 1, storage_b, l)
    storage_c = new_storage()
    c = new_test_raft(3, [1, 2, 3], 10, 1, storage_c, l)

    nt = Network.new([a, b, c], l)

    # we can not let system choose the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    b_election_timeout = nt.peers[2].raft.election_timeout()
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    class Test:
        def __init__(
            self, id: int, proposals: int, wri: int, wctx: List[str], pending: bool
        ) -> None:
            self.id = id
            self.proposals = proposals
            self.wri = wri
            self.wctx = wctx
            self.pending = pending

    tests = [
        Test(1, 10, 11, ["ctx1", "ctx11"], False),
        Test(2, 10, 21, ["ctx2", "ctx22"], False),
        Test(3, 10, 31, ["ctx3", "ctx33"], False),
        Test(1, 10, 41, ["ctx4", "ctx44"], True),
        Test(2, 10, 51, ["ctx5", "ctx55"], True),
        Test(3, 10, 61, ["ctx6", "ctx66"], True),
    ]

    for i, v in enumerate(tests):
        id, proposals, wri, wctx, pending = v.id, v.proposals, v.wri, v.wctx, v.pending
        for _ in range(0, proposals):
            nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

        msg1 = new_message_with_entries(
            id, id, MessageType.MsgReadIndex, [new_entry(0, 0, wctx[0])]
        )

        msg2 = new_message_with_entries(
            id, id, MessageType.MsgReadIndex, [new_entry(0, 0, wctx[1])]
        )

        # `pending` indicates that a `ReadIndex` request will not get through quorum checking immediately
        # so that it remains in the `read_index_queue`
        if pending:
            nt.ignore(MessageType.MsgHeartbeatResponse)
            nt.send([msg1.clone(), msg1.clone(), msg2.clone()])
            nt.recover()
            # send a ReadIndex request with the last ctx to notify leader to handle pending read requests
            nt.send([msg2.clone()])
        else:
            nt.send([msg1.clone(), msg1.clone(), msg2.clone()])

        read_states = nt.peers.get(id).raft.get_read_states()
        nt.peers.get(id).raft.set_read_states([])

        assert read_states, f"#{i}: read_states is empty, want non-empty"

        assert len(read_states) == len(wctx)

        for rs, wctx in zip(read_states, wctx):
            assert (
                rs.get_index() == wri
            ), f"#{i}: read_index = {rs.get_index()}, want {wri}"

            ctx_bytes = wctx.encode("utf-8")
            assert (
                rs.get_request_ctx() == ctx_bytes
            ), f"#{i}: request_ctx = {rs.get_request_ctx()}, want {ctx_bytes}"


def test_read_only_with_learner():
    l = default_logger()
    a_s, b_s = new_storage(), new_storage()
    a = new_test_learner_raft(1, [1], [2], 10, 1, a_s, l)
    b = new_test_learner_raft(2, [1], [2], 10, 1, b_s, l)

    nt = Network.new([a, b], l)

    # we can not system choose the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    b_election_timeout = nt.peers[2].raft.election_timeout()
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers[1].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.get_state() == StateRole.Follower

    class Test:
        def __init__(self, id: int, proposals: int, wri: int, wctx: str) -> None:
            self.id = id
            self.proposals = proposals
            self.wri = wri
            self.wctx = wctx

    tests = [
        Test(1, 10, 11, "ctx1"),
        Test(2, 10, 21, "ctx2"),
        Test(1, 10, 31, "ctx3"),
        Test(2, 10, 41, "ctx4"),
    ]

    for i, v in enumerate(tests):
        id, proposals, wri, wctx = v.id, v.proposals, v.wri, v.wctx

        for _ in range(0, proposals):
            nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

        e = new_entry(0, 0, wctx)
        nt.send(
            [
                new_message_with_entries(
                    id,
                    id,
                    MessageType.MsgReadIndex,
                    [e],
                )
            ]
        )

        read_states = nt.peers.get(id).raft.get_read_states()
        nt.peers.get(id).raft.set_read_states([])

        assert not nt.peers.get(
            id
        ).raft.get_read_states(), f"#{i}: read_states is not empty, want empty"
        rs = read_states[0]

        assert rs.get_index() == wri, f"#{i}: read_index = {rs.get_index()}, want {wri}"

        vec_wctx = wctx

        assert rs.get_request_ctx() == vec_wctx.encode(
            "utf-8"
        ), f"#{i}: request_ctx = {rs.get_request_ctx()}, want {vec_wctx}"


def test_read_only_option_lease():
    l = default_logger()
    a_s, b_s, c_s = new_storage(), new_storage(), new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_s, l)
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_s, l)
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_s, l)

    a.raft.set_read_only_option(ReadOnlyOption.LeaseBased)
    b.raft.set_read_only_option(ReadOnlyOption.LeaseBased)
    c.raft.set_read_only_option(ReadOnlyOption.LeaseBased)

    a.raft.set_check_quorum(True)
    b.raft.set_check_quorum(True)
    c.raft.set_check_quorum(True)

    nt = Network.new([a, b, c], l)

    # we can not let system choose the value of randomizedElectionTimeout
    # otherwise it will introduce some uncertainty into this test case
    # we need to ensure randomizedElectionTimeout > electionTimeout here
    b_election_timeout = nt.peers[2].raft.election_timeout()
    nt.peers.get(2).raft.set_randomized_election_timeout(b_election_timeout + 1)

    for _ in range(0, b_election_timeout):
        nt.peers.get(2).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers[1].raft.get_state() == StateRole.Leader

    class Test:
        def __init__(self, id: int, proposals: int, wri: int, wctx: str) -> None:
            self.id = id
            self.proposals = proposals
            self.wri = wri
            self.wctx = wctx

    tests = [
        Test(1, 10, 11, "ctx1"),
        Test(2, 10, 21, "ctx2"),
        Test(3, 10, 31, "ctx3"),
        Test(1, 10, 41, "ctx4"),
        Test(2, 10, 51, "ctx5"),
        Test(3, 10, 61, "ctx6"),
    ]

    for i, v in enumerate(tests):
        id, proposals, wri, wctx = v.id, v.proposals, v.wri, v.wctx

        for _ in range(0, proposals):
            nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

        entry = new_entry(0, 0, wctx)
        nt.send(
            [
                new_message_with_entries(
                    id,
                    id,
                    MessageType.MsgReadIndex,
                    [entry],
                )
            ]
        )

        read_states = nt.peers.get(id).raft.get_read_states()
        nt.peers.get(id).raft.set_read_states([])

        assert read_states, f"#{i}: read_states is empty, want non-empty"

        rs = read_states[0]

        assert rs.get_index() == wri, f"#{i}: read_index = {rs.get_index()}, want {wri}"

        vec_wctx = wctx.encode("utf-8")

        assert (
            rs.get_request_ctx() == vec_wctx
        ), f"#{i}: request_ctx = {rs.get_request_ctx()}, want {vec_wctx}"


def test_read_only_option_lease_without_check_quorum():
    l = default_logger()
    a_s, b_s, c_s = new_storage(), new_storage(), new_storage()
    a = new_test_raft(1, [1, 2, 3], 10, 1, a_s, l)
    b = new_test_raft(2, [1, 2, 3], 10, 1, b_s, l)
    c = new_test_raft(3, [1, 2, 3], 10, 1, c_s, l)

    a.raft.set_read_only_option(ReadOnlyOption.LeaseBased)
    b.raft.set_read_only_option(ReadOnlyOption.LeaseBased)
    c.raft.set_read_only_option(ReadOnlyOption.LeaseBased)

    nt = Network.new([a, b, c], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    ctx = "ctx1"
    entry = new_entry(0, 0, ctx)
    nt.send(
        [
            new_message_with_entries(
                2,
                2,
                MessageType.MsgReadIndex,
                [entry],
            )
        ]
    )

    read_states = nt.peers[2].raft.get_read_states()
    nt.peers[2].raft.set_read_states([])
    assert read_states
    rs = read_states[0]
    assert rs.get_index() == 1
    vec_ctx = ctx.encode("utf-8")
    assert rs.get_request_ctx() == vec_ctx


# `test_read_only_for_new_leader` ensures that a leader only accepts MsgReadIndex message
# when it commits at least one log entry at it term.
def test_read_only_for_new_leader():
    l = default_logger()
    heartbeat_ticks = 1
    node_configs = [(1, 1, 1, 0), (2, 2, 2, 2), (3, 2, 2, 2)]
    peers = []

    class Test:
        def __init__(
            self, id: int, committed: int, applied: int, compact_index: int
        ) -> None:
            self.id = id
            self.committed = committed
            self.applied = applied
            self.compact_index = compact_index

    node_configs = [Test(1, 1, 1, 0), Test(2, 2, 2, 2), Test(3, 2, 2, 2)]

    for v in node_configs:
        id, committed, applied, compact_index = (
            v.id,
            v.committed,
            v.applied,
            v.compact_index,
        )

        cfg = new_test_config(id, 10, heartbeat_ticks)
        cfg.set_applied(applied)

        storage = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
        entries = [empty_entry(1, 1), empty_entry(1, 2)]
        storage.wl().append(entries)
        hs = HardState.default()
        hs.set_term(1)
        hs.set_commit(committed)
        storage.wl().set_hardstate(hs)

        if compact_index != 0:
            storage.wl().compact(compact_index)

        i = new_test_raft_with_config(cfg, storage, l)
        peers.append(i)

    nt = Network.new(peers, l)

    # Drop MsgAppend to forbid peer 1 to commit any log entry at its term
    # after it becomes leader.
    nt.ignore(MessageType.MsgAppend)
    # Force peer 1 to become leader
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers[1].raft.get_state() == StateRole.Leader

    # Ensure peer 1 drops read only request.
    windex = 4
    wctx = "ctx"
    nt.send(
        [
            new_message_with_entries(
                1,
                1,
                MessageType.MsgReadIndex,
                [new_entry(0, 0, wctx)],
            )
        ]
    )

    assert not nt.peers[1].raft.get_read_states()
    nt.recover()

    # Force peer 1 to commit a log entry at its term.
    for _ in range(0, heartbeat_ticks):
        nt.peers.get(1).raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    assert nt.peers[1].raft_log.get_committed() == 4

    commit = nt.peers[1].raft_log.term(nt.peers[1].raft_log.get_committed())
    assert commit == nt.peers[1].raft.get_term()

    # Ensure peer 1 accepts read only request after it commits a entry at its term.
    nt.send(
        [
            new_message_with_entries(
                1,
                1,
                MessageType.MsgReadIndex,
                [new_entry(0, 0, wctx)],
            )
        ]
    )

    read_states = nt.peers.get(1).raft.get_read_states()
    assert len(read_states) == 1
    rs = read_states[0]
    assert rs.get_index() == windex
    assert rs.get_request_ctx() == wctx.encode("utf-8")


# `test_advance_commit_index_by_read_index_response` ensures that read index response
# can advance the follower's commit index if it has new enough logs
def test_advance_commit_index_by_read_index_response():
    l = default_logger()
    tt = Network.new([None, None, None, None, None], l)
    tt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # don't commit entries
    tt.cut(1, 3)
    tt.cut(1, 4)
    tt.cut(1, 5)
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    tt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    tt.recover()
    tt.cut(1, 2)

    # commit entries for leader but not node 2
    tt.send([new_message(3, 1, MessageType.MsgReadIndex, 1)])
    assert tt.peers[1].raft_log.get_committed() == 3
    assert tt.peers[2].raft_log.get_committed() == 1

    tt.recover()
    # use LeaseBased so leader won't send MsgHeartbeat to advance node 2's commit index
    tt.peers.get(1).raft.set_read_only_option(ReadOnlyOption.LeaseBased)
    tt.send([new_message(2, 1, MessageType.MsgReadIndex, 1)])
    assert tt.peers[2].raft_log.get_committed() == 3


def test_leader_append_response():
    l = default_logger()
    # Initial progress: match = 0, next = 4 on followers.

    class Test:
        def __init__(
            self,
            index: int,
            reject: bool,
            wmatch: int,
            wnext: int,
            wmsg_num: int,
            windex: int,
            wcommitted: int,
        ) -> None:
            self.index = index
            self.reject = reject
            self.wmatch = wmatch
            self.wnext = wnext
            self.wmsg_num = wmsg_num
            self.windex = windex
            self.wcommitted = wcommitted

    tests = [
        # Stale resp; no replies.
        Test(3, True, 0, 3, 0, 0, 0),
        # Denied resp; decrease next and send probing message.
        Test(2, True, 0, 2, 1, 1, 0),
        # Accepted resp; leader commits; broadcast with committed index.
        Test(2, False, 2, 4, 2, 2, 2),
        Test(0, False, 0, 3, 0, 0, 0),
    ]

    for i, v in enumerate(tests):
        index, reject, wmatch, wnext, wmsg_num, windex, wcommitted = (
            v.index,
            v.reject,
            v.wmatch,
            v.wnext,
            v.wmsg_num,
            v.windex,
            v.wcommitted,
        )
        # Initial raft logs: last index = 3, committed = 1.
        cs = ConfState([1, 2, 3], [])
        store = MemStorage.new_with_conf_state(cs)
        ents = [empty_entry(0, 1), empty_entry(1, 2)]
        store.wl().append(ents)
        sm = new_test_raft(1, [1, 2, 3], 10, 1, store, l)
        # sm term is 2 after it becomes the leader.

        sm.raft.become_candidate()
        sm.raft.become_leader()
        sm.read_messages()

        m = new_message(2, 0, MessageType.MsgAppendResponse, 0)
        m.set_index(index)
        m.set_term(sm.raft.get_term())
        m.set_reject(reject)
        m.set_reject_hint(index)
        sm.step(m)

        assert (
            sm.raft.prs().get(2).get_matched() == wmatch
        ), f"#{i}: match = {sm.raft.prs().get(2).get_matched()}, want {wmatch}"

        assert (
            sm.raft.prs().get(2).get_next_idx() == wnext
        ), f"#{i}: match = {sm.raft.prs().get(2).get_next_idx()}, want {wnext}"

        msgs = sm.read_messages()
        assert len(msgs) == wmsg_num, f"#{i} msg_num = {len(msgs)}, want {wmsg_num}"

        for j, msg in enumerate(msgs):
            assert (
                msg.get_index() == windex
            ), f"#{i}.{j} index = {msg.get_index()}, want {windex}"

            assert (
                msg.get_commit() == wcommitted
            ), f"#{i}.{j} commit = {msg.get_committed()}, want {wcommitted}"


# When the leader receives a heartbeat tick, it should
# send a MsgApp with m.Index = 0, m.LogTerm=0 and empty entries.
def test_bcast_beat():
    l = default_logger()
    # make a state machine with log.offset = 1000
    offset = 1000
    s = new_snapshot(offset, 1, [1, 2, 3])
    store = new_storage()
    store.wl().apply_snapshot(s)
    sm = new_test_raft(1, [1, 2, 3], 10, 1, store, l)
    sm.raft.set_term(1)

    sm.raft.become_candidate()
    sm.raft.become_leader()
    for i in range(0, 10):
        sm.raft.append_entry([empty_entry(0, offset + i + 1)])
    sm.persist()

    # slow follower
    def mut_pr(sm: Interface, n: int, matched: int, next_idx: int):
        m = sm.raft.prs().get(n)
        m.set_matched(matched)
        m.set_next_idx(next_idx)

    # slow follower
    mut_pr(sm, 2, offset + 5, offset + 6)
    # normal follower
    last_index = sm.raft_log.last_index()
    mut_pr(sm, 3, last_index, last_index + 1)

    sm.step(new_message(0, 0, MessageType.MsgBeat, 0))
    msgs = sm.read_messages()
    assert len(msgs) == 2

    want_commit_map = {}
    want_commit_map[2] = min(
        sm.raft_log.get_committed(), sm.raft.prs().get(2).get_matched()
    )
    want_commit_map[3] = min(
        sm.raft_log.get_committed(), sm.raft.prs().get(3).get_matched()
    )
    for i, m in enumerate(msgs):
        assert (
            m.get_msg_type() == MessageType.MsgHeartbeat
        ), f"#{i}: type = {m.get_msg_type()}, want = {MessageType.MsgHeartbeat}"

        assert m.get_index() == 0, f"#{i}: prev_index = {m.get_index()}, want = 0"

        assert want_commit_map[m.get_to()] != 0, f"#{i}: unexpected to {m.get_to()}"

        assert (
            m.get_commit() == want_commit_map[m.get_to()]
        ), f"#{i}: commit = {m.get_commit()}, want {want_commit_map[m.get_to()]}"

        want_commit_map.pop(m.get_to())

        assert not (
            m.get_entries()
        ), f"#{i}: entries count = {len(m.get_entries())}, want 0"


# tests the output of the statemachine when receiving MsgBeat
def test_recv_msg_beat():
    l = default_logger()

    class Test:
        def __init__(self, state: StateRole, w_msg: int) -> None:
            self.state = state
            self.w_msg = w_msg

    tests = [
        Test(StateRole.Leader, 2),
        # candidate and follower should ignore MsgBeat
        Test(StateRole.Candidate, 0),
        Test(StateRole.Follower, 0),
    ]

    for i, v in enumerate(tests):
        state, w_msg = v.state, v.w_msg
        cs = ConfState([1, 2, 3], [])
        store = MemStorage.new_with_conf_state(cs)
        ents = [empty_entry(0, 1), empty_entry(1, 2)]
        store.wl().append(ents)

        sm = new_test_raft(1, [1, 2, 3], 10, 1, store, l)
        sm.raft.set_state(state)
        sm.step(new_message(1, 1, MessageType.MsgBeat, 0))

        msgs = sm.read_messages()
        assert len(msgs) == w_msg, f"#{i}: msg count = {len(msgs)}, want {w_msg}"

        for m in msgs:
            assert (
                m.get_msg_type() == MessageType.MsgHeartbeat
            ), f"#{i}: msg.type = {m.get_msg_type()}, want {MessageType.MsgHeartbeat}"


def test_leader_increase_next():
    l = default_logger()
    previous_ents = [empty_entry(1, 1), empty_entry(1, 2), empty_entry(1, 3)]

    class Test:
        def __init__(self, state: ProgressState, next_idx: int, wnext: int) -> None:
            self.state = state
            self.next_idx = next_idx
            self.wnext = wnext

    tests = [
        # state replicate; optimistically increase next
        # previous entries + noop entry + propose + 1
        Test(ProgressState.Replicate, 2, len(previous_ents) + 1 + 1 + 1),
        # state probe, not optimistically increase next
        Test(ProgressState.Probe, 2, 2),
    ]

    for i, v in enumerate(tests):
        state, next_idx, wnext = v.state, v.next_idx, v.wnext
        storage = new_storage()
        sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
        sm.raft_log.append(previous_ents)
        sm.persist()
        sm.raft.become_candidate()
        sm.raft.become_leader()
        sm.raft.prs().get(2).set_state(state)
        sm.raft.prs().get(2).set_next_idx(next_idx)
        sm.step(new_message(1, 1, MessageType.MsgPropose, 1))

        assert (
            sm.raft.prs().get(2).get_next_idx() == wnext
        ), f"#{i}: next = {sm.raft.prs().get(2).get_next_idx()}, want {wnext}"


def test_send_append_for_progress_probe():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2], 10, 1, storage, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    r.read_messages()
    r.raft.prs().get(2).become_probe()

    # each round is a heartbeat
    for i in range(0, 3):
        if i == 0:
            # we expect that raft will only send out one msgAPP on the first
            # loop. After that, the follower is paused until a heartbeat response is
            # received.
            r.raft.append_entry([new_entry(0, 0, SOME_DATA)])
            r.raft.send_append(2)
            msg = r.read_messages()
            assert len(msg) == 1
            assert msg[0].get_index() == 0

        assert r.raft.prs().get(2).get_paused()
        for _ in range(0, 10):
            r.raft.append_entry([new_entry(0, 0, SOME_DATA)])
            r.raft.send_append(2)
            assert not r.read_messages()

        # do a heartbeat
        for _ in range(0, r.raft.heartbeat_timeout()):
            r.step(new_message(1, 1, MessageType.MsgBeat, 0))

        assert r.raft.prs().get(2).get_paused()

        # consume the heartbeat
        msg = r.read_messages()
        assert len(msg) == 1
        assert msg[0].get_msg_type() == MessageType.MsgHeartbeat

    # a heartbeat response will allow another message to be sent
    r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
    msg = r.read_messages()
    assert len(msg) == 1
    assert msg[0].get_index() == 0
    assert r.raft.prs().get(2).get_paused()


def test_send_append_for_progress_replicate():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2], 10, 1, storage, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    r.read_messages()
    r.raft.prs().get(2).become_replicate()

    for _ in range(0, 10):
        r.raft.append_entry([new_entry(0, 0, SOME_DATA)])
        r.raft.send_append(2)
        assert len(r.read_messages()) == 1


def test_send_append_for_progress_snapshot():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2], 10, 1, storage, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    r.read_messages()
    r.raft.prs().get(2).become_snapshot(10)

    for _ in range(0, 10):
        r.raft.append_entry([new_entry(0, 0, SOME_DATA)])
        r.raft.send_append(2)
        assert not r.read_messages()


def test_recv_msg_unreachable():
    l = default_logger()
    previous_ents = [empty_entry(1, 1), empty_entry(1, 2), empty_entry(1, 3)]
    s = new_storage()
    s.wl().append(previous_ents)
    r = new_test_raft(1, [1, 2], 10, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    r.read_messages()
    # set node 2 to state replicate
    r.raft.prs().get(2).set_matched(3)
    r.raft.prs().get(2).become_replicate()
    r.raft.prs().get(2).optimistic_update(5)

    r.step(new_message(2, 1, MessageType.MsgUnreachable, 0))

    peer_2 = r.raft.prs().get(2)
    assert peer_2.get_state() == ProgressState.Probe
    assert peer_2.get_matched() + 1 == peer_2.get_next_idx()


def test_restore():
    l = default_logger()
    # magic number
    s = new_snapshot(11, 11, [1, 2, 3])

    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(s.clone())
    assert sm.raft_log.last_index() == s.get_metadata().get_index()
    assert sm.raft_log.term(s.get_metadata().get_index()) == s.get_metadata().get_term()

    assert sm.raft.prs().conf_voters().ids() == set(
        s.get_metadata().get_conf_state().get_voters()
    )

    assert not sm.raft.restore(s)


def test_restore_ignore_snapshot():
    l = default_logger()
    previous_ents = [empty_entry(1, 1), empty_entry(1, 2), empty_entry(1, 3)]
    commit = 1
    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft_log.append(previous_ents)
    sm.raft_log.commit_to(commit)

    s = new_snapshot(commit, 1, [1, 2])

    # ingore snapshot
    assert not sm.raft.restore(s)
    assert sm.raft_log.get_committed() == commit

    # ignore snapshot and fast forward commit
    s.get_metadata().set_index(commit + 1)
    assert not sm.raft.restore(s)
    assert sm.raft_log.get_committed() == commit + 1


def test_provide_snap():
    l = default_logger()
    # restore the state machine from a snapshot so it has a compacted log and a snapshot
    s = new_snapshot(11, 11, [1, 2])

    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    sm.raft.restore(s.clone())
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    # force set the next of node 2, so that node 2 needs a snapshot
    sm.raft.prs().get(2).set_next_idx(sm.raft_log.first_index())
    m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    m.set_index(sm.raft.prs().get(2).get_next_idx() - 1)
    m.set_reject(True)
    sm.step(m)

    msgs = sm.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgSnapshot


def test_ignore_providing_snapshot():
    l = default_logger()
    # restore the state machine from a snapshot so it has a compacted log and a snapshot
    s = new_snapshot(11, 11, [1, 2])
    storage = new_storage()
    sm = new_test_raft(1, [1], 10, 1, storage, l)
    sm.raft.restore(s)
    sm.persist()

    sm.raft.become_candidate()
    sm.raft.become_leader()

    # force set the next of node 2, so that node 2 needs a snapshot
    # change node 2 to be inactive, expect node 1 ignore sending snapshot to 2
    sm.raft.prs().get(2).set_next_idx(sm.raft_log.first_index() - 1)
    sm.raft.prs().get(2).set_recent_active(False)

    sm.step(new_message(1, 1, MessageType.MsgAppendResponse, 1))

    assert not sm.read_messages()


def test_restore_from_snap_msg():
    l = default_logger()
    s = new_snapshot(11, 11, [1, 2])
    storage = new_storage()
    sm = new_test_raft(2, [1, 2], 10, 1, storage, l)
    m = new_message(1, 0, MessageType.MsgSnapshot, 0)
    m.set_term(2)
    m.set_snapshot(s)

    sm.step(m)

    assert sm.raft.get_leader_id() == 1

    # raft-rs's TODO: port the remaining if upstream completed this test.


def test_slow_node_restore():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    nt.isolate(3)
    for _ in range(0, 100):
        nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    next_ents(nt.peers.get(1).raft, nt.storage.get(1))

    nt.storage.get(1).wl().commit_to(nt.peers.get(1).raft_log.get_applied())
    nt.storage.get(1).wl().compact(nt.peers.get(1).raft_log.get_applied())

    nt.recover()

    # send heartbeats so that the leader can learn everyone is active.
    # node 3 will only be considered as active when node 1 receives a reply from it.
    while True:
        nt.send([new_message(1, 1, MessageType.MsgBeat, 0)])
        if nt.peers.get(1).raft.prs().get(3).get_recent_active():
            break

    # trigger a snapshot
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    # trigger a commit
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    assert (
        nt.peers.get(3).raft_log.get_committed()
        == nt.peers.get(1).raft_log.get_committed()
    )


# test_step_config tests that when raft step msgProp in EntryConfChange type,
# it appends the entry to log and sets pendingConf to be true.
def test_step_config():
    l = default_logger()
    # a raft that cannot make progress
    s = new_storage()
    r = new_test_raft(1, [1, 2], 10, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    index = r.raft_log.last_index()
    m = new_message(1, 1, MessageType.MsgPropose, 0)
    e = Entry.default()
    e.set_entry_type(EntryType.EntryConfChange)
    m.set_entries([*m.get_entries(), e])
    r.step(m)
    assert r.raft_log.last_index() == index + 1


# test_step_ignore_config tests that if raft step the second msgProp in
# EntryConfChange type when the first one is uncommitted, the node will set
# the proposal to noop and keep its original state.
def test_step_ignore_config():
    l = default_logger()
    s = new_storage()
    # a raft that cannot make progress
    r = new_test_raft(1, [1, 2], 10, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    assert not r.raft.has_pending_conf()
    m = new_message(1, 1, MessageType.MsgPropose, 0)
    e = Entry.default()
    e.set_entry_type(EntryType.EntryConfChange)
    m.set_entries([*m.get_entries(), e])
    assert not r.raft.has_pending_conf()
    r.step(m)
    assert r.raft.has_pending_conf()
    index = r.raft_log.last_index()
    pending_conf_index = r.raft.get_pending_conf_index()
    r.step(m)
    we = empty_entry(1, 3)
    we.set_entry_type(EntryType.EntryNormal)
    wents = [we]
    ctx = GetEntriesContext.empty(False)
    entries = r.raft_log.entries(index + 1, ctx.make_ref(), None)
    assert entries == wents
    assert r.raft.get_pending_conf_index() == pending_conf_index


# test_new_leader_pending_config tests that new leader sets its pending_conf_index
# based on uncommitted entries.
def test_new_leader_pending_config():
    l = default_logger()

    class Test:
        def __init__(self, add_entry: bool, wpending_index: int):
            self.add_entry = add_entry
            self.wpending_index = wpending_index

    tests = [
        Test(False, 0),
        Test(True, 1),
    ]

    for i, v in enumerate(tests):
        add_entry, wpending_index = v.add_entry, v.wpending_index
        storage = new_storage()
        r = new_test_raft(1, [1, 2], 10, 1, storage, l)
        e = Entry.default()
        if add_entry:
            e.set_entry_type(EntryType.EntryNormal)
            r.raft.append_entry([e])
            r.persist()
        r.raft.become_candidate()
        r.raft.become_leader()

        assert (
            r.raft.get_pending_conf_index() == wpending_index
        ), f"#{i}: pending_conf_index = {r.raft.get_pending_conf_index}, want {wpending_index}"

        assert r.raft.has_pending_conf() == add_entry, f"#{i}: "


# test_add_node tests that add_node could update nodes correctly.
def test_add_node():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1], 10, 1, storage, l)
    r.raft.apply_conf_change(add_node(2))
    assert r.raft.prs().conf_voters().ids() == {1, 2}


def test_add_node_check_quorum():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1], 10, 1, storage, l)
    r.raft.set_check_quorum(True)
    r.raft.become_candidate()
    r.raft.become_leader()
    for _ in range(0, r.raft.election_timeout() - 1):
        r.raft.tick()

    r.raft.apply_conf_change(add_node(2))

    # This tick will reach electionTimeout, which triggers a quorum check.
    r.raft.tick()

    # Node 1 should still be the leader after a single tick.
    assert r.raft.get_state() == StateRole.Leader

    # After another electionTimeout ticks without hearing from node 2,
    # node 1 should step down.
    for _ in range(0, r.raft.election_timeout()):
        r.raft.tick()

    assert r.raft.get_state() == StateRole.Follower


# test_remove_node tests that removeNode could update pendingConf, nodes and
# and removed list correctly.
def test_remove_node():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2], 10, 1, storage, l)
    r.raft.apply_conf_change(remove_node(2))

    assert r.raft.prs().conf_voters().ids() == {1}

    # Removing all voters is not allowed.
    with pytest.raises(ConfChangeError):
        r.raft.apply_conf_change(remove_node(1))

    assert r.raft.prs().conf_voters().ids() == {1}


def test_remove_node_itself():
    l = default_logger()
    storage = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, storage, l)

    with pytest.raises(ConfChangeError):
        n1.raft.apply_conf_change(remove_node(1))

    assert n1.raft.prs().conf_learners() == {2}
    assert n1.raft.prs().conf_voters().ids() == {1}


def test_promotable():
    l = default_logger()
    id = 1

    class Test:
        def __init__(self, peers: List[int], wp: bool):
            self.peers = peers
            self.wp = wp

    tests = [
        Test([1], True),
        Test([1, 2, 3], True),
        Test([], False),
        Test([2, 3], False),
    ]

    for i, v in enumerate(tests):
        peers, wp = v.peers, v.wp
        storage = new_storage()
        r = new_test_raft(id, peers, 5, 1, storage, l)
        assert (
            r.raft.promotable() == wp
        ), f"#{i}: promotable = {r.raft.promotable()}, want {wp}"


def test_raft_nodes():
    l = default_logger()

    class Test:
        def __init__(self, ids: List[int], wids: List[int]):
            self.ids = ids
            self.wids = wids

    tests = [
        Test([1, 2, 3], [1, 2, 3]),
        Test([3, 2, 1], [1, 2, 3]),
    ]

    for i, v in enumerate(tests):
        ids, wids = v.ids, v.wids
        storage = new_storage()
        r = new_test_raft(1, ids, 10, 1, storage, l)
        voter_ids = r.raft.prs().conf_voters().ids()
        wids = set(wids)
        assert voter_ids == wids, f"#{i}: nodes = {voter_ids}, want {wids}"


# test_commit_after_remove_node verifies that pending commands can become
# committed when a config change reduces the quorum requirements.
#
# test_campaign_while_leader
# test_campaign_while_leader_with_pre_vote
@pytest.mark.parametrize("pre_vote", [True, False])
def test_commit_after_remove_node(pre_vote: bool):
    l = default_logger()
    r = new_test_raft_with_prevote(1, [1], 5, 1, new_storage(), pre_vote, l)
    assert r.raft.get_state() == StateRole.Follower
    # We don't call campaign() directly because it comes after the check
    # for our current state.
    r.raft.step(new_message(1, 1, MessageType.MsgHup, 0))
    assert r.raft.get_state() == StateRole.Leader
    term = r.raft.get_term()
    r.raft.step(new_message(1, 1, MessageType.MsgHup, 0))
    assert r.raft.get_term() == term


# test_leader_transfer_to_uptodate_node verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
def test_leader_transfer_to_uptodate_node():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    lead_id = nt.peers[1].raft.get_leader_id()
    assert lead_id == 1

    # Transfer leadership to peer 2.
    nt.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 2)

    # After some log replication, transfer leadership back to peer 1.
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    nt.send([new_message(1, 2, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


# test_leader_transfer_to_uptodate_node_from_follower verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
# Not like test_leader_transfer_to_uptodate_node, where the leader transfer message
# is sent to the leader, in this test case every leader transfer message is sent
# to the follower.
def test_leader_transfer_to_uptodate_node_from_follower():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    lead_id = nt.peers[1].raft.get_leader_id()
    assert lead_id == 1

    # transfer leadership to peer 2.
    nt.send([new_message(2, 2, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 2)

    # After some log replication, transfer leadership back to peer 1.
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    nt.send([new_message(1, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


# TestLeaderTransferWithCheckQuorum ensures transferring leader still works
# even the current leader is still under its leader lease
def test_leader_transfer_with_check_quorum():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    for i in range(1, 4):
        r = nt.peers[i].raft
        r.set_check_quorum(True)
        election_timeout = r.election_timeout()
        r.set_randomized_election_timeout(election_timeout + 1)

    b_election_timeout = nt.peers[2].raft.election_timeout()
    nt.peers[2].raft.set_randomized_election_timeout(b_election_timeout + 1)

    # Letting peer 2 electionElapsed reach to timeout so that it can vote for peer 1
    for _ in range(0, b_election_timeout):
        nt.peers[2].raft.tick()

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers[1].raft.get_leader_id() == 1

    # Transfer leadership to 2.
    nt.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 2)

    # After some log replication, transfer leadership back to 1.
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    nt.send([new_message(1, 2, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def test_leader_transfer_to_slow_follower():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    nt.recover()
    nt.peers[1].raft.prs().get(3).get_matched() == 1

    # Transfer leadership to 3 when node 3 is lack of log.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 3)


def test_leader_transfer_after_snapshot():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
    next_ents(nt.peers[1].raft, nt.storage[1])
    nt.storage[1].wl().commit_to(nt.peers[1].raft_log.get_applied())
    nt.storage[1].wl().compact(nt.peers[1].raft_log.get_applied())

    nt.recover()
    assert nt.peers[1].raft.prs().get(3).get_matched() == 1

    # Transfer leadership to 3 when node 3 is lack of snapshot.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    # Send pb.MsgHeartbeatResp to leader to trigger a snapshot for node 3.
    nt.send([new_message(3, 1, MessageType.MsgHeartbeatResponse, 0)])

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 3)


def test_leader_transfer_to_self():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # Transfer leadership to self, there will be noop.
    nt.send([new_message(1, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def test_leader_transfer_to_non_existing_node():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # Transfer leadership to non-existing node, there will be noop.
    nt.send([new_message(4, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def test_leader_transfer_to_learner():
    l = default_logger()
    s = MemStorage.new_with_conf_state(ConfState([1], [2]))
    c = new_test_config(1, 10, 1)
    leader = new_test_raft_with_config(c, s, l)

    s = MemStorage.new_with_conf_state(ConfState([1], [2]))
    c = new_test_config(2, 10, 1)
    learner = new_test_raft_with_config(c, s, l)

    nt = Network.new([leader, learner], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # Transfer leadership to learner node, there will be noop.
    nt.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])
    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def test_leader_transfer_timeout():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    # Transfer leadership to isolated node, wait for timeout.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3
    heartbeat_timeout = nt.peers[1].raft.heartbeat_timeout()
    election_timeout = nt.peers[1].raft.election_timeout()
    for _ in range(0, heartbeat_timeout):
        nt.peers[1].raft.tick()
    assert nt.peers[1].raft.get_lead_transferee() == 3
    for _ in range(0, election_timeout - heartbeat_timeout):
        nt.peers[1].raft.tick()

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def test_leader_transfer_ignore_proposal():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    # Transfer leadership to isolated node to let transfer pending, then send proposal.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3

    with pytest.raises(ProposalDroppedError):
        nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])
        nt.peers[1].step(new_message(1, 1, MessageType.MsgPropose, 1))

    assert nt.peers[1].raft.prs().get(1).get_matched() == 1


def test_leader_transfer_receive_higher_term_vote():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    # Transfer leadership to isolated node to let transfer pending.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3

    nt.send(
        [new_message_with_entries(2, 2, MessageType.MsgHup, [new_entry(1, 2, None)])]
    )

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 2)


def test_leader_transfer_remove_node():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.ignore(MessageType.MsgTimeoutNow)

    # The lead_transferee is removed when leadship transferring.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


# test_leader_transfer_back verifies leadership can transfer
# back to self when last transfer is pending.
def test_leader_transfer_back():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3

    # Transfer leadership back to self.
    nt.send([new_message(1, 1, MessageType.MsgTransferLeader, 0)])

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


# test_leader_transfer_second_transfer_to_another_node verifies leader can transfer to another node
# when last transfer is pending.
def test_leader_transfer_second_transfer_to_another_node():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers[1].raft.get_lead_transferee() == 3

    # Transfer leadership to another node.
    nt.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Follower, 2)


# test_leader_transfer_second_transfer_to_same_node verifies second transfer leader request
# to the same node should not extend the timeout while the first one is pending.
def test_leader_transfer_second_transfer_to_same_node():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    nt.isolate(3)

    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])

    assert nt.peers[1].raft.get_lead_transferee() == 3

    heartbeat_timeout = nt.peers[1].raft.heartbeat_timeout()

    for _ in range(0, heartbeat_timeout):
        nt.peers[1].raft.tick()

    # Second transfer leadership request to the same node.
    nt.send([new_message(3, 1, MessageType.MsgTransferLeader, 0)])

    election_timeout = nt.peers[1].raft.election_timeout()
    for _ in range(0, election_timeout - heartbeat_timeout):
        nt.peers[1].raft.tick()

    check_leader_transfer_state(nt.peers[1].raft, StateRole.Leader, 1)


def check_leader_transfer_state(r: InMemoryRaftRef, state: StateRole, lead: int):
    assert (
        r.get_state() == state and r.get_leader_id() == lead
    ), f"after transferring, node has state {r.state} lead {state}, want state {r.get_leader_id()} lead {lead}"


# test_transfer_non_member verifies that when a MsgTimeoutNow arrives at
# a node that has been removed from the group, nothing happens.
# (previously, if the node also got votes, it would panic as it
# transitioned to StateRole::Leader)
def test_transfer_non_member():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [2, 3, 4], 5, 1, storage, l)
    raft.step(new_message(2, 1, MessageType.MsgTimeoutNow, 0))
    raft.step(new_message(2, 1, MessageType.MsgRequestVoteResponse, 0))
    raft.step(new_message(3, 1, MessageType.MsgRequestVoteResponse, 0))
    assert raft.raft.get_state() == StateRole.Follower


# TestNodeWithSmallerTermCanCompleteElection tests the scenario where a node
# that has been partitioned away (and fallen behind) rejoins the cluster at
# about the same time the leader node gets partitioned away.
# Previously the cluster would come to a standstill when run with PreVote
# enabled.
def test_node_with_smaller_term_can_complete_election():
    l = default_logger()
    s1 = new_storage()
    n1 = new_test_raft_with_prevote(1, [1, 2, 3], 10, 1, s1, True, l)
    s2 = new_storage()
    n2 = new_test_raft_with_prevote(2, [1, 2, 3], 10, 1, s2, True, l)
    s3 = new_storage()
    n3 = new_test_raft_with_prevote(3, [1, 2, 3], 10, 1, s3, True, l)

    n1.raft.become_follower(1, INVALID_ID)
    n2.raft.become_follower(1, INVALID_ID)
    n3.raft.become_follower(1, INVALID_ID)

    # cause a network partition to isolate node 3
    config = Network.default_config()
    config.set_pre_vote(True)
    nt = Network.new_with_config([n1, n2, n3], config, l)
    nt.cut(1, 3)
    nt.cut(2, 3)

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    assert nt.peers[1].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.get_state() == StateRole.Follower

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    assert nt.peers[3].raft.get_state() == StateRole.PreCandidate

    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # check whether the term values are expected
    # a.Term == 3
    # b.Term == 3
    # c.Term == 1

    assert nt.peers[1].raft.get_term() == 3
    assert nt.peers[2].raft.get_term() == 3
    assert nt.peers[3].raft.get_term() == 1

    # check state
    # a == follower
    # b == leader
    # c == pre-candidate
    assert nt.peers[1].raft.get_state() == StateRole.Follower
    assert nt.peers[2].raft.get_state() == StateRole.Leader
    assert nt.peers[3].raft.get_state() == StateRole.PreCandidate

    # recover the network then immediately isolate b which is currently
    # the leader, this is to emulate the crash of b.
    nt.recover()
    nt.cut(2, 1)
    nt.cut(2, 3)

    # call for election
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # do we have a leader?
    assert (
        nt.peers[1].raft.get_state() == StateRole.Leader
        or nt.peers[3].raft.get_state() == StateRole.Leader
    ), f"no leader"


def new_test_learner_raft(
    id: int,
    peers: List[int],
    learners: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorageRef,
    logger: LoggerRef,
) -> Interface:
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), f"new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        storage.initialize_with_conf_state(ConfState(peers, learners))

    cfg = new_test_config(id, election, heartbeat)
    return new_test_raft_with_config(cfg, storage, logger)


def new_test_learner_raft_with_prevote(
    id: int, peers: List[int], learners: List[int], logger: LoggerRef, prevote: bool
) -> Interface:
    storage = new_storage()
    storage.initialize_with_conf_state(ConfState(peers, learners))
    cfg = new_test_config(id, 10, 1)
    cfg.set_pre_vote(prevote)
    return new_test_raft_with_config(cfg, storage, logger)


# TestLearnerElectionTimeout verifies that the leader should not start election
# even when times out.
def test_learner_election_timeout():
    l = default_logger()
    s1 = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, s1, l)

    s2 = new_storage()
    n2 = new_test_learner_raft(2, [1], [2], 10, 1, s2, l)

    timeout = n2.raft.election_timeout()
    n2.raft.set_randomized_election_timeout(timeout)

    # n2 is a learner. Learner should not start election even when time out.
    for _ in range(0, timeout):
        n2.raft.tick()

    assert n2.raft.get_state() == StateRole.Follower


# TestLearnerPromotion verifies that the leaner should not election until
# it is promoted to a normal peer.
def test_learner_promotion():
    l = default_logger()
    s1 = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, s1, l)
    n1.raft.become_follower(1, INVALID_ID)

    s2 = new_storage()
    n2 = new_test_learner_raft(2, [1], [2], 10, 1, s2, l)
    n2.raft.become_follower(1, INVALID_ID)

    network = Network.new([n1, n2], l)
    assert network.peers[1].raft.get_state() == StateRole.Follower

    # n1 should become leader.
    timeout = network.peers[1].raft.election_timeout()
    network.peers[1].raft.set_randomized_election_timeout(timeout)

    for _ in range(0, timeout):
        network.peers[1].raft.tick()

    assert network.peers[1].raft.get_state() == StateRole.Leader
    assert network.peers[2].raft.get_state() == StateRole.Follower

    heart_beat = new_message(1, 1, MessageType.MsgBeat, 0)
    network.send([heart_beat.clone()])

    # Promote n2 from learner to follower.
    network.peers[1].raft.apply_conf_change(add_node(2))
    network.peers[2].raft.apply_conf_change(add_node(2))
    assert network.peers[2].raft.get_state() == StateRole.Follower
    assert network.peers[2].raft.promotable()

    timeout = network.peers[2].raft.election_timeout()
    network.peers[2].raft.set_randomized_election_timeout(timeout)
    for _ in range(0, timeout):
        network.peers[2].raft.tick()

    heart_beat.set_to(2)
    heart_beat.set_from(2)
    network.send([heart_beat])
    assert network.peers[1].raft.get_state() == StateRole.Follower
    assert network.peers[2].raft.get_state() == StateRole.Leader


# TestLearnerLogReplication tests that a learner can receive entries from the leader.
def test_learner_log_replication():
    l = default_logger()
    s1 = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, s1, l)
    s2 = new_storage()
    n2 = new_test_learner_raft(2, [1], [2], 10, 1, s2, l)
    network = Network.new([n1, n2], l)

    network.peers[1].raft.become_follower(1, INVALID_ID)
    network.peers[2].raft.become_follower(1, INVALID_ID)

    timeout = network.peers[1].raft.election_timeout()
    network.peers[1].raft.set_randomized_election_timeout(timeout)

    for _ in range(0, timeout):
        network.peers[1].raft.tick()

    heart_beat = new_message(1, 1, MessageType.MsgBeat, 0)
    network.send([heart_beat])

    assert network.peers[1].raft.get_state() == StateRole.Leader
    assert network.peers[2].raft.get_state() == StateRole.Follower
    assert not network.peers[2].raft.promotable()

    next_committed = network.peers[1].raft_log.get_committed() + 1

    msg = new_message(1, 1, MessageType.MsgPropose, 1)
    network.send([msg])

    assert network.peers[1].raft_log.get_committed() == next_committed
    assert network.peers[2].raft_log.get_committed() == next_committed

    matched = network.peers[1].raft.prs().get(2).get_matched()
    assert matched == network.peers[2].raft_log.get_committed()


# TestRestoreWithLearner restores a snapshot which contains learners.
def test_restore_with_learner():
    l = default_logger()
    s = new_snapshot(11, 11, [1, 2])
    s.get_metadata().get_conf_state().set_learners(
        [*s.get_metadata().get_conf_state().get_learners(), 3]
    )

    storage = new_storage()
    sm = new_test_learner_raft(3, [1, 2], [3], 10, 1, storage, l)
    assert not sm.raft.promotable()
    assert sm.raft.restore(s.clone())
    assert sm.raft_log.last_index() == 11
    assert sm.raft_log.term(11) == 11
    assert sm.raft.prs().conf_voters().ids() == {1, 2}
    assert sm.raft.prs().conf_learners() == {3}

    conf_state = s.get_metadata().get_conf_state()
    for node in conf_state.get_voters():
        assert sm.raft.prs().get(node)
        assert node not in sm.raft.prs().conf_learners()

    for node in conf_state.get_learners():
        assert sm.raft.prs().get(node)
        assert node in sm.raft.prs().conf_learners()

    assert not sm.raft.restore(s)


# Tests if outgoing voters can restore snapshot correctly.
def test_restore_with_voters_outgoing():
    l = default_logger()
    # magic number
    s = new_snapshot(11, 11, [2, 3, 4])
    s.get_metadata().get_conf_state().set_voters_outgoing([1, 2, 3])

    storage = new_storage()
    sm = new_test_raft(1, [1, 2], 10, 1, storage, l)
    assert sm.raft.restore(s.clone())
    assert sm.raft_log.last_index() == s.get_metadata().get_index()
    assert sm.raft_log.term(s.get_metadata().get_index()) == s.get_metadata().get_term()
    assert sm.raft.prs().conf_voters().ids() == {1, 2, 3, 4}
    assert not sm.raft.restore(s)


# Verifies that a voter can be depromoted by snapshot.
def test_restore_depromote_voter():
    l = default_logger()
    s = new_snapshot(11, 11, [1, 2])
    s.get_metadata().get_conf_state().set_learners(
        [*s.get_metadata().get_conf_state().get_learners(), 3]
    )

    storage = new_storage()
    sm = new_test_raft(3, [1, 2, 3], 10, 1, storage, l)
    assert sm.raft.promotable()
    assert sm.raft.restore(s)


def test_restore_learner():
    l = default_logger()
    s = new_snapshot(11, 11, [1, 2])
    s.get_metadata().get_conf_state().set_learners(
        [*s.get_metadata().get_conf_state().get_learners(), 3]
    )

    storage = new_storage()
    sm = new_test_raft(3, [], 10, 1, storage, l)
    assert not sm.raft.promotable()
    assert sm.raft.restore(s)
    assert not sm.raft.promotable()


# TestRestoreLearnerPromotion checks that a learner can become to a follower after
# restoring snapshot.
def test_restore_learner_promotion():
    l = default_logger()
    s = new_snapshot(11, 11, [1, 2, 3])
    storage = new_storage()
    sm = new_test_learner_raft(3, [1, 2], [3], 10, 1, storage, l)
    assert not sm.raft.promotable()
    assert sm.raft.restore(s)
    assert sm.raft.promotable()


# TestLearnerReceiveSnapshot tests that a learner can receive a snapshot from leader.
def test_learner_receive_snapshot():
    l = default_logger()
    s = new_snapshot(11, 11, [1])
    s.get_metadata().get_conf_state().set_learners(
        [*s.get_metadata().get_conf_state().get_learners(), 2]
    )

    s1 = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, s1, l)
    s2 = new_storage()
    n2 = new_test_learner_raft(2, [1], [2], 10, 1, s2, l)

    n1.raft.restore(s)
    n1.persist()

    commited = n1.raft_log.get_committed()
    n1.raft.commit_apply(commited)

    network = Network.new([n1, n2], l)

    timeout = network.peers[1].raft.election_timeout()
    network.peers[1].raft.set_randomized_election_timeout(timeout)

    for _ in range(0, timeout):
        network.peers[1].raft.tick()

    msg = Message.default()
    msg.set_from(1)
    msg.set_to(1)
    msg.set_msg_type(MessageType.MsgBeat)
    network.send([msg])

    n1_committed = network.peers[1].raft_log.get_committed()
    n2_committed = network.peers[2].raft_log.get_committed()

    assert n1_committed == n2_committed


# TestAddLearner tests that addLearner could update nodes correctly.
def test_add_learner():
    l = default_logger()
    storage = new_storage()
    n1 = new_test_raft(1, [1, 2], 10, 1, storage, l)
    n1.raft.apply_conf_change(add_learner(2))

    assert n1.raft.prs().conf_learners() == {2}
    assert 2 in n1.raft.prs().conf_learners()


# TestRemoveLearner tests that removeNode could update nodes and
# and removed list correctly.
def test_remove_learner():
    l = default_logger()
    storage = new_storage()
    n1 = new_test_learner_raft(1, [1], [2], 10, 1, storage, l)
    n1.raft.apply_conf_change(remove_node(2))
    assert n1.raft.prs().conf_voters().ids() == {1}
    assert not n1.raft.prs().conf_learners()

    # Remove all voters are not allowed.
    with pytest.raises(ConfChangeError):
        n1.raft.apply_conf_change(remove_node(1))

    assert n1.raft.prs().conf_voters().ids() == {1}
    assert not n1.raft.prs().conf_learners()


# simulate rolling update a cluster for Pre-Vote. cluster has 3 nodes [n1, n2, n3].
# n1 is leader with term 2
# n2 is follower with term 2
# n3 is partitioned, with term 4 and less log, state is candidate
def new_prevote_migration_cluster() -> Network:
    # We intentionally do not enable pre_vote for n3, this is done so in order
    # to simulate a rolling restart process where it's possible to have a mixed
    # version cluster with replicas with pre_vote enabled, and replicas without.
    l = default_logger()
    s1 = new_storage()
    n1 = new_test_raft_with_prevote(1, [1, 2, 3], 10, 1, s1, True, l)
    s2 = new_storage()
    n2 = new_test_raft_with_prevote(2, [1, 2, 3], 10, 1, s2, True, l)
    s3 = new_storage()
    n3 = new_test_raft_with_prevote(3, [1, 2, 3], 10, 1, s3, False, l)

    n1.raft.become_follower(1, INVALID_ID)
    n2.raft.become_follower(1, INVALID_ID)
    n3.raft.become_follower(1, INVALID_ID)

    nt = Network.new([n1, n2, n3], l)

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # Cause a network partition to isolate n3.
    nt.isolate(3)
    nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    # check state
    # n1.state == Leader
    # n2.state == Follower
    # n3.state == Candidate
    assert nt.peers[1].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.get_state() == StateRole.Follower
    assert nt.peers[3].raft.get_state() == StateRole.Candidate

    # check term
    # n1.Term == 2
    # n2.Term == 2
    # n3.Term == 4
    assert nt.peers[1].raft.get_term() == 2
    assert nt.peers[2].raft.get_term() == 2
    assert nt.peers[3].raft.get_term() == 4

    # Enable prevote on n3, then recover the network
    nt.peers[3].raft.set_pre_vote(True)
    nt.recover()

    return nt


def test_prevote_migration_can_complete_election():
    # n1 is leader with term 2
    # n2 is follower with term 2
    # n3 is pre-candidate with term 4, and less log
    nt = new_prevote_migration_cluster()

    # simulate leader down
    nt.isolate(1)

    # Call for elections from both n2 and n3.
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # check state
    # n2.state == Follower
    # n3.state == PreCandidate
    assert nt.peers[2].raft.get_state() == StateRole.Follower
    assert nt.peers[3].raft.get_state() == StateRole.PreCandidate

    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # Do we have a leader?
    assert (
        nt.peers[2].raft.get_state() == StateRole.Leader
        or nt.peers[3].raft.get_state() == StateRole.Leader
    )


def test_prevote_migration_with_free_stuck_pre_candidate():
    l = default_logger()
    nt = new_prevote_migration_cluster()

    # n1 is leader with term 2
    # n2 is follower with term 2
    # n3 is pre-candidate with term 4, and less log
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])

    assert nt.peers[1].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.get_state() == StateRole.Follower
    assert nt.peers[3].raft.get_state() == StateRole.PreCandidate

    # Pre-Vote again for safety
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    assert nt.peers[1].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.get_state() == StateRole.Follower
    assert nt.peers[3].raft.get_state() == StateRole.PreCandidate

    to_send = new_message(1, 3, MessageType.MsgHeartbeat, 0)
    to_send.set_term(nt.peers[1].raft.get_term())
    nt.send([to_send])

    # Disrupt the leader so that the stuck peer is freed
    assert nt.peers[1].raft.get_state() == StateRole.Follower

    assert nt.peers[3].raft.get_term() == nt.peers[1].raft.get_term()


def test_learner_respond_vote():
    l = default_logger()

    s1 = new_storage()
    n1 = new_test_learner_raft(1, [1, 2], [3], 10, 1, s1, l)
    n1.raft.become_follower(1, INVALID_ID)
    n1.raft.reset_randomized_election_timeout()

    s3 = new_storage()
    n3 = new_test_learner_raft(3, [1, 2], [3], 10, 1, s3, l)
    n3.raft.become_follower(1, INVALID_ID)
    n3.raft.reset_randomized_election_timeout()

    def do_campaign(nw: Network):
        msg = new_message(1, 1, MessageType.MsgHup, 0)
        nw.send([msg])

    network = Network.new([n1, None, n3], l)
    network.isolate(2)

    # Can't elect new leader because 1 won't send MsgRequestVote to 3.
    do_campaign(network)
    assert network.peers[1].raft.get_state() == StateRole.Candidate

    # After promote 3 to voter, election should success.
    network.peers[1].raft.apply_conf_change(add_node(3))
    do_campaign(network)
    assert n1.raft.get_state() == StateRole.Leader


def test_election_tick_range():
    l = default_logger()
    cfg = new_test_config(1, 10, 1)
    s = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
    raft = new_test_raft_with_config(cfg, s, l)
    for _ in range(0, 1000):
        raft.raft.reset_randomized_election_timeout()
        randomized_timeout = raft.raft.randomized_election_timeout()
        assert (
            cfg.get_election_tick() <= randomized_timeout
            and randomized_timeout < 2 * cfg.get_election_tick()
        )

    cfg.set_min_election_tick(cfg.get_election_tick())
    cfg.validate()

    # Too small election tick.
    cfg.set_min_election_tick(cfg.get_election_tick() - 1)
    with pytest.raises(ConfigInvalidError) as e:
        cfg.validate()

    assert (
        f"min election tick {cfg.get_election_tick() - 1} must not be less than election_tick {cfg.get_election_tick()}"
        == str(e.value)
    )

    # max_election_tick should be larger than min_election_tick
    cfg.set_min_election_tick(cfg.get_election_tick())
    cfg.set_max_election_tick(cfg.get_election_tick())

    with pytest.raises(ConfigInvalidError) as e:
        cfg.validate()

    assert (
        f"min election tick {cfg.get_election_tick()} should be less than max election tick {cfg.get_election_tick()}"
        == str(e.value)
    )

    cfg.set_max_election_tick(cfg.get_election_tick() + 1)

    storage = new_storage()
    raft = new_test_raft_with_config(cfg, storage, l)

    for _ in range(0, 100):
        raft.raft.reset_randomized_election_timeout()
        randomized_timeout = raft.raft.randomized_election_timeout()
        assert randomized_timeout == cfg.get_election_tick()


# TestPreVoteWithSplitVote verifies that after split vote, cluster can complete
# election in next round.
def test_prevote_with_split_vote():
    l = default_logger()
    s1, s2, s3 = new_storage(), new_storage(), new_storage()
    peers = [
        new_test_raft(1, [1, 2, 3], 10, 1, s1, l),
        new_test_raft(2, [1, 2, 3], 10, 1, s2, l),
        new_test_raft(3, [1, 2, 3], 10, 1, s3, l),
    ]

    peers[0].raft.become_follower(1, INVALID_ID)
    peers[1].raft.become_follower(1, INVALID_ID)
    peers[2].raft.become_follower(1, INVALID_ID)

    network = Network.new(peers, l)
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # simulate leader down. followers start split vote.
    network.isolate(1)
    network.send(
        [
            new_message(2, 2, MessageType.MsgHup, 0),
            new_message(3, 3, MessageType.MsgHup, 0),
        ]
    )

    # check whether the term values are expected
    assert peers[1].raft.get_term() == 3, "peer 2 term"
    assert peers[2].raft.get_term() == 3, "peer 3 term"

    # check state
    assert peers[1].raft.get_state() == StateRole.Candidate, "peer 2 state"
    assert peers[2].raft.get_state() == StateRole.Candidate, "peer 3 state"

    # node 2 election timeout first
    network.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # check whether the term values are expected
    assert peers[1].raft.get_term() == 4, "peer 2 term"
    assert peers[2].raft.get_term() == 4, "peer 3 term"

    # check state
    assert peers[1].raft.get_state() == StateRole.Leader, "peer 2 state"
    assert peers[2].raft.get_state() == StateRole.Follower, "peer 3 state"


# ensure that after a node become pre-candidate, it will checkQuorum correctly.
def test_prevote_with_check_quorum():
    l = default_logger()

    def bootstrap(id: int) -> Interface:
        cfg = new_test_config(id, 10, 1)
        cfg.set_pre_vote(True)
        cfg.set_check_quorum(True)
        s = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
        i = new_test_raft_with_config(cfg, s, l)
        i.raft.become_follower(1, INVALID_ID)
        return i

    peer1, peer2, peer3 = bootstrap(1), bootstrap(2), bootstrap(3)

    network = Network.new([peer1, peer2, peer3], l)
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # cause a network partition to isolate node 3. node 3 has leader info
    network.cut(1, 3)
    network.cut(2, 3)

    assert network.peers[1].raft.get_state() == StateRole.Leader, "peer 1 state"
    assert network.peers[2].raft.get_state() == StateRole.Follower, "peer 2 state"

    network.send([new_message(3, 3, MessageType.MsgHup, 0)])

    assert network.peers[3].raft.get_state() == StateRole.PreCandidate, "peer 3 state"

    # term + 2, so that node 2 will ignore node 3's PreVote
    network.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])
    network.send([new_message(1, 2, MessageType.MsgTransferLeader, 0)])

    # check whether the term values are expected
    assert network.peers[1].raft.get_term() == 4, "peer 1 term"
    assert network.peers[2].raft.get_term() == 4, "peer 2 term"
    assert network.peers[3].raft.get_term() == 2, "peer 3 term"

    # check state
    assert network.peers[1].raft.get_state() == StateRole.Leader, "peer 1 state"
    assert network.peers[2].raft.get_state() == StateRole.Follower, "peer 2 state"
    assert network.peers[3].raft.get_state() == StateRole.PreCandidate, "peer 3 state"

    # recover the network then immediately isolate node 1 which is currently
    # the leader, this is to emulate the crash of node 1.
    network.recover()
    network.cut(1, 2)
    network.cut(1, 3)

    # call for election. node 3 shouldn't ignore node 2's PreVote
    timeout = network.peers[3].raft.randomized_election_timeout()
    for _ in range(0, timeout):
        network.peers[3].raft.tick()

    network.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # check state
    assert network.peers[2].raft.get_state() == StateRole.Leader, "peer 2 state"
    assert network.peers[3].raft.get_state() == StateRole.Follower, "peer 3 state"


# ensure a new Raft returns a Error::ConfigInvalid with an invalid config
def test_new_raft_with_bad_config_errors():
    l = default_logger()
    invalid_config = new_test_config(INVALID_ID, 1, 1)
    s = MemStorage.new_with_conf_state(ConfState([1, 2], []))

    with pytest.raises(ConfigInvalidError):
        InMemoryRaft(invalid_config, s, l)


# tests whether MsgAppend are batched
def test_batch_msg_append():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2, 3], 10, 1, storage.clone(), l)
    raft.raft.become_candidate()
    raft.raft.become_leader()
    raft.raft.set_batch_append(True)
    commit_noop_entry(raft, storage)
    for _ in range(0, 10):
        prop_msg = new_message(1, 1, MessageType.MsgPropose, 1)
        raft.raft.step(prop_msg)

    assert len(raft.raft.get_msgs()) == 2

    for msg in raft.raft.get_msgs():
        assert len(msg.get_entries()) == 10
        assert msg.get_index() == 1

    # if the append entry is not continuous, raft should not batch the RPC
    reject_msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    reject_msg.set_reject(True)
    reject_msg.set_index(2)
    raft.raft.step(reject_msg)
    assert len(raft.raft.get_msgs()) == 3


# Tests if unapplied conf change is checked before campaign.
def test_conf_change_check_before_campaign():
    l = default_logger()
    nt = Network.new([None, None, None], l)
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers[1].raft.get_state() == StateRole.Leader

    m = new_message(1, 1, MessageType.MsgPropose, 0)
    e = Entry.default()
    e.set_entry_type(EntryType.EntryConfChange)
    cc = ConfChange.default()
    cc.set_change_type(ConfChangeType.RemoveNode)
    cc.set_node_id(3)
    e.set_data(cc.encode())
    m.set_entries([*m.get_entries(), e])
    nt.send([m])

    # trigger campaign in node 2
    nt.peers.get(2).raft.reset_randomized_election_timeout()
    timeout = nt.peers.get(2).raft.randomized_election_timeout()
    for _ in range(0, timeout):
        nt.peers.get(2).raft.tick()

    # It's still follower because committed conf change is not applied.
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower

    # Transfer leadership to peer 2.
    nt.send([new_message(1, 1, MessageType.MsgTransferLeader, 2)])
    assert nt.peers.get(1).raft.get_state() == StateRole.Leader

    # It's still follower because committed conf change is not applied.
    assert nt.peers.get(2).raft.get_state() == StateRole.Follower

    # Abort transfer leader.
    committed = nt.peers.get(2).raft_log.get_committed()
    nt.peers.get(2).raft.commit_apply(committed)
    nt.peers.get(2).raft.apply_conf_change(remove_node(3))

    # transfer leadership to peer 2 again.
    nt.send([new_message(2, 1, MessageType.MsgTransferLeader, 0)])
    assert nt.peers.get(1).raft.get_state() == StateRole.Follower
    assert nt.peers.get(2).raft.get_state() == StateRole.Leader

    nt.peers.get(1).raft.commit_apply(committed)
    nt.peers.get(1).raft.apply_conf_change(remove_node(3))

    # trigger campaign in node 1
    nt.peers.get(1).raft.reset_randomized_election_timeout()

    timeout = nt.peers.get(1).raft.randomized_election_timeout()
    for _ in range(0, timeout):
        nt.peers.get(1).raft.tick()

    assert nt.peers.get(1).raft.get_state() == StateRole.Candidate


@pytest.mark.parametrize("use_prevote", [True, False])
def test_advance_commit_index_by_vote_request(use_prevote: bool):
    l = default_logger()

    cases: List[ConfChange] = [
        conf_change(ConfChangeType.AddNode, 4),
        conf_change_v2(
            [
                new_conf_change_single(3, ConfChangeType.AddLearnerNode),
                new_conf_change_single(4, ConfChangeType.AddNode),
            ]
        ),
    ]

    for i, cc in enumerate(cases):
        peers = [
            new_test_learner_raft_with_prevote(1, [1, 2, 3], [4], l, use_prevote),
            new_test_learner_raft_with_prevote(2, [1, 2, 3], [4], l, use_prevote),
            new_test_learner_raft_with_prevote(3, [1, 2, 3], [4], l, use_prevote),
            new_test_learner_raft_with_prevote(4, [1, 2, 3], [4], l, use_prevote),
        ]

        nt = Network.new(peers, l)
        nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
        e = Entry.default()

        if v1 := cc.as_v1():
            e.set_entry_type(EntryType.EntryConfChange)
            e.set_data(v1.encode())
        else:
            e.set_entry_type(EntryType.EntryConfChangeV2)
            v2 = cc.as_v2()
            e.set_data(v2.encode())

        # propose a confchange entry but don't let it commit
        nt.ignore(MessageType.MsgAppendResponse)
        nt.send([new_message_with_entries(1, 1, MessageType.MsgPropose, [e])])

        cc_index = nt.peers[1].raft_log.last_index()

        # let node 4 have more up to data log than other voter
        nt.recover()
        nt.cut(1, 2)
        nt.cut(1, 3)
        nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

        # let the confchange entry commit but don't let node 4 know
        nt.recover()
        nt.cut(1, 4)
        nt.ignore(MessageType.MsgAppend)
        msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
        msg.set_index(nt.peers[2].raft_log.last_index())
        nt.send([msg, new_message(1, 1, MessageType.MsgBeat, 0)])

        # simulate the leader down
        nt.recover()
        nt.isolate(1)

        p4 = nt.peers[4]
        assert (
            p4.raft_log.get_committed() < cc_index
        ), f"#{i} expected node 4 commit index less than {cc_index}, got {p4.raft_log.get_committed()}"

        # node 4 can't start new election because it thinks itself is a learner
        for _ in range(0, p4.raft.randomized_election_timeout()):
            p4.raft.tick()

        assert (
            p4.raft.get_state() == StateRole.Follower
        ), f"#{i} node 4 state: {p4.raft.get_state()}, want Follower"

        p2 = nt.peers[2]
        assert (
            p2.raft_log.get_committed() >= cc_index
        ), f"#{i} expected node 2 commit index not less than {cc_index}, got {p2.raft_log.get_committed()}"

        p2.raft.apply_conf_change(cc.as_v2())
        p2.raft.commit_apply(cc_index)

        # node 2 needs votes from both node 3 and node 4, but node 4 will reject it
        for _ in range(0, p2.raft.randomized_election_timeout()):
            p2.raft.tick()

        want = StateRole.PreCandidate if use_prevote else StateRole.Candidate

        assert (
            p2.raft.get_state() == want
        ), f"#{i} node 2 state: {p2.raft.get_state()}, want {want}"
        msgs = nt.read_messages()
        nt.filter_and_send(msgs)

        assert (
            nt.peers[2].raft.get_state() != StateRole.Leader
        ), f"#{i} node 2 can't campaign successfully."

        # node 4's commit index should be advanced by node 2's vote request
        p4 = nt.peers[4]
        assert (
            p4.raft_log.get_committed() >= cc_index
        ), f"#{i} expected node 4 commit index not less than {cc_index}, got {p4.raft_log.get_committed()}"

        p4.raft.apply_conf_change(cc.as_v2())
        p4.raft.commit_apply(cc_index)

        # now node 4 can start new election and become leader
        for _ in range(0, p4.raft.randomized_election_timeout()):
            p4.raft.tick()
        msgs = nt.read_messages()
        nt.filter_and_send(msgs)
        assert (
            nt.peers[4].raft.get_state() == StateRole.Leader
        ), f"#{i} node 4 state: {nt.peers[4].raft.get_state()}, want Leader"


# test_advance_commit_index_by_direct_vote_request
#: Tests the commit index can be advanced by direct vote request
#
# test_advance_commit_index_by_prevote_request
#: Tests the commit index can be advanced by prevote request
@pytest.mark.parametrize("use_prevote", [True, False])
def test_advance_commit_index_by_vote_response(use_prevote: bool):
    l = default_logger()
    cases: List[ConfChange] = [
        conf_change(ConfChangeType.RemoveNode, 4),
        # Explicit leave joint
        conf_change_v2([]),
    ]

    # Enter joint confchange
    enter_joint = conf_change_v2(
        [
            new_conf_change_single(3, ConfChangeType.AddNode),
            new_conf_change_single(4, ConfChangeType.AddLearnerNode),
        ]
    )

    enter_joint.set_transition(ConfChangeTransition.Explicit)

    for i, cc in enumerate(cases):
        s1, s2, s3, s4 = new_storage(), new_storage(), new_storage(), new_storage()
        peers = [
            new_test_raft_with_prevote(1, [1, 2, 3, 4], 10, 1, s1, use_prevote, l),
            new_test_raft_with_prevote(2, [1, 2, 3, 4], 10, 1, s2, use_prevote, l),
            new_test_raft_with_prevote(3, [1, 2, 3, 4], 10, 1, s3, use_prevote, l),
            new_test_raft_with_prevote(4, [1, 2, 3, 4], 10, 1, s4, use_prevote, l),
        ]

        nt = Network.new(peers, l)

        # Joint confchange, let's enter joint first
        if not cc.as_v1():
            for p in nt.peers.values():
                p.raft.apply_conf_change(enter_joint)

        nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

        e = Entry.default()

        if v1 := cc.as_v1():
            e.set_entry_type(EntryType.EntryConfChange)
            e.set_data(v1.encode())
        else:
            e.set_entry_type(EntryType.EntryConfChangeV2)
            v2 = cc.as_v2()
            e.set_data(v2.encode())

        # propose a confchange entry but don't let it commit
        nt.ignore(MessageType.MsgAppendResponse)
        nt.send([new_message_with_entries(1, 1, MessageType.MsgPropose, [e])])

        cc_index = nt.peers[1].raft_log.last_index()

        # let node 4 have more up to data log than other voter
        nt.recover()
        nt.cut(1, 2)
        nt.cut(1, 3)
        nt.send([new_message(1, 1, MessageType.MsgPropose, 1)])

        # A delayed MsgAppResp message make the confchange entry become committed
        msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
        msg.set_index(nt.peers[2].raft_log.last_index())
        nt.send([msg, new_message(1, 1, MessageType.MsgBeat, 0)])

        # simulate the leader down
        nt.recover()
        nt.isolate(1)

        p4 = nt.peers[4]
        assert (
            p4.raft_log.get_committed() >= cc_index
        ), f"#{i} expected node 4 commit index larger than {cc_index}, got {p4.raft_log.get_committed()}"

        p4.raft.apply_conf_change(cc.as_v2())
        p4.raft.commit_apply(cc_index)
        # node 4 can't start new election because it thinks itself is a learner
        for _ in range(0, p4.raft.randomized_election_timeout()):
            p4.raft.tick()

        assert (
            p4.raft.get_state() == StateRole.Follower
        ), f"#{i} node 4 state: {p4.raft.get_state()}, want Follower"

        p2 = nt.peers[2]
        assert (
            p2.raft_log.get_committed() < cc_index
        ), f"#{i} expected node 2 commit index less than {cc_index}, got {p2.raft_log.get_committed()}"

        # node 2 needs votes from both node 3 and node 4, but node 4 will reject it
        for _ in range(0, p2.raft.randomized_election_timeout()):
            p2.raft.tick()

        want = StateRole.PreCandidate if use_prevote else StateRole.Candidate

        assert (
            p2.raft.get_state() == want
        ), f"#{i} node 2 state: {p2.raft.get_state()}, want {want}"

        msgs = nt.read_messages()

        nt.filter_and_send(msgs)

        p2 = nt.peers[2]
        assert (
            p2.raft.get_state() == StateRole.Follower
        ), f"#{i} node 2 should become follower by vote response, but got {p2.raft.get_state()}"

        # node 2's commit index should be advanced by vote response
        assert (
            p2.raft_log.get_committed() >= cc_index
        ), f"#{i} expected node 2 commit index less than {cc_index}, got {p2.raft_log.get_committed()}"

        p2.raft.apply_conf_change(cc.as_v2())
        p2.raft.commit_apply(cc_index)

        # now node 2 only need vote from node 3
        for _ in range(0, p2.raft.randomized_election_timeout()):
            p2.raft.tick()

        msgs = nt.read_messages()
        nt.filter_and_send(msgs)

        assert (
            nt.peers[2].raft.get_state() == StateRole.Leader
        ), f"#{i} node 2 state: {nt.peers[2].raft.get_state()} want Leader"


def prepare_request_snapshot() -> Tuple[Network, Snapshot]:
    l = default_logger()

    def index_term_11(id: int, ids: List[int]) -> Interface:
        store = MemStorage()
        store.wl().apply_snapshot(new_snapshot(11, 11, ids))
        raft = new_test_raft(id, ids, 5, 1, store, l)
        raft.raft.reset(11)
        return raft

    nt = Network.new(
        [
            index_term_11(1, [1, 2, 3]),
            index_term_11(2, [1, 2, 3]),
            index_term_11(3, [1, 2, 3]),
        ],
        l,
    )

    # elect r1 as leader
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    test_entries = Entry.default()

    test_entries.set_data(b"testdata")
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.send([msg.clone(), msg])
    assert nt.peers[1].raft_log.get_committed() == 14
    assert nt.peers[2].raft_log.get_committed() == 14

    ents = nt.peers[1].raft_log.unstable_entries()
    nt.storage[1].wl().append(ents)
    nt.storage[1].wl().commit_to(14)
    nt.peers[1].raft_log.set_applied(14)

    # Commit a new raft log.
    test_entries = Entry.default()
    test_entries.set_data(b"testdata")
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.send([msg])

    s = nt.storage[1].snapshot(0, 0)

    return (nt, s)


# Test if an up-to-date follower can request a snapshot from leader.
def test_follower_request_snapshot():
    nt, s = prepare_request_snapshot()

    # Request the latest snapshot.
    prev_snapshot_idx = s.get_metadata().get_index()
    request_idx = nt.peers[1].raft_log.get_committed()
    assert prev_snapshot_idx < request_idx
    nt.peers[2].raft.request_snapshot()

    # Send the request snapshot message.
    req_snap = nt.peers[2].raft.get_msgs().pop()
    assert req_snap.get_msg_type() == MessageType.MsgAppendResponse
    assert req_snap.get_reject()
    assert req_snap.get_request_snapshot() == request_idx

    nt.peers[1].raft.step(req_snap)

    # New proposes can not be replicated to peer 2.
    test_entries = Entry.default()
    test_entries.set_data(b"testdata")
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.send([msg.clone()])
    assert nt.peers[1].raft_log.get_committed() == 16
    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Snapshot
    assert nt.peers[2].raft_log.get_committed() == 15

    # Util snapshot success or fail.
    report_ok = new_message(2, 1, MessageType.MsgSnapStatus, 0)
    nt.send([report_ok])
    hb_resp = new_message(2, 1, MessageType.MsgHeartbeatResponse, 0)
    nt.send([hb_resp])
    nt.send([msg])

    assert nt.peers[1].raft_log.get_committed() == 17
    assert nt.peers[2].raft_log.get_committed() == 17


# Test if request snapshot can make progress when it meets SnapshotTemporarilyUnavailable.
def test_request_snapshot_unavailable():
    nt, s = prepare_request_snapshot()

    # Request the latest snapshot.
    prev_snapshot_idx = s.get_metadata().get_index()
    request_idx = nt.peers[1].raft_log.get_committed()
    assert prev_snapshot_idx < request_idx

    nt.peers[2].raft.request_snapshot()

    # Send the request snapshot message.
    req_snap = nt.peers[2].raft.get_msgs().pop()

    assert req_snap.get_msg_type() == MessageType.MsgAppendResponse
    assert req_snap.get_reject()
    assert req_snap.get_request_snapshot() == request_idx

    # Peer 2 is still in probe state due to SnapshotTemporarilyUnavailable.
    nt.peers[1].raft.store().wl().trigger_snap_unavailable()
    nt.peers[1].step(req_snap.clone())
    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Probe

    # Next index is decreased.
    nt.peers[1].raft.store().wl().trigger_snap_unavailable()
    nt.peers[1].step(req_snap.clone())

    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Probe

    # Snapshot will be available if it requests again. This message must not
    # be considered stale even if `reject != next - 1`
    nt.peers[1].step(req_snap)
    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Snapshot


# Test if request snapshot can make progress when matched is advanced.
def test_request_snapshot_matched_change():
    nt, _ = prepare_request_snapshot()
    # Let matched be greater than the committed.
    nt.peers[2].raft_log.set_committed(nt.peers[2].raft_log.get_committed() - 1)

    # Request the latest snapshot.
    nt.peers[2].raft.request_snapshot()
    req_snap = nt.peers[2].raft.get_msgs().pop()
    # The request snapshot is ignored because it is considered as out of order.
    nt.peers[1].step(req_snap)
    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Replicate

    # Heartbeat is responded with a request snapshot message.
    for _ in range(0, nt.peers[1].raft.heartbeat_timeout()):
        nt.peers[1].raft.tick()

    msg_hb = list(filter(lambda m: m.get_to() == 2, nt.peers[1].raft.get_msgs()))
    nt.peers[2].step(msg_hb.pop())
    req_snap = nt.peers[2].raft.get_msgs().pop()
    nt.peers[1].step(req_snap)
    assert nt.peers[1].raft.prs().get(2).get_state() == ProgressState.Snapshot


# Test if request snapshot can make progress when the peer is not Replicate.
def test_request_snapshot_none_replicate():
    nt, _ = prepare_request_snapshot()
    nt.peers[1].raft.prs().get(2).set_state(ProgressState.Snapshot)

    # Request the latest snapshot.
    nt.peers[2].raft.request_snapshot()
    req_snap = nt.peers[2].raft.get_msgs().pop()
    nt.peers[1].raft.step(req_snap)
    assert nt.peers[1].raft.prs().get(2).get_pending_request_snapshot() != 0


# Test if request snapshot can make progress when leader steps down.
def test_request_snapshot_step_down():
    nt, _ = prepare_request_snapshot()

    # Commit a new entry and leader steps down while peer 2 is isolated.
    nt.isolate(2)
    test_entries = Entry.default()
    test_entries.set_data(b"testdata")
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.send([msg])
    nt.send([new_message(3, 3, MessageType.MsgHup, 0)])
    assert nt.peers[3].raft.get_state() == StateRole.Leader

    # Recover and request the latest snapshot.
    nt.recover()
    nt.peers[2].raft.request_snapshot()
    nt.send([new_message(3, 3, MessageType.MsgBeat, 0)])
    assert (
        nt.peers[2].raft.get_pending_request_snapshot() == INVALID_INDEX
    ), f"{nt.peers[2].raft.get_pending_request_snapshot()}"


# Abort request snapshot if it becomes leader or candidate.
def test_request_snapshot_on_role_change():
    nt, _ = prepare_request_snapshot()

    nt.peers[2].raft.request_snapshot()

    # Becoming follower does not reset pending_request_snapshot.
    term, id = nt.peers[1].raft.get_term(), nt.peers[2].raft.get_id()
    nt.peers[2].raft.become_follower(term, id)

    assert (
        nt.peers[2].raft.get_pending_request_snapshot() != INVALID_INDEX
    ), f"{nt.peers[2].raft.get_pending_request_snapshot()}"

    nt.peers[2].raft.become_candidate()
    # Becoming candidate resets pending_request_snapshot.
    assert (
        nt.peers[2].raft.get_pending_request_snapshot() == INVALID_INDEX
    ), f"{nt.peers[2].raft.get_pending_request_snapshot()}"


# Tests group commit.
#
# 1. Logs should be replicated to at least different groups before committed;
# 2. all peers are configured to the same group, simple quorum should be used.
def test_group_commit():
    l = default_logger()

    class Test:
        def __init__(
            self, matches: List[int], group_ids: List[int], g_w: int, q_w: int
        ):
            self.matches = matches
            self.group_ids = group_ids
            self.g_w = g_w
            self.q_w = q_w

    tests = [
        # Single
        Test([1], [0], 1, 1),
        Test([1], [1], 1, 1),
        # Odd
        Test([2, 2, 1], [1, 2, 1], 2, 2),
        Test([2, 2, 1], [1, 1, 2], 1, 2),
        Test([2, 2, 1], [1, 0, 1], 1, 2),
        Test([2, 2, 1], [0, 0, 0], 1, 2),
        # Even
        Test([4, 2, 1, 3], [0, 0, 0, 0], 1, 2),
        Test([4, 2, 1, 3], [1, 0, 0, 0], 1, 2),
        Test([4, 2, 1, 3], [0, 1, 0, 2], 2, 2),
        Test([4, 2, 1, 3], [0, 2, 1, 0], 1, 2),
        Test([4, 2, 1, 3], [1, 1, 1, 1], 2, 2),
        Test([4, 2, 1, 3], [1, 1, 2, 1], 1, 2),
        Test([4, 2, 1, 3], [1, 2, 1, 1], 2, 2),
        Test([4, 2, 1, 3], [4, 3, 2, 1], 2, 2),
    ]

    for i, v in enumerate(tests):
        matches, group_ids, g_w, q_w = v.matches, v.group_ids, v.g_w, v.q_w
        store = MemStorage.new_with_conf_state(ConfState([1], []))
        min_index = min(matches)
        max_index = max(matches)
        logs = [empty_entry(1, i) for i in range(min_index, max_index + 1)]
        store.wl().append(logs)
        hs = HardState.default()
        hs.set_term(1)
        store.wl().set_hardstate(hs)
        cfg = new_test_config(1, 5, 1)
        sm = new_test_raft_with_config(cfg, store, l)

        groups = []
        for j, v in enumerate(zip(matches, group_ids)):
            m, g = v[0], v[1]
            id = j + 1
            if not sm.raft.prs().get(id):
                sm.raft.apply_conf_change(add_node(id))
                pr = sm.raft.prs().get(id)
                pr.set_matched(m)
                pr.set_next_idx(m + 1)
            if g != 0:
                groups.append((id, g))
        sm.raft.enable_group_commit(True)
        sm.raft.assign_commit_groups(groups)

        assert (
            sm.raft_log.get_committed() == 0
        ), f"#{i}: follower group committed {sm.raft_log.get_committed()}, want 0"

        sm.raft.set_state(StateRole.Leader)
        sm.raft.assign_commit_groups(groups)

        assert (
            sm.raft_log.get_committed() == g_w
        ), f"#{i}: leader group committed {sm.raft_log.get_committed()}, want {g_w}"
        sm.raft.enable_group_commit(False)
        assert (
            sm.raft_log.get_committed() == q_w
        ), f"#{i}: quorum committed {sm.raft_log.get_committed()}, want {g_w}"


def test_group_commit_consistent():
    l = default_logger()
    logs = []
    for i in range(1, 6):
        logs.append(empty_entry(1, i))
    for i in range(6, 8 + 1):
        logs.append(empty_entry(2, i))

    class Test:
        def __init__(
            self,
            matches: List[int],
            group_ids: List[int],
            committed: int,
            applied: int,
            role: StateRole,
            exp: Optional[bool],
        ) -> None:
            self.matches = matches
            self.group_ids = group_ids
            self.committed = committed
            self.applied = applied
            self.role = role
            self.exp = exp

    tests = [
        # Single node is not using group commit
        Test([8], [0], 8, 6, StateRole.Leader, False),
        Test([8], [1], 8, 5, StateRole.Leader, None),
        Test([8], [1], 8, 6, StateRole.Follower, None),
        # Not commit to current term should return None, as old leader may
        # have reach consistent.
        Test([8, 2, 0], [1, 2, 1], 2, 2, StateRole.Leader, None),
        Test([8, 2, 6], [1, 1, 2], 6, 6, StateRole.Leader, True),
        # Not apply to current term should return None, as there maybe pending conf change.
        Test([8, 2, 6], [1, 1, 2], 6, 5, StateRole.Leader, None),
        # It should be false when not using group commit.
        Test([8, 6, 6], [0, 0, 0], 6, 6, StateRole.Leader, False),
        Test([8, 6, 6], [1, 1, 0], 6, 6, StateRole.Leader, False),
        # Only leader knows what's the current state.
        Test([8, 2, 6], [1, 1, 2], 6, 6, StateRole.Follower, None),
        Test([8, 2, 6], [1, 1, 2], 6, 6, StateRole.Candidate, None),
        Test([8, 2, 6], [1, 1, 2], 6, 6, StateRole.PreCandidate, None),
    ]

    for i, v in enumerate(tests):
        matches, group_ids, committed, applied, role, exp = (
            v.matches,
            v.group_ids,
            v.committed,
            v.applied,
            v.role,
            v.exp,
        )
        store = MemStorage.new_with_conf_state(ConfState([1], []))
        store.wl().append(logs)
        hs = HardState.default()
        hs.set_term(2)
        hs.set_commit(committed)
        store.wl().set_hardstate(hs)
        cfg = new_test_config(1, 5, 1)
        cfg.set_applied(applied)
        sm = new_test_raft_with_config(cfg, store, l)
        sm.raft.set_state(role)

        groups = []
        for j, v in enumerate(zip(matches, group_ids)):
            m, g = v[0], v[1]
            id = j + 1
            if not sm.raft.prs().get(id):
                sm.raft.apply_conf_change(add_node(id))
                pr = sm.raft.prs().get(id)
                pr.set_matched(m)
                pr.set_next_idx(m + 1)
            if g != 0:
                groups.append((id, g))

        sm.raft.assign_commit_groups(groups)

        if exp:
            is_consistent = sm.raft.check_group_commit_consistent()
            assert (
                is_consistent == False
            ), f"#{i}: consistency = {is_consistent}, want Some(false)"
        sm.raft.enable_group_commit(True)

        is_consistent = sm.raft.check_group_commit_consistent()
        assert is_consistent == exp, f"#{i}: consistency = {is_consistent}, want {exp}"


# test_election_with_priority_log verifies the correctness
# of the election with both priority and log.
def test_election_with_priority_log():
    l = default_logger()

    class Test:
        def __init__(
            self,
            l1: bool,
            l2: bool,
            l3: bool,
            p1: int,
            p2: int,
            p3: int,
            id: int,
            state: StateRole,
        ) -> None:
            self.l1 = l1
            self.l2 = l2
            self.l3 = l3
            self.p1 = p1
            self.p2 = p2
            self.p3 = p3
            self.id = id
            self.state = state

    tests = [
        # log is up to date or not 1..3, priority 1..3, id, state
        Test(True, False, False, 3, 1, 1, 1, StateRole.Leader),
        Test(True, False, False, 2, 2, 2, 1, StateRole.Leader),
        Test(True, False, False, 1, 3, 3, 1, StateRole.Leader),
        Test(True, True, True, 3, 1, 1, 1, StateRole.Leader),
        Test(True, True, True, 2, 2, 2, 1, StateRole.Leader),
        Test(True, True, True, 1, 3, 3, 1, StateRole.Follower),
        Test(False, True, True, 3, 1, 1, 1, StateRole.Follower),
        Test(False, True, True, 2, 2, 2, 1, StateRole.Follower),
        Test(False, True, True, 1, 3, 3, 1, StateRole.Follower),
        Test(False, False, True, 1, 3, 3, 1, StateRole.Follower),
        Test(False, False, True, 1, 1, 3, 1, StateRole.Leader),
    ]

    for _i, v in enumerate(tests):
        l1, l2, l3, p1, p2, p3, id, state = (
            v.l1,
            v.l2,
            v.l3,
            v.p1,
            v.p2,
            v.p3,
            v.id,
            v.state,
        )
        s1, s2, s3 = new_storage(), new_storage(), new_storage()
        n1 = new_test_raft(1, [1, 2, 3], 10, 1, s1, l)
        n2 = new_test_raft(2, [1, 2, 3], 10, 1, s2, l)
        n3 = new_test_raft(3, [1, 2, 3], 10, 1, s3, l)

        n1.raft.set_priority(p1)
        n2.raft.set_priority(p2)
        n3.raft.set_priority(p3)

        entries = [new_entry(1, 1, SOME_DATA), new_entry(1, 1, SOME_DATA)]

        if l1:
            n1.raft_log.append(entries)
        if l2:
            n2.raft_log.append(entries)
        if l3:
            n3.raft_log.append(entries)

        network = Network.new([n1, n2, n3], l)
        network.send([new_message(id, id, MessageType.MsgHup, 0)])

        assert network.peers[id].raft.get_state() == state


# test_election_after_change_priority verifies that a peer can win an election
# by raising its priority and lose election by lowering its priority.
def test_election_after_change_priority():
    l = default_logger()
    s1, s2, s3 = new_storage(), new_storage(), new_storage()
    n1 = new_test_raft(1, [1, 2, 3], 10, 1, s1, l)
    n2 = new_test_raft(2, [1, 2, 3], 10, 1, s2, l)
    n3 = new_test_raft(3, [1, 2, 3], 10, 1, s3, l)

    # priority of n1 is 0 in default.
    n2.raft.set_priority(2)
    n3.raft.set_priority(3)
    n1.raft.become_follower(1, INVALID_ID)
    n2.raft.become_follower(1, INVALID_ID)
    n3.raft.become_follower(1, INVALID_ID)
    network = Network.new([n1, n2, n3], l)

    assert network.peers[1].raft.get_priority() == 0, "peer 1 priority"
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])
    # check state
    assert network.peers[1].raft.get_state() == StateRole.Follower, "peer 1 state"

    class Test:
        def __init__(self, id: int, p: int, state: StateRole) -> None:
            self.id = id
            self.p = p
            self.state = state

    tests = [
        Test(1, 1, StateRole.Follower),
        Test(1, 2, StateRole.Leader),
        Test(1, 3, StateRole.Leader),
        Test(1, 0, StateRole.Follower),
    ]

    for i, v in enumerate(tests):
        id, p, state = v.id, v.p, v.state
        network.peers[id].raft.become_follower(i + 2, INVALID_ID)
        network.peers[id].raft.set_priority(p)
        network.send([new_message(id, id, MessageType.MsgHup, 0)])

        # check state
        assert network.peers[id].raft.get_state() == state, f"peer {id} state"


# `test_read_when_quorum_becomes_less` tests read requests could be handled earlier
# if quorum becomes less in configuration changes.
def test_read_when_quorum_becomes_less():
    l = default_logger()
    network = Network.new([None, None], l)

    m = Message.default()
    m.set_from(1)
    m.set_to(1)
    m.set_msg_type(MessageType.MsgHup)
    network.send([m])
    assert network.peers[1].raft_log.get_committed() == 1

    # Read index on the peer.
    m = Message.default()
    m.set_to(1)
    m.set_msg_type(MessageType.MsgReadIndex)
    e = Entry.default()
    e.set_data(b"abcdefg")
    m.set_entries([e])
    network.dispatch([m])

    # Broadcast heartbeats.
    heartbeats = network.read_messages()
    network.dispatch(heartbeats)

    # Drop heartbeat response from peer 2.
    heartbeat_responses = network.read_messages()
    assert len(heartbeat_responses) == 1

    network.peers[1].raft.apply_conf_change(remove_node(2))
    assert network.peers[1].raft.get_read_states()


def test_uncommitted_entries_size_limit():
    l = default_logger()
    config = Config.default()
    config.set_id(1)
    config.set_max_uncommitted_size(12)
    nt = Network.new_with_config([None, None, None], config, l)
    data = b"hello world!"
    entry = Entry.default()
    entry.set_data(data)
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # should return ok
    nt.dispatch([msg.clone()])

    # then next proposal should be dropped
    with pytest.raises(ProposalDroppedError):
        nt.dispatch([msg])

    # but entry with empty size should be accepted
    entry = Entry.default()
    empty_msgs = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])
    nt.dispatch([empty_msgs])

    # after reduce, new proposal should be accepted
    entry = Entry.default()
    entry.set_data(data)
    entry.set_index(3)
    nt.peers[1].raft.reduce_uncommitted_size([entry]) == 0
    assert nt.peers[1].raft.uncommitted_size() == 0

    # a huge proposal should be accepted when there is no uncommitted entry,
    # even it's bigger than max_uncommitted_size
    entry = Entry.default()
    entry.set_data(b"hello world and raft")
    long_msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])
    nt.dispatch([long_msg])

    # but another huge one will be dropped
    entry = Entry.default()
    entry.set_data(b"hello world and raft")
    long_msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])
    with pytest.raises(ProposalDroppedError):
        nt.dispatch([long_msg])

    # entry with empty size should still be accepted
    entry = Entry.default()
    empty_msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])
    nt.dispatch([empty_msg])


def test_uncommitted_entry_after_leader_election():
    l = default_logger()
    config = Config.default()
    config.set_id(1)
    config.set_max_uncommitted_size(12)
    nt = Network.new_with_config([None, None, None, None, None], config, l)
    data = b"hello world!"
    entry = Entry.default()
    entry.set_data(data)
    msg = new_message_with_entries(1, 1, MessageType.MsgPropose, [entry])

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])

    # create a uncommitted entry on node2
    nt.cut(1, 3)
    nt.cut(1, 4)
    nt.cut(1, 5)
    nt.send([msg])

    # now isolate master and make node2 as master
    nt.isolate(1)
    # ignore message append, cluster only work on election
    nt.ignore(MessageType.MsgAppend)
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])

    # uncommitted log size should be 0 on node2,
    # because we set uncommitted size to 0 rather than re-computing it,
    # which means max_uncommitted_size is a soft limit
    assert nt.peers[2].raft.get_state() == StateRole.Leader
    assert nt.peers[2].raft.uncommitted_size() == 0


def test_uncommitted_state_advance_ready_from_last_term():
    l = default_logger()
    config = Config.default()
    config.set_id(1)
    config.set_max_uncommitted_size(12)
    nt = Network.new_with_config([None, None, None, None, None], config, l)

    data = b"hello world!"
    ent = Entry.default()
    ent.set_data(data)

    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    nt.send([new_message_with_entries(1, 1, MessageType.MsgPropose, [ent.clone()])])
    nt.send([new_message_with_entries(1, 1, MessageType.MsgPropose, [ent.clone()])])

    # now node2 has 2 committed entries
    # make node2 leader
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])
    assert nt.peers[2].raft.get_state() == StateRole.Leader

    nt.isolate(2)
    # create one uncommitted entry
    nt.send([new_message_with_entries(2, 2, MessageType.MsgPropose, [ent.clone()])])

    ent1 = ent.clone()
    ent1.set_index(1)
    ent2 = ent
    ent2.set_index(2)

    # simulate advance 2 entries when node2 is follower
    nt.peers[2].raft.reduce_uncommitted_size([ent1, ent2])

    # uncommitted size should be 12(remain unchanged since there's only one uncommitted entries)
    assert nt.peers[2].raft.uncommitted_size() == len(data)


def test_fast_log_rejection():
    class Test:
        def __init__(
            self,
            leader_log: List[int],
            follower_log: List[int],
            reject_hint_term: int,
            reject_hint_index: int,
            next_append_term: int,
            next_append_index: int,
        ) -> None:
            self.leader_log = leader_log
            self.follower_log = follower_log
            self.reject_hint_term = reject_hint_term
            self.reject_hint_index = reject_hint_index
            self.next_append_term = next_append_term
            self.next_append_index = next_append_index

    tests = [
        # This case tests that leader can find the conflict index quickly.
        # Firstly leader appends (type=MsgApp,index=7,logTerm=4, entries=...);
        # After rejected leader appends (type=MsgApp,index=3,logTerm=2).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(4, 4),
                empty_entry(4, 5),
                empty_entry(4, 6),
                empty_entry(4, 7),
            ],
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(3, 4),
                empty_entry(3, 5),
                empty_entry(3, 6),
                empty_entry(3, 7),
                empty_entry(3, 8),
                empty_entry(3, 9),
                empty_entry(3, 10),
                empty_entry(3, 11),
            ],
            3,
            7,
            2,
            3,
        ),
        # This case tests that leader can find the conflict index quickly.
        # Firstly leader appends (type=MsgApp,index=8,logTerm=5, entries=...);
        # After rejected leader appends (type=MsgApp,index=4,logTerm=3).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(3, 4),
                empty_entry(4, 5),
                empty_entry(4, 6),
                empty_entry(4, 7),
                empty_entry(5, 8),
            ],
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(3, 4),
                empty_entry(3, 5),
                empty_entry(3, 6),
                empty_entry(3, 7),
                empty_entry(3, 8),
                empty_entry(3, 9),
                empty_entry(3, 10),
                empty_entry(3, 11),
            ],
            3,
            8,
            3,
            4,
        ),
        # This case tests that follower can find the conflict index quickly.
        # Firstly leader appends (type=MsgApp,index=4,logTerm=1, entries=...);
        # After rejected leader appends (type=MsgApp,index=1,logTerm=1).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(1, 2),
                empty_entry(1, 3),
                empty_entry(1, 4),
            ],
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(4, 4),
            ],
            1,
            1,
            1,
            1,
        ),
        # This case is similar to the previous case. However, this time, the
        # leader has a longer uncommitted log tail than the follower.
        # Firstly leader appends (type=MsgApp,index=6,logTerm=1, entries=...);
        # After rejected leader appends (type=MsgApp,index=1,logTerm=1).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(1, 2),
                empty_entry(1, 3),
                empty_entry(1, 4),
                empty_entry(1, 5),
                empty_entry(1, 6),
            ],
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(4, 4),
            ],
            1,
            1,
            1,
            1,
        ),
        # This case is similar to the previous case. However, this time, the
        # follower has a longer uncommitted log tail than the leader.
        # Firstly leader appends (type=MsgApp,index=4,logTerm=1, entries=...);
        # After rejected leader appends (type=MsgApp,index=1,logTerm=1).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(1, 2),
                empty_entry(1, 3),
                empty_entry(1, 4),
            ],
            [
                empty_entry(1, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(4, 4),
                empty_entry(4, 5),
                empty_entry(4, 6),
            ],
            1,
            1,
            1,
            1,
        ),
        # An normal case that there are no log conflicts.
        # Firstly leader appends (type=MsgApp,index=5,logTerm=5, entries=...);
        # After rejected leader appends (type=MsgApp,index=4,logTerm=4).
        Test(
            [
                empty_entry(1, 1),
                empty_entry(1, 2),
                empty_entry(1, 3),
                empty_entry(4, 4),
                empty_entry(5, 5),
            ],
            [
                empty_entry(1, 1),
                empty_entry(1, 2),
                empty_entry(1, 3),
                empty_entry(4, 4),
            ],
            4,
            4,
            4,
            4,
        ),
        # Test case from example comment in stepLeader (on leader).
        Test(
            [
                empty_entry(2, 1),
                empty_entry(5, 2),
                empty_entry(5, 3),
                empty_entry(5, 4),
                empty_entry(5, 5),
                empty_entry(5, 6),
                empty_entry(5, 7),
                empty_entry(5, 8),
                empty_entry(5, 9),
            ],
            [
                empty_entry(2, 1),
                empty_entry(4, 2),
                empty_entry(4, 3),
                empty_entry(4, 4),
                empty_entry(4, 5),
                empty_entry(4, 6),
            ],
            4,
            6,
            2,
            1,
        ),
        # Test case from example comment in handleAppendEntries (on follower).
        Test(
            [
                empty_entry(2, 1),
                empty_entry(2, 2),
                empty_entry(2, 3),
                empty_entry(2, 4),
                empty_entry(2, 5),
            ],
            [
                empty_entry(2, 1),
                empty_entry(4, 2),
                empty_entry(4, 3),
                empty_entry(4, 4),
                empty_entry(4, 5),
                empty_entry(4, 6),
                empty_entry(4, 7),
                empty_entry(4, 8),
            ],
            2,
            1,
            2,
            1,
        ),
    ]

    for i, v in enumerate(tests):
        (
            leader_log,
            follower_log,
            reject_hint_term,
            reject_hint_index,
            next_append_term,
            next_append_index,
        ) = (
            v.leader_log,
            v.follower_log,
            v.reject_hint_term,
            v.reject_hint_index,
            v.next_append_term,
            v.next_append_index,
        )
        l = default_logger()
        s1 = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
        s1.wl().append(leader_log)

        s2 = MemStorage.new_with_conf_state(ConfState([1, 2, 3], []))
        s2.wl().append(follower_log)

        n1 = new_test_raft(1, [1, 2, 3], 10, 1, s1, l)
        n2 = new_test_raft(2, [1, 2, 3], 10, 1, s2, l)

        n1.raft.become_candidate()
        n1.raft.become_leader()

        n2.step(new_message(2, 1, MessageType.MsgHeartbeat, 0))

        msgs = n2.read_messages()
        assert len(msgs) == 1, f"{i}"
        assert msgs[0].get_msg_type() == MessageType.MsgHeartbeatResponse, f"{i}"

        # move Vec item by pop
        n1.step(msgs.pop())

        msgs = n1.read_messages()
        assert len(msgs) == 1, f"{i}"
        assert msgs[0].get_msg_type() == MessageType.MsgAppend, f"{i}"
        n2.step(msgs.pop())

        msgs = n2.read_messages()
        assert len(msgs) == 1, f"{i}"
        assert msgs[0].get_msg_type() == MessageType.MsgAppendResponse, f"{i}"
        assert msgs[0].get_reject(), f"{i}"
        assert msgs[0].get_reject_hint() == reject_hint_index, f"{i}"
        assert msgs[0].get_log_term() == reject_hint_term, f"{i}"
        n1.step(msgs.pop())

        msgs = n1.read_messages()
        assert len(msgs) == 1, f"{i}"
        assert msgs[0].get_log_term() == next_append_term, f"{i}"
        assert msgs[0].get_index() == next_append_index, f"{i}"


def test_switching_check_quorum():
    l = default_logger()
    s = new_storage()
    sm = new_test_raft(1, [1, 2, 3], 5, 1, s, l)

    sm.raft.set_check_quorum(True)
    sm.raft.become_candidate()
    sm.raft.become_leader()
    for _ in range(0, sm.raft.election_timeout() + 1):
        sm.raft.tick()

    assert sm.raft.get_state() != StateRole.Leader

    sm.persist()
    sm.raft.set_check_quorum(False)
    sm.raft.become_candidate()
    sm.raft.become_leader()

    for _ in range(0, sm.raft.election_timeout() + 1):
        sm.raft.tick()

    assert sm.raft.get_state() == StateRole.Leader
