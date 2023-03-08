from typing import Dict, List
from test_utils import new_message, new_storage, new_test_raft, empty_entry, hard_state
from rraft import (
    Logger_Ref,
    MemStorage_Ref,
    Message_Owner,
    Message_Ref,
    MessageType,
    StateRole,
    default_logger,
    INVALID_ID,
)

import os
import sys
import pytest

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "../src"))
sys.path.append(parent_dir)
from interface import Interface


def commit_noop_entry(r: Interface, s: MemStorage_Ref):
    assert r.raft.make_ref().get_state() == StateRole.Leader
    r.raft.make_ref().bcast_append()
    # simulate the response of MsgAppend
    msgs = r.read_messages()
    for m in msgs:
        assert m.make_ref().get_msg_type() == MessageType.MsgAppend
        assert len(m.make_ref().get_entries()) == 1
        assert len(m.make_ref().get_entries()[0].get_data()) == 0
        r.step(accept_and_reply(m.make_ref()))

    # ignore further messages to refresh followers' commit index
    r.read_messages()
    unstable = r.raft_log.unstable_entries()
    e = unstable[-1]
    last_idx, last_term = e.get_index(), e.get_term()
    r.raft_log.stable_entries(last_idx, last_term)
    s.wl(lambda core: core.append(unstable))
    r.raft.make_ref().on_persist_entries(last_idx, last_term)
    committed = r.raft_log.get_committed()
    r.raft.make_ref().commit_apply(committed)


def accept_and_reply(m: Message_Ref) -> Message_Ref:
    assert m.get_msg_type() == MessageType.MsgAppend
    reply = new_message(m.get_to(), m.get_from(), MessageType.MsgAppendResponse, 0)
    reply.make_ref().set_term(m.get_term())
    reply.make_ref().set_index(m.get_index() + len(m.get_entries()))
    return reply


# test_update_term_from_message tests that if one server’s current term is
# smaller than the other’s, then it updates its current term to the larger
# value. If a candidate or leader discovers that its term is out of date,
# it immediately reverts to follower state.
# Reference: section 5.1
#
# test_follower_update_term_from_message
# test_candidate_update_term_from_message
# test_leader_update_term_from_message
@pytest.mark.parametrize(
    "state", [StateRole.Follower, StateRole.Candidate, StateRole.Leader]
)
def test_update_term_from_message(state: StateRole):
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l)

    if state == StateRole.Follower:
        r.raft.make_ref().become_follower(1, 2)
    elif state == StateRole.PreCandidate:
        r.raft.make_ref().become_pre_candidate()
    elif state == StateRole.Candidate:
        r.raft.make_ref().become_candidate()
    elif state == StateRole.Leader:
        r.raft.make_ref().become_candidate()
        r.raft.make_ref().become_leader()
    else:
        assert False, "Invalid state"

    m = new_message(0, 0, MessageType.MsgAppend, 0)
    m.make_ref().set_term(2)
    r.step(m)
    assert r.raft.make_ref().get_term() == 2
    assert r.raft.make_ref().get_state() == StateRole.Follower


# test_start_as_follower tests that when servers start up, they begin as followers.
# Reference: section 5.2
def test_start_as_follower():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l.make_ref())
    assert r.raft.make_ref().get_state() == StateRole.Follower


# test_leader_bcast_beat tests that if the leader receives a heartbeat tick,
# it will send a msgApp with m.Index = 0, m.LogTerm=0 and empty entries as
# heartbeat to all followers.
# Reference: section 5.2
def test_leader_bcast_beat():
    l = default_logger()
    storage = new_storage()
    hi = 1
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l.make_ref())
    r.raft.make_ref().become_candidate()
    r.raft.make_ref().become_leader()
    for i in range(0, 10):
        ent = empty_entry(0, i + 1)
        r.raft.make_ref().append_entry([ent])

    for _ in range(0, hi):
        r.raft.make_ref().tick()

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))

    def new_message_ext(f: int, to: int) -> Message_Owner:
        m = new_message(f, to, MessageType.MsgHeartbeat, 0)
        m.make_ref().set_term(1)
        m.make_ref().set_commit(0)
        return m

    expect_msgs = [new_message_ext(1, 2), new_message_ext(1, 3)]
    assert msgs == expect_msgs


# test_nonleader_start_election tests that if a follower receives no communication
# over election timeout, it begins an election to choose a new leader. It
# increments its current term and transitions to candidate state. It then
# votes for itself and issues RequestVote RPCs in parallel to each of the
# other servers in the cluster.
# Reference: section 5.2
# Also if a candidate fails to obtain a majority, it will time out and
# start a new election by incrementing its term and initiating another
# round of RequestVote RPCs.
# Reference: section 5.2
#
# test_follower_start_election
# test_candidate_start_new_election
@pytest.mark.parametrize("state", [StateRole.Follower, StateRole.Candidate])
def test_nonleader_start_election(state: StateRole):
    l = default_logger()
    storage = new_storage()
    # election timeout
    et = 10

    r = new_test_raft(1, [1, 2, 3], et, 1, storage.make_ref(), l.make_ref())

    if state == StateRole.Follower:
        r.raft.make_ref().become_follower(1, 2)
    elif state == StateRole.Candidate:
        r.raft.make_ref().become_candidate()
    else:
        assert False, "Only non-leader role is accepted."

    for _ in range(1, 2 * et):
        r.raft.make_ref().tick()

    assert r.raft.make_ref().get_term() == 2
    assert r.raft.make_ref().get_state() == StateRole.Candidate
    assert r.raft.make_ref().prs().votes()[r.raft.make_ref().get_id()]

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))

    def new_message_ext(f: int, to: int) -> Message_Owner:
        m = new_message(f, to, MessageType.MsgRequestVote, 0)
        m.make_ref().set_term(2)
        return m

    expect_msgs = [new_message_ext(1, 2), new_message_ext(1, 3)]
    assert msgs == expect_msgs


# test_leader_election_in_one_round_rpc tests all cases that may happen in
# leader election during one round of RequestVote RPC:
# a) it wins the election
# b) it loses the election
# c) it is unclear about the result
# Reference: section 5.2
def test_leader_election_in_one_round_rpc():
    l = default_logger()

    class Test:
        def __init__(self, size: int, votes: Dict[int, bool], state: StateRole):
            self.size = size
            self.votes = votes
            self.state = state

    tests = [
        # win the election when receiving votes from a majority of the servers
        Test(1, {}, StateRole.Leader),
        Test(3, {2: True, 3: True}, StateRole.Leader),
        Test(3, {2: True}, StateRole.Leader),
        Test(5, {2: True, 3: True, 4: True, 5: True}, StateRole.Leader),
        Test(5, {2: True, 3: True, 4: True}, StateRole.Leader),
        Test(5, {2: True, 3: True}, StateRole.Leader),
        # return to follower state if it receives vote denial from a majority
        Test(3, {2: False, 3: False}, StateRole.Follower),
        Test(5, {2: False, 3: False, 4: False, 5: False}, StateRole.Follower),
        Test(5, {2: True, 3: False, 4: False, 5: False}, StateRole.Follower),
        # stay in candidate if it does not obtain the majority
        Test(3, {}, StateRole.Candidate),
        Test(5, {2: True}, StateRole.Candidate),
        Test(5, {2: False, 2: False}, StateRole.Candidate),
        Test(5, {}, StateRole.Candidate),
    ]

    for i, v in enumerate(tests):
        size, votes, state = v.size, v.votes, v.state
        storage = new_storage()
        r = new_test_raft(1, list(range(1, size + 1)), 10, 1, storage.make_ref(), l)
        r.step(new_message(1, 1, MessageType.MsgHup, 0))

        for id, vote in votes.items():
            m = new_message(id, 1, MessageType.MsgRequestVoteResponse, 0)
            m.make_ref().set_term(r.raft.make_ref().get_term())
            m.make_ref().set_reject(not vote)
            r.step(m.make_ref())

        assert (
            r.raft.make_ref().get_state() == state
        ), f"#{i}: state = {r.raft.make_ref().get_state()}, want {state}"

        assert (
            r.raft.make_ref().get_term() == 1
        ), f"#{i}: term = {r.raft.make_ref().get_term()}, want {1}"


# test_follower_vote tests that each follower will vote for at most one
# candidate in a given term, on a first-come-first-served basis.
# Reference: section 5.2
def test_follower_vote():
    l = default_logger()

    class Test:
        def __init__(self, vote: int, nvote: int, wreject: bool):
            self.vote = vote
            self.nvote = nvote
            self.wreject = wreject

    tests = [
        Test(INVALID_ID, 1, False),
        Test(INVALID_ID, 2, False),
        Test(1, 1, False),
        Test(2, 2, False),
        Test(1, 2, True),
        Test(2, 1, True),
    ]

    for i, v in enumerate(tests):
        vote, nvote, wreject = v.vote, v.nvote, v.wreject
        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l)
        hs = hard_state(1, 0, vote)
        r.raft.make_ref().load_state(hs.make_ref())

        m = new_message(nvote, 1, MessageType.MsgRequestVote, 0)
        m.make_ref().set_term(1)
        r.step(m.make_ref())

        msgs = r.read_messages()
        m = new_message(1, nvote, MessageType.MsgRequestVoteResponse, 0)
        m.make_ref().set_term(1)
        m.make_ref().set_reject(wreject)
        expected_msgs = [m]
        assert msgs == expected_msgs, f"#{i}: msgs = {msgs}, want {expected_msgs}"


# test_candidate_fallback tests that while waiting for votes,
# if a candidate receives an AppendEntries RPC from another server claiming
# to be leader whose term is at least as large as the candidate's current term,
# it recognizes the leader as legitimate and returns to follower state.
# Reference: section 5.2
def test_candidate_fallback():
    l = default_logger()

    def new_message_ext(f: int, to: int, term: int) -> Message_Owner:
        m = new_message(f, to, MessageType.MsgAppend, 0)
        m.make_ref().set_term(term)
        return m

    tests: List[Message_Owner] = [
        new_message_ext(2, 1, 2),
        new_message_ext(2, 1, 3),
    ]

    for i, m in enumerate(tests):
        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage.make_ref(), l)
        r.raft.make_ref().step(new_message(1, 1, MessageType.MsgHup, 0))
        assert r.raft.make_ref().get_state() == StateRole.Candidate

        term = m.make_ref().get_term()
        r.raft.make_ref().step(m.make_ref())

        assert (
            r.raft.make_ref().get_state() == StateRole.Follower
        ), f"#{i}: state = {r.raft.make_ref().get_state()}, want {StateRole.Follower}"

        assert (
            r.raft.make_ref().get_term() == term
        ), f"#{i}: term = {r.raft.make_ref().get_term()}, want {term}"


# test_non_leader_election_timeout_randomized tests that election timeout for
# follower or candidate is randomized.
# Reference: section 5.2
#
# test_follower_election_timeout_randomized
# test_candidate_election_timeout_randomized
@pytest.mark.parametrize("state", [StateRole.Follower, StateRole.Candidate])
def test_non_leader_election_timeout_randomized(state: StateRole):
    l = default_logger()
    et = 10
    storage = new_storage()
    r = new_test_raft(1, [1, 2, 3], et, 1, storage.make_ref(), l)
    timeouts = {}
    for _ in range(1000 * et):
        term = r.raft.make_ref().get_term()
        if state == StateRole.Follower:
            r.raft.make_ref().become_follower(term + 1, 2)
        elif state == StateRole.Candidate:
            r.raft.make_ref().become_candidate()
        else:
            assert False, "only non leader state is accepted!"

        time = 0
        while not r.read_messages():
            r.raft.make_ref().tick()
            time += 1

        timeouts[time] = True


def test_follower_election_timeout_nonconflict():
    pass


def test_candidates_election_timeout_nonconf():
    pass


# test_nonleaders_election_timeout_nonconfict tests that in most cases only a
# single server(follower or candidate) will time out, which reduces the
# likelihood of split vote in the new election.
# Reference: section 5.2
def test_nonleaders_election_timeout_nonconfict():
    pass


# test_leader_start_replication tests that when receiving client proposals,
# the leader appends the proposal to its log as a new entry, then issues
# AppendEntries RPCs in parallel to each of the other servers to replicate
# the entry. Also, when sending an AppendEntries RPC, the leader includes
# the index and term of the entry in its log that immediately precedes
# the new entries.
# Also, it writes the new entry into stable storage.
# Reference: section 5.3
def test_leader_start_replication():
    pass


# test_leader_commit_entry tests that when the entry has been safely replicated,
# the leader gives out the applied entries, which can be applied to its state
# machine.
# Also, the leader keeps track of the highest index it knows to be committed,
# and it includes that index in future AppendEntries RPCs so that the other
# servers eventually find out.
# Reference: section 5.3
def test_leader_commit_entry():
    pass


# test_leader_acknowledge_commit tests that a log entry is committed once the
# leader that created the entry has replicated it on a majority of the servers.
# Reference: section 5.3
def test_leader_acknowledge_commit():
    pass


# test_leader_commit_preceding_entries tests that when leader commits a log entry,
# it also commits all preceding entries in the leader’s log, including
# entries created by previous leaders.
# Also, it applies the entry to its local state machine (in log order).
# Reference: section 5.3
def test_leader_commit_preceding_entries():
    pass


# test_follower_commit_entry tests that once a follower learns that a log entry
# is committed, it applies the entry to its local state machine (in log order).
# Reference: section 5.3
def test_follower_commit_entry():
    pass


# test_follower_check_msg_append tests that if the follower does not find an
# entry in its log with the same index and term as the one in AppendEntries RPC,
# then it refuses the new entries. Otherwise it replies that it accepts the
# append entries.
# Reference: section 5.3
def test_follower_check_msg_append():
    pass


# test_follower_append_entries tests that when AppendEntries RPC is valid,
# the follower will delete the existing conflict entry and all that follow it,
# and append any new entries not already in the log.
# Also, it writes the new entry into stable storage.
# Reference: section 5.3
def test_follower_append_entries():
    pass


# test_leader_sync_follower_log tests that the leader could bring a follower's log
# into consistency with its own.
# Reference: section 5.3, figure 7
def test_leader_sync_follower_log():
    pass


# test_vote_request tests that the vote request includes information about the candidate’s log
# and are sent to all of the other nodes.
# Reference: section 5.4.1
def test_vote_request():
    pass


# test_voter tests the voter denies its vote if its own log is more up-to-date
# than that of the candidate.
# Reference: section 5.4.1
def test_voter():
    pass


# TestLeaderOnlyCommitsLogFromCurrentTerm tests that only log entries from the leader’s
# current term are committed by counting replicas.
# Reference: section 5.4.2
def test_leader_only_commits_log_from_current_term():
    pass
