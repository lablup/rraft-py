import os
import sys
import pytest
from typing import Any, List
from test_utils import (
    new_test_raft_with_prevote,
    new_storage,
    new_message,
    new_message_with_entries,
    new_test_raft,
    new_test_config,
    new_test_raft_with_config,
    new_entry,
    # Interface,
    # Network,
)

from rraft import (
    ConfState_Owner,
    Entry_Owner,
    Logger_Ref,
    MemStorage_Owner,
    MemStorage_Ref,
    MemStorageCore_Ref,
    Message_Owner,
    MessageType,
    ProgressState,
    Raft__MemStorage_Owner,
    Raft__MemStorage_Ref,
    RaftLog__MemStorage_Ref,
    StateRole,
    default_logger,
    vote_resp_msg_type,
    INVALID_ID,
)

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "../src"))
sys.path.append(parent_dir)
from interface import Interface
from network import Network


def read_messages(raft: Raft__MemStorage_Owner) -> List[Message_Owner]:
    return raft.make_ref().take_msgs()


def ents_with_config(
    terms: List[int],
    pre_vote: bool,
    id: int,
    peers: List[int],
    l: Logger_Ref,
) -> Interface:
    cs = ConfState_Owner(peers, [])
    store = MemStorage_Owner.new_with_conf_state(cs.make_ref())

    for i, term in enumerate(terms):
        e = Entry_Owner.default()
        e.make_ref().set_index(i + 1)
        e.make_ref().set_term(term)
        store.make_ref().wl(lambda core: core.append([e]))

    raft = new_test_raft_with_prevote(id, peers, 5, 1, store.make_ref(), pre_vote, l)
    raft.raft.make_ref().reset(terms[-1])
    return raft


def assert_raft_log(
    prefix: str,
    raft_log: RaftLog__MemStorage_Ref,
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
    l: Logger_Ref,
) -> Interface:
    cs = ConfState_Owner(peers, [])
    store = MemStorage_Owner.new_with_conf_state(cs.make_ref())

    def hard_state_set_vote(core: MemStorageCore_Ref):
        core.hard_state().set_vote(vote)

    def hard_state_set_term(core: MemStorageCore_Ref):
        core.hard_state().set_term(term)

    store.make_ref().wl(hard_state_set_vote)
    store.make_ref().wl(hard_state_set_term)

    raft = new_test_raft_with_prevote(id, peers, 5, 1, store.make_ref(), pre_vote, l)
    raft.raft.make_ref().reset(term)
    return raft


# Persist committed index and fetch next entries.
def next_ents(r: Raft__MemStorage_Ref, s: MemStorage_Ref) -> List[Entry_Owner]:
    unstable_refs = r.get_raft_log().unstable_entries()
    unstable = list(map(lambda e: e.clone(), unstable_refs))

    if unstable:
        e = unstable[-1]
        last_idx, last_term = e.make_ref().get_index(), e.make_ref().get_term()
        r.get_raft_log().stable_entries(last_idx, last_term)
        s.wl(lambda core: core.append(unstable))
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
    assert nt.peers.get(1).raft.make_ref().get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft.make_ref().get_raft_log(), 1, 0, 1)
    assert_raft_log("#2: ", nt.peers.get(2).raft.make_ref().get_raft_log(), 1, 0, 1)
    assert_raft_log("#3: ", nt.peers.get(3).raft.make_ref().get_raft_log(), 1, 0, 1)

    assert nt.peers.get(1).raft.make_ref().prs().get(1).get_committed_index() == 1
    assert nt.peers.get(1).raft.make_ref().prs().get(2).get_committed_index() == 1
    assert nt.peers.get(1).raft.make_ref().prs().get(3).get_committed_index() == 1

    # #1 test append entries
    # append entries between 1 and 2
    test_entries = Entry_Owner.default()
    test_entries.make_ref().set_data(list(b"testdata"))
    m = new_message_with_entries(1, 1, MessageType.MsgPropose, [test_entries])
    nt.cut(1, 3)
    nt.send([m.clone(), m])
    nt.recover()

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 3, 0, 3)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 3, 0, 3)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 1, 0, 1)

    assert nt.peers.get(1).raft.make_ref().prs().get(1).get_committed_index() == 3
    assert nt.peers.get(1).raft.make_ref().prs().get(2).get_committed_index() == 3
    assert nt.peers.get(1).raft.make_ref().prs().get(3).get_committed_index() == 1

    # #2 test heartbeat
    heartbeat = new_message(1, 1, MessageType.MsgBeat, 0)
    nt.send([heartbeat])

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 3, 0, 3)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 3, 0, 3)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 3, 0, 3)

    # set node 2 as Leader
    nt.send([new_message(2, 2, MessageType.MsgHup, 0)])
    assert nt.peers.get(2).raft.make_ref().get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 4, 0, 4)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 4, 0, 4)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 4, 0, 4)

    assert nt.peers.get(2).raft.make_ref().prs().get(1).get_committed_index() == 4
    assert nt.peers.get(2).raft.make_ref().prs().get(2).get_committed_index() == 4
    assert nt.peers.get(2).raft.make_ref().prs().get(3).get_committed_index() == 4

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
    assert nt.peers.get(2).raft.make_ref().prs().get(1).get_committed_index() == 4
    assert nt.peers.get(2).raft.make_ref().prs().get(2).get_committed_index() == 4
    assert nt.peers.get(2).raft.make_ref().prs().get(3).get_committed_index() == 4

    # resend append
    nt.send(msg_append)

    # log is up-to-date
    assert nt.peers.get(2).raft.make_ref().prs().get(1).get_committed_index() == 7
    assert nt.peers.get(2).raft.make_ref().prs().get(2).get_committed_index() == 7
    assert nt.peers.get(2).raft.make_ref().prs().get(3).get_committed_index() == 7

    # set node 1 as Leader again
    nt.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert nt.peers.get(1).raft.make_ref().get_state() == StateRole.Leader

    assert_raft_log("#1: ", nt.peers.get(1).raft_log, 8, 0, 8)
    assert_raft_log("#2: ", nt.peers.get(2).raft_log, 8, 0, 8)
    assert_raft_log("#3: ", nt.peers.get(3).raft_log, 8, 0, 8)

    # update to 8
    assert nt.peers.get(1).raft.make_ref().prs().get(1).get_committed_index() == 8
    assert nt.peers.get(1).raft.make_ref().prs().get(2).get_committed_index() == 8
    assert nt.peers.get(1).raft.make_ref().prs().get(3).get_committed_index() == 8

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

    assert nt.peers.get(1).raft.make_ref().prs().get(1).get_committed_index() == 10
    assert nt.peers.get(1).raft.make_ref().prs().get(2).get_committed_index() == 10
    assert nt.peers.get(1).raft.make_ref().prs().get(3).get_committed_index() == 10

    # committed index remain 10

    # msg_type: MsgAppendResponse to: 1 from: 2 term: 3 index: 10 commit: 9,
    # msg_type: MsgAppendResponse to: 1 from: 3 term: 3 index: 10 commit: 9
    nt.send(msg_append_response)
    assert nt.peers.get(1).raft.make_ref().prs().get(1).get_committed_index() == 10
    assert nt.peers.get(1).raft.make_ref().prs().get(2).get_committed_index() == 10
    assert nt.peers.get(1).raft.make_ref().prs().get(3).get_committed_index() == 10


def test_progress_leader():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2], 5, 1, storage.make_ref(), l.make_ref())
    raft.raft.make_ref().become_candidate()
    raft.raft.make_ref().become_leader()
    # For no-op entry
    raft.persist()
    raft.raft.make_ref().prs().get(2).become_replicate()

    prop_msg = new_message(1, 1, MessageType.MsgPropose, 1)
    for i in range(0, 5):
        assert raft.raft.make_ref().prs().get(1).get_state() == ProgressState.Replicate

        matched = raft.raft.make_ref().prs().get(1).get_matched()
        next_idx = raft.raft.make_ref().prs().get(1).get_next_idx()
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
    raft = new_test_raft(1, [1, 2], 5, 1, storage.make_ref(), l.make_ref())
    raft.raft.make_ref().become_candidate()
    raft.raft.make_ref().become_leader()
    raft.raft.make_ref().prs().get(2).set_paused(True)

    raft.step(new_message(1, 1, MessageType.MsgBeat, 0))
    assert raft.raft.make_ref().prs().get(2).get_paused()
    raft.raft.make_ref().prs().get(2).become_replicate()
    raft.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
    assert not raft.raft.make_ref().prs().get(2).get_paused()


def test_progress_paused():
    l = default_logger()
    storage = new_storage()
    raft = new_test_raft(1, [1, 2], 5, 1, storage.make_ref(), l.make_ref())
    raft.raft.make_ref().become_candidate()
    raft.raft.make_ref().become_leader()

    m = Message_Owner.default()
    m.make_ref().set_from(1)
    m.make_ref().set_to(1)
    m.make_ref().set_msg_type(MessageType.MsgPropose)

    e = Entry_Owner.default()
    e.make_ref().set_data(list(b"some_data"))
    m.make_ref().set_entries([e])

    raft.step(m.clone())
    raft.step(m.clone())
    raft.step(m)

    ms = read_messages(raft.raft)
    assert len(ms) == 1


def test_progress_flow_control():
    l = default_logger()
    cfg = new_test_config(1, 5, 1)
    cfg.make_ref().set_max_inflight_msgs(3)
    cfg.make_ref().set_max_size_per_msg(2048)
    cs = ConfState_Owner([1, 2], [])
    s = MemStorage_Owner.new_with_conf_state(cs.make_ref())

    r = new_test_raft_with_config(cfg.make_ref(), s.make_ref(), l.make_ref())
    r.raft.make_ref().become_candidate()
    r.raft.make_ref().become_leader()

    # Throw away all the messages relating to the initial election.
    r.read_messages()

    # While node 2 is in probe state, propose a bunch of entries.
    r.raft.make_ref().prs().get(2).become_probe()
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
    assert ms[0].make_ref().get_msg_type() == MessageType.MsgAppend
    assert len(ms[0].make_ref().get_entries()) == 2
    assert len(ms[0].make_ref().get_entries()[0].get_data()) == 0
    assert len(ms[0].make_ref().get_entries()[1].get_data()) == 1000

    # When this append is acked, we change to replicate state and can
    # send multiple messages at once.
    msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    msg.make_ref().set_index(ms[0].make_ref().get_entries()[1].get_index())
    r.step(msg)
    ms = r.read_messages()
    assert len(ms) == 3

    for i, m in enumerate(ms):
        assert (
            m.make_ref().get_msg_type() == MessageType.MsgAppend
        ), f"{i}: expected MsgAppend, got {m.make_ref().get_msg_type()}"

        assert (
            len(m.make_ref().get_entries()) == 2
        ), f"{i}: expected 2 entries, got {len(m.make_ref().get_entries())}"

    # Ack all three of those messages together and get the last two
    # messages (containing three entries).
    msg = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    msg.make_ref().set_index(ms[2].make_ref().get_entries()[1].get_index())
    r.step(msg)
    ms = r.read_messages()
    assert len(ms) == 2

    for i, m in enumerate(ms):
        assert (
            m.make_ref().get_msg_type() == MessageType.MsgAppend
        ), f"{i}: expected MsgAppend, got {m.make_ref().get_msg_type()}"

    assert len(ms[0].make_ref().get_entries()) == 2
    assert len(ms[1].make_ref().get_entries()) == 1


# test_leader_election
# test_leader_election_pre_vote
@pytest.mark.parametrize("pre_vote", [True, False])
def test_leader_election_with_config(pre_vote: bool):
    l = default_logger()
    config = Network.default_config()
    config.make_ref().set_pre_vote(pre_vote)

    class Test:
        def __init__(self, network: Any, state: StateRole, term: int) -> None:
            self.network = network
            self.state = state
            self.term = term

    NOP_STEPPER = Interface(None)

    tests = [
        Test(
            Network.new_with_config([None, None, None], config.make_ref(), l),
            StateRole.Leader,
            1,
        ),
        Test(
            Network.new_with_config([None, None, NOP_STEPPER], config.make_ref(), l),
            StateRole.Leader,
            1,
        ),
        Test(
            Network.new_with_config(
                [None, NOP_STEPPER, NOP_STEPPER], config.make_ref(), l
            ),
            StateRole.Candidate,
            1,
        ),
        Test(
            Network.new_with_config(
                [None, NOP_STEPPER, NOP_STEPPER, None], config.make_ref(), l
            ),
            StateRole.Candidate,
            1,
        ),
        Test(
            Network.new_with_config(
                [None, NOP_STEPPER, NOP_STEPPER, None, None], config.make_ref(), l
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
                    ents_with_config([1], pre_vote, 2, [1, 2, 3, 4, 5], l.make_ref()),
                    ents_with_config([1], pre_vote, 3, [1, 2, 3, 4, 5], l.make_ref()),
                    ents_with_config(
                        [1, 1], pre_vote, 4, [1, 2, 3, 4, 5], l.make_ref()
                    ),
                    None,
                ],
                config.make_ref(),
                l,
            ),
            StateRole.Follower,
            1,
        ),
    ]

    for i, v in enumerate(tests):
        network, state, term = v.network, v.state, v.term
        m = Message_Owner.default()
        m.make_ref().set_from(1)
        m.make_ref().set_to(1)
        m.make_ref().set_msg_type(MessageType.MsgHup)
        network.send([m])
        raft = network.peers.get(1)

        exp_state, exp_term = state, term
        if state == StateRole.Candidate and pre_vote:
            # In pre-vote mode, an election that fails to complete
            # leaves the node in pre-candidate state without advancing
            # the term.
            exp_state, exp_term = StateRole.PreCandidate, 0

        assert (
            raft.raft.make_ref().get_state() == exp_state
        ), f"#{i}: state = {raft.raft.make_ref().get_state()}, want {exp_state}"

        assert (
            raft.raft.make_ref().get_term() == exp_term
        ), f"#{i}: term = {raft.raft.make_ref().get_term()}, want {exp_term}"


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
    config.make_ref().set_pre_vote(pre_vote)

    network = Network.new_with_config([None, None, None], config.make_ref(), l)

    for campaigner_id in range(1, 4):
        network.send([new_message(campaigner_id, campaigner_id, MessageType.MsgHup, 0)])

        for sm in network.peers.values():
            assert not (
                sm.raft.make_ref().get_id() == campaigner_id
                and sm.raft.make_ref().get_state() != StateRole.Leader
            ), f"pre_vote={pre_vote}: campaigning node {sm.raft.make_ref().get_id()} state = {sm.raft.make_ref().get_state()}, want Leader"

            assert not (
                sm.raft.make_ref().get_id() != campaigner_id
                and sm.raft.make_ref().get_state() != StateRole.Follower
            ), f"pre_vote={pre_vote}: after campaign of node {campaigner_id}, node {sm.raft.make_ref().get_id()} had state = {sm.raft.make_ref().get_state()}, want \
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
    config.make_ref().set_pre_vote(pre_vote)
    network = Network.new_with_config(
        [
            # Node 1: Won first election
            ents_with_config([1], pre_vote, 1, peers, l.make_ref()),
            # Node 2: Get logs from node 1
            ents_with_config([1], pre_vote, 2, peers, l.make_ref()),
            # Node 3: Won second election
            ents_with_config([2], pre_vote, 3, peers, l.make_ref()),
            # Node 4: Voted but didn't get logs
            voted_with_config(3, 2, pre_vote, 4, peers, l.make_ref()),
            # Node 5: Voted but didn't get logs
            voted_with_config(3, 2, pre_vote, 5, peers, l.make_ref()),
        ],
        config.make_ref(),
        l,
    )

    # Node 1 campaigns. The election fails because a quorum of nodes
    # know about the election that already happened at term 2. Node 1's
    # term is pushed ahead to 2.
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert network.peers.get(1).raft.make_ref().get_state() == StateRole.Follower
    assert network.peers.get(1).raft.make_ref().get_term() == 2

    # Node 1 campaigns again with a higher term. this time it succeeds.
    network.send([new_message(1, 1, MessageType.MsgHup, 0)])
    assert network.peers.get(1).raft.make_ref().get_state() == StateRole.Leader
    assert network.peers.get(1).raft.make_ref().get_term() == 3

    # Now all nodes agree on a log entry with term 1 at index 1 (and
    # term 3 at index 2).
    for id, sm in network.peers.items():
        entries = sm.raft_log.all_entries()
        assert len(entries) == 2, f"node {id}: entries.len() == {len(entries)}, want 2"

        assert (
            entries[0].make_ref().get_term() == 1
        ), f"node {id}: term at index 1 == {entries[0].make_ref().get_term()}, want 1"

        assert (
            entries[1].make_ref().get_term() == 3
        ), f"node {id}: term at index 2 == {entries[1].make_ref().get_term()}, want 3"


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
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l.make_ref())
        r.raft.make_ref().set_term(1)
        if state == StateRole.Follower:
            term = r.raft.make_ref().get_term()
            r.raft.make_ref().become_follower(term, 3)
        elif state == StateRole.PreCandidate:
            r.raft.make_ref().become_pre_candidate()
        elif state == StateRole.Candidate:
            r.raft.make_ref().become_candidate()
        else:
            r.raft.make_ref().become_candidate()
            r.raft.make_ref().become_leader()

        # Note that setting our state above may have advanced r.term
        # past its initial value.
        orig_term = r.raft.make_ref().get_term()
        new_term = r.raft.make_ref().get_term() + 1

        msg = new_message(2, 1, vt, 0)
        msg.make_ref().set_term(new_term)
        msg.make_ref().set_log_term(orig_term)
        msg.make_ref().set_index(42)
        r.step(msg.make_ref())

        assert (
            len(r.raft.make_ref().get_msgs()) == 1
        ), f"{vt},{state}: {len(r.raft.make_ref().get_msgs())} response messages, want 1: {r.raft.make_ref().get_msgs()}"

        resp = r.raft.make_ref().get_msgs()[0]

        assert resp.get_msg_type() == vote_resp_msg_type(
            vt
        ), f"{vt},{state}: response message is {resp.get_msg_type()}, want {vote_resp_msg_type(vt)}"

        assert not resp.get_reject(), f"{vt},{state}: unexpected rejection"

        # If this was a real vote, we reset our state and term.
        if vt == MessageType.MsgRequestVote:
            assert (
                r.raft.make_ref().get_state() == StateRole.Follower
            ), f"{vt},{state}, state is {r.raft.make_ref().get_state()}, want {StateRole.Follower}"

            assert (
                r.raft.make_ref().get_term() == new_term
            ), f"{vt},{state}, term is {r.raft.make_ref().get_term()}, want {new_term}"

            assert (
                r.raft.make_ref().get_vote() == 2
            ), f"{vt},{state}, vote {r.raft.make_ref().get_vote()}, want 2"
        else:
            # In a pre-vote, nothing changes.
            assert (
                r.raft.make_ref().get_state() == state
            ), f"{vt},{state}, state {r.raft.make_ref().get_state()}, want {state}"

            assert (
                r.raft.make_ref().get_term() == orig_term
            ), f"{vt},{state}, term {r.raft.make_ref().get_term()}, want {orig_term}"

            # If state == Follower or PreCandidate, r hasn't voted yet.
            # In Candidate or Leader, it's voted for itself.
            assert (
                r.raft.make_ref().get_vote() == INVALID_ID
                or r.raft.make_ref().get_vote() == 1
            ), f"{vt},{state}, vote {r.raft.make_ref().get_vote()}, want {INVALID_ID} or 1"


def test_log_replication():
    l = default_logger()

    class Test:
        def __init__(
            self, network: Network, msgs: List[Message_Owner], wcommitted: int
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

            ents = next_ents(x.raft.make_ref(), network.storage.get(j))
            ents = list(filter(lambda x: len(x.make_ref().get_data()) != 0, ents))

            for k, m in enumerate(
                filter(
                    lambda msg: msg.make_ref().get_msg_type() == MessageType.MsgPropose,
                    msgs,
                )
            ):
                assert (
                    ents[k].make_ref().get_data()
                    == m.make_ref().get_entries()[0].get_data()
                ), f"#{i}.{j}: data = {ents[k].make_ref().get_data()}, want {m.make_ref().get_entries()[0].get_data()}"


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
    pass


def test_dueling_candidates():
    pass


def test_dueling_pre_candidates():
    pass


def test_candidate_concede():
    pass


def test_single_node_candidate():
    pass


def test_sinle_node_pre_candidate():
    pass


def test_old_messages():
    pass


def test_proposal():
    pass


def test_proposal_by_proxy():
    pass


def test_commit():
    pass


def test_pass_election_timeout():
    pass


# test_handle_msg_append ensures:
# 1. Reply false if log doesn’t contain an entry at prevLogIndex whose term matches prevLogTerm.
# 2. If an existing entry conflicts with a new one (same index but different terms),
#    delete the existing entry and all that follow it; append any new entries not already in the
#    log.
# 3. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry).
def test_handle_msg_append():
    pass


# test_handle_heartbeat ensures that the follower commits to the commit in the message.
def test_handle_heartbeat():
    pass


# test_handle_heartbeat_resp ensures that we re-send log entries when we get a heartbeat response.
def test_handle_heartbeat_resp():
    pass


# test_raft_frees_read_only_mem ensures raft will free read request from
# ReadOnly read_index_queue and pending_read_index map.
# related issue: https://github.com/coreos/etcd/issues/7571
def test_raft_frees_read_only_mem():
    pass


# test_msg_append_response_wait_reset verifies the waitReset behavior of a leader
# MsgAppResp.
def test_msg_append_response_wait_reset():
    pass


def test_recv_msg_request_vote():
    pass


def test_recv_msg_request_vote_for_type():
    pass


def test_state_transition():
    pass


def test_all_server_stepdown():
    pass


def test_candidate_reset_term_msg_heartbeat():
    pass


def test_candidate_reset_term_msg_append():
    pass


# test_candidate_reset_term tests when a candidate receives a
# MsgHeartbeat or MsgAppend from leader, "step" resets the term
# with leader's and reverts back to follower.
def test_candidate_reset_term():
    pass


def test_leader_stepdown_when_quorum_active():
    pass


def test_leader_stepdown_when_quorum_lost():
    pass


def test_leader_superseding_with_check_quorum():
    pass


def test_leader_election_with_check_quorum():
    pass


# test_free_stuck_candidate_with_check_quorum ensures that a candidate with a higher term
# can disrupt the leader even if the leader still "officially" holds the lease, The
# leader is expected to step down and adopt the candidate's term
def test_free_stuck_candidate_with_check_quorum():
    pass


def test_non_promotable_voter_with_check_quorum():
    pass


# `test_disruptive_follower` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a candidate with an increased term. Then, the
# candiate's response to late leader heartbeat forces the leader
def test_disruptive_follower():
    pass


# `test_disruptive_follower_pre_vote` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a pre-candidate with less log than current leader.
# Then pre-vote phase prevents this isolated node from forcing
# current leader to step down, thus less disruptions.
def test_disruptive_follower_pre_vote():
    pass


def test_read_only_option_safe():
    pass


def test_read_only_with_learner():
    pass


def test_read_only_option_lease():
    pass


def test_read_only_option_lease_without_check_quorum():
    pass


# `test_read_only_for_new_leader` ensures that a leader only accepts MsgReadIndex message
# when it commits at least one log entry at it term.
def test_read_only_for_new_leader():
    pass


# `test_advance_commit_index_by_read_index_response` ensures that read index response
# can advance the follower's commit index if it has new enough logs
def test_advance_commit_index_by_read_index_response():
    pass


def test_leader_append_response():
    pass


# When the leader receives a heartbeat tick, it should
# send a MsgApp with m.Index = 0, m.LogTerm=0 and empty entries.
def test_bcast_beat():
    pass


# tests the output of the statemachine when receiving MsgBeat
def test_recv_msg_beat():
    pass


def test_leader_increase_next():
    pass


def test_send_append_for_progress_probe():
    pass


def test_send_append_for_progress_replicate():
    pass


def test_send_append_for_progress_snapshot():
    pass


def test_recv_msg_unreachable():
    pass


def test_restore():
    pass


def test_restore_ignore_snapshot():
    pass


def test_provide_snap():
    pass


def test_ignore_providing_snapshot():
    pass


def test_restore_from_snap_msg():
    pass


def test_slow_node_restore():
    pass


# test_step_config tests that when raft step msgProp in EntryConfChange type,
# it appends the entry to log and sets pendingConf to be true.
def test_step_config():
    pass


def test_step_ignore_config():
    pass


# test_new_leader_pending_config tests that new leader sets its pending_conf_index
# based on uncommitted entries.
def test_new_leader_pending_config():
    pass


# test_add_node tests that add_node could update nodes correctly.
def test_add_node():
    pass


def test_add_node_check_quorum():
    pass


# test_remove_node tests that removeNode could update pendingConf, nodes and
# and removed list correctly.
def test_remove_node():
    pass


def test_remove_node_itself():
    pass


def test_promotable():
    pass


def test_raft_nodes():
    pass


def test_campaign_while_leader():
    pass


def test_campaign_while_leader_with_pre_vote():
    pass


# test_commit_after_remove_node verifies that pending commands can become
# committed when a config change reduces the quorum requirements.
def test_commit_after_remove_node():
    pass


# test_leader_transfer_to_uptodate_node verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
def test_leader_transfer_to_uptodate_node():
    pass


# test_leader_transfer_to_uptodate_node_from_follower verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
# Not like test_leader_transfer_to_uptodate_node, where the leader transfer message
# is sent to the leader, in this test case every leader transfer message is sent
# to the follower.
def test_leader_transfer_to_uptodate_node_from_follower():
    pass


# TestLeaderTransferWithCheckQuorum ensures transferring leader still works
# even the current leader is still under its leader lease
def test_leader_transfer_with_check_quorum():
    pass


def test_leader_transfer_to_slow_follower():
    pass


def test_leader_transfer_after_snapshot():
    pass


def test_leader_transfer_to_self():
    pass


def test_leader_transfer_to_non_existing_node():
    pass


def test_leader_transfer_to_learner():
    pass


def test_leader_transfer_timeout():
    pass


def test_leader_transfer_ignore_proposal():
    pass


def test_leader_transfer_receive_higher_term_vote():
    pass


def test_leader_transfer_remove_node():
    pass


# test_leader_transfer_back verifies leadership can transfer
# back to self when last transfer is pending.
def test_leader_transfer_back():
    pass


# test_leader_transfer_second_transfer_to_another_node verifies leader can transfer to another node
# when last transfer is pending.
def test_leader_transfer_second_transfer_to_another_node():
    pass


# test_leader_transfer_second_transfer_to_same_node verifies second transfer leader request
# to the same node should not extend the timeout while the first one is pending.
def test_leader_transfer_second_transfer_to_same_node():
    pass


def check_leader_transfer_state():
    pass


# test_transfer_non_member verifies that when a MsgTimeoutNow arrives at
# a node that has been removed from the group, nothing happens.
# (previously, if the node also got votes, it would panic as it
# transitioned to StateRole::Leader)
def test_transfer_non_member():
    pass


# TestNodeWithSmallerTermCanCompleteElection tests the scenario where a node
# that has been partitioned away (and fallen behind) rejoins the cluster at
# about the same time the leader node gets partitioned away.
# Previously the cluster would come to a standstill when run with PreVote
# enabled.
def test_node_with_smaller_term_can_complete_election():
    pass


def new_test_learner_raft():
    pass


def new_test_learner_raft_with_prevote():
    pass


# TestLearnerElectionTimeout verifies that the leader should not start election
# even when times out.
def test_learner_election_timeout():
    pass


# TestLearnerPromotion verifies that the leaner should not election until
# it is promoted to a normal peer.
def test_learner_promotion():
    pass


# TestLearnerLogReplication tests that a learner can receive entries from the leader.
def test_learner_log_replication():
    pass


# TestRestoreWithLearner restores a snapshot which contains learners.
def test_restore_with_learner():
    pass


# Tests if outgoing voters can restore snapshot correctly.
def test_restore_with_voters_outgoing():
    pass


# Verifies that a voter can be depromoted by snapshot.
def test_restore_depromote_voter():
    pass


def test_restore_learner():
    pass


# TestRestoreLearnerPromotion checks that a learner can become to a follower after
# restoring snapshot.
def test_restore_learner_promotion():
    pass


# TestLearnerReceiveSnapshot tests that a learner can receive a snapshot from leader.
def test_learner_receive_snapshot():
    pass


# TestAddLearner tests that addLearner could update nodes correctly.
def test_add_learner():
    pass


# TestRemoveLearner tests that removeNode could update nodes and
# and removed list correctly.
def test_remove_learner():
    pass


# simulate rolling update a cluster for Pre-Vote. cluster has 3 nodes [n1, n2, n3].
# n1 is leader with term 2
# n2 is follower with term 2
# n3 is partitioned, with term 4 and less log, state is candidate
def new_prevote_migration_cluster():
    pass


def test_prevote_migration_can_complete_election():
    pass


def test_prevote_migration_with_free_stuck_pre_candidate():
    pass


def test_learner_respond_vote():
    pass


def test_election_tick_range():
    pass


# TestPreVoteWithSplitVote verifies that after split vote, cluster can complete
# election in next round.
def test_prevote_with_split_vote():
    pass


# ensure that after a node become pre-candidate, it will checkQuorum correctly.
def test_prevote_with_check_quorum():
    pass


# ensure a new Raft returns a Error::ConfigInvalid with an invalid config
def test_new_raft_with_bad_config_errors():
    pass


# tests whether MsgAppend are batched
def test_batch_msg_append():
    pass


# Tests if unapplied conf change is checked before campaign.
def test_conf_change_check_before_campaign():
    pass


def test_advance_commit_index_by_vote_request():
    pass


def test_advance_commit_index_by_direct_vote_request():
    pass


# Tests the commit index can be advanced by direct vote request
def test_advance_commit_index_by_prevote_request():
    pass


# Tests the commit index can be advanced by prevote request
def test_advance_commit_index_by_vote_response():
    pass


# Tests the commit index can be forwarded by direct vote response
def test_advance_commit_index_by_direct_vote_response():
    pass


# Tests the commit index can be forwarded by prevote response
def test_advance_commit_index_by_prevote_response():
    pass


def prepare_request_snapshot():
    pass


# Test if an up-to-date follower can request a snapshot from leader.
def test_follower_request_snapshot():
    pass


# Test if request snapshot can make progress when it meets SnapshotTemporarilyUnavailable.
def test_request_snapshot_unavailable():
    pass


# Test if request snapshot can make progress when matched is advanced.
def test_request_snapshot_matched_change():
    pass


# Test if request snapshot can make progress when the peer is not Replicate.
def test_request_snapshot_none_replicate():
    pass


# Test if request snapshot can make progress when leader steps down.
def test_request_snapshot_step_down():
    pass


# Abort request snapshot if it becomes leader or candidate.
def test_request_snapshot_on_role_change():
    pass


# Tests group commit.
#
# 1. Logs should be replicated to at least different groups before committed;
# 2. all peers are configured to the same group, simple quorum should be used.
def test_group_commit():
    pass


def test_group_commit_consistent():
    pass


# test_election_with_priority_log verifies the correctness
# of the election with both priority and log.
def test_election_with_priority_log():
    pass


# test_election_after_change_priority verifies that a peer can win an election
# by raising its priority and lose election by lowering its priority.
def test_election_after_change_priority():
    pass


# `test_read_when_quorum_becomes_less` tests read requests could be handled earlier
# if quorum becomes less in configuration changes.
def test_read_when_quorum_becomes_less():
    pass


def test_uncommitted_entries_size_limit():
    pass


def test_uncommitted_entry_after_leader_election():
    pass


def test_uncommitted_state_advance_ready_from_last_term():
    pass


def test_fast_log_rejection():
    pass


def test_switching_check_quorum():
    pass
