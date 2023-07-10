import pytest
from typing import Dict, List
from harness.src.interface import Interface
from harness.src.network import Network
from rraft import (
    ConfState,
    Entry,
    MemStorage,
    MemStorageRef,
    Message,
    MessageRef,
    MessageType,
    StateRole,
    default_logger,
    INVALID_ID,
)

from harness.utils import (
    ltoa,
    new_message,
    new_storage,
    new_test_raft,
    empty_entry,
    hard_state,
    new_entry,
    SOME_DATA,
    new_test_config,
    new_test_raft_with_config,
)


def commit_noop_entry(r: Interface, s: MemStorageRef):
    assert r.raft.get_state() == StateRole.Leader
    r.raft.bcast_append()

    # simulate the response of MsgAppend
    msgs = r.read_messages()
    for m in msgs:
        assert m.get_msg_type() == MessageType.MsgAppend
        assert len(m.get_entries()) == 1
        assert len(m.get_entries()[0].get_data()) == 0
        reply = accept_and_reply(m)
        r.step(reply)

    # ignore further messages to refresh followers' commit index
    r.read_messages()
    unstable = r.raft_log.unstable_entries()

    if unstable:
        e = unstable[-1]
        last_idx, last_term = e.get_index(), e.get_term()
        r.raft_log.stable_entries(last_idx, last_term)
        s.wl().append(unstable)
        r.raft.on_persist_entries(last_idx, last_term)
        committed = r.raft_log.get_committed()
        r.raft.commit_apply(committed)


def accept_and_reply(m: MessageRef) -> Message:
    assert m.get_msg_type() == MessageType.MsgAppend
    reply = new_message(m.get_to(), m.get_from(), MessageType.MsgAppendResponse, 0)
    reply.set_term(m.get_term())
    reply.set_index(m.get_index() + len(m.get_entries()))
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
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)

    if state == StateRole.Follower:
        r.raft.become_follower(1, 2)
    elif state == StateRole.PreCandidate:
        r.raft.become_pre_candidate()
    elif state == StateRole.Candidate:
        r.raft.become_candidate()
    elif state == StateRole.Leader:
        r.raft.become_candidate()
        r.raft.become_leader()
    else:
        assert False, "Invalid state"

    m = new_message(0, 0, MessageType.MsgAppend, 0)
    m.set_term(2)
    r.step(m)
    assert r.raft.get_term() == 2
    assert r.raft.get_state() == StateRole.Follower


# test_start_as_follower tests that when servers start up, they begin as followers.
# Reference: section 5.2
def test_start_as_follower():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
    assert r.raft.get_state() == StateRole.Follower


# test_leader_bcast_beat tests that if the leader receives a heartbeat tick,
# it will send a msgApp with m.Index = 0, m.LogTerm=0 and empty entries as
# heartbeat to all followers.
# Reference: section 5.2
def test_leader_bcast_beat():
    l = default_logger()
    storage = new_storage()
    hi = 1
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    for i in range(0, 10):
        ent = empty_entry(0, i + 1)
        r.raft.append_entry([ent])

    for _ in range(0, hi):
        r.raft.tick()

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))

    def new_message_ext(f: int, to: int) -> Message:
        m = new_message(f, to, MessageType.MsgHeartbeat, 0)
        m.set_term(1)
        m.set_commit(0)
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

    r = new_test_raft(1, [1, 2, 3], et, 1, storage, l)

    if state == StateRole.Follower:
        r.raft.become_follower(1, 2)
    elif state == StateRole.Candidate:
        r.raft.become_candidate()
    else:
        assert False, "Only non-leader role is accepted."

    for _ in range(1, 2 * et):
        r.raft.tick()

    assert r.raft.get_term() == 2
    assert r.raft.get_state() == StateRole.Candidate
    assert r.raft.prs().votes()[r.raft.get_id()]

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))

    def new_message_ext(f: int, to: int) -> Message:
        m = new_message(f, to, MessageType.MsgRequestVote, 0)
        m.set_term(2)
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
        r = new_test_raft(1, list(range(1, size + 1)), 10, 1, storage, l)
        r.step(new_message(1, 1, MessageType.MsgHup, 0))

        for id, vote in votes.items():
            m = new_message(id, 1, MessageType.MsgRequestVoteResponse, 0)
            m.set_term(r.raft.get_term())
            m.set_reject(not vote)
            r.step(m)

        assert (
            r.raft.get_state() == state
        ), f"#{i}: state = {r.raft.get_state()}, want {state}"

        assert r.raft.get_term() == 1, f"#{i}: term = {r.raft.get_term()}, want {1}"


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
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
        hs = hard_state(1, 0, vote)
        r.raft.load_state(hs)

        m = new_message(nvote, 1, MessageType.MsgRequestVote, 0)
        m.set_term(1)
        r.step(m)

        msgs = r.read_messages()
        m = new_message(1, nvote, MessageType.MsgRequestVoteResponse, 0)
        m.set_term(1)
        m.set_reject(wreject)
        expected_msgs = [m]
        assert msgs == expected_msgs, f"#{i}: msgs = {msgs}, want {expected_msgs}"


# test_candidate_fallback tests that while waiting for votes,
# if a candidate receives an AppendEntries RPC from another server claiming
# to be leader whose term is at least as large as the candidate's current term,
# it recognizes the leader as legitimate and returns to follower state.
# Reference: section 5.2
def test_candidate_fallback():
    l = default_logger()

    def new_message_ext(f: int, to: int, term: int) -> Message:
        m = new_message(f, to, MessageType.MsgAppend, 0)
        m.set_term(term)
        return m

    tests: List[Message] = [
        new_message_ext(2, 1, 2),
        new_message_ext(2, 1, 3),
    ]

    for i, m in enumerate(tests):
        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
        r.raft.step(new_message(1, 1, MessageType.MsgHup, 0))
        assert r.raft.get_state() == StateRole.Candidate

        term = m.get_term()
        r.raft.step(m)

        assert (
            r.raft.get_state() == StateRole.Follower
        ), f"#{i}: state = {r.raft.get_state()}, want {StateRole.Follower}"

        assert (
            r.raft.get_term() == term
        ), f"#{i}: term = {r.raft.get_term()}, want {term}"


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
    r = new_test_raft(1, [1, 2, 3], et, 1, storage, l)
    timeouts = {}
    for _ in range(1000 * et):
        term = r.raft.get_term()
        if state == StateRole.Follower:
            r.raft.become_follower(term + 1, 2)
        elif state == StateRole.Candidate:
            r.raft.become_candidate()
        else:
            assert False, "only non leader state is accepted!"

        time = 0
        while not r.read_messages():
            r.raft.tick()
            time += 1

        timeouts[time] = True


# test_nonleaders_election_timeout_nonconfict tests that in most cases only a
# single server(follower or candidate) will time out, which reduces the
# likelihood of split vote in the new election.
# Reference: section 5.2
#
# test_follower_election_timeout_nonconflict
# test_candidates_election_timeout_nonconf
@pytest.mark.parametrize("state", [StateRole.Follower, StateRole.Candidate])
def test_nonleaders_election_timeout_nonconfict(state: StateRole):
    l = default_logger()
    et = 10
    size = 5
    rs: List[Interface] = []
    ids = list(range(1, size + 1))
    for id in ids:
        storage = new_storage()
        rs.append(new_test_raft(id, ids, et, 1, storage, l))

    conflicts = 0

    for _ in range(0, 1000):
        for r in rs:
            term = r.raft.get_term()
            if state == StateRole.Follower:
                r.raft.become_follower(term + 1, INVALID_ID)
            elif state == StateRole.Candidate:
                r.raft.become_candidate()
            else:
                assert False, "non leader state is expect!"

        timeout_num = 0
        while timeout_num == 0:
            for r in rs:
                r.raft.tick()

                if not r.read_messages():
                    timeout_num += 1

        # several rafts time out at the same tick
        if timeout_num > 1:
            conflicts += 1


# test_leader_start_replication tests that when receiving client proposals,
# the leader appends the proposal to its log as a new entry, then issues
# AppendEntries RPCs in parallel to each of the other servers to replicate
# the entry. Also, when sending an AppendEntries RPC, the leader includes
# the index and term of the entry in its log that immediately precedes
# the new entries.
# Also, it writes the new entry into stable storage.
# Reference: section 5.3
def test_leader_start_replication():
    l = default_logger()
    s = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    commit_noop_entry(r, s)
    li = r.raft_log.last_index()

    r.step(new_message(1, 1, MessageType.MsgPropose, 1))

    assert r.raft_log.last_index() == li + 1
    assert r.raft_log.get_committed() == li

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))
    wents1, wents2 = [new_entry(1, li + 1, SOME_DATA)], [
        new_entry(1, li + 1, SOME_DATA)
    ]

    def new_message_ext(f: int, to: int, ents: List[Entry]) -> Message:
        m = new_message(f, to, MessageType.MsgAppend, 0)
        m.set_term(1)
        m.set_index(li)
        m.set_log_term(1)
        m.set_commit(li)
        m.set_entries(ents)
        return m

    excepted_msgs = [
        new_message_ext(1, 2, wents1),
        new_message_ext(1, 3, wents2),
    ]

    assert msgs == excepted_msgs
    assert r.raft_log.unstable_entries() == wents1


# test_leader_commit_entry tests that when the entry has been safely replicated,
# the leader gives out the applied entries, which can be applied to its state
# machine.
# Also, the leader keeps track of the highest index it knows to be committed,
# and it includes that index in future AppendEntries RPCs so that the other
# servers eventually find out.
# Reference: section 5.3
def test_leader_commit_entry():
    l = default_logger()
    s = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()
    commit_noop_entry(r, s)
    li = r.raft_log.last_index()

    propose = new_message(1, 1, MessageType.MsgPropose, 1)

    r.step(propose)
    r.persist()

    for m in r.read_messages():
        reply = accept_and_reply(m)
        r.step(reply)

    assert r.raft_log.get_committed() == li + 1

    wents = [new_entry(1, li + 1, SOME_DATA)]

    assert r.raft_log.next_entries(None) == wents

    msgs = r.read_messages()
    msgs.sort(key=lambda m: str(m))

    for i, m in enumerate(msgs):
        assert i + 2 == m.get_to()
        assert m.get_msg_type() == MessageType.MsgAppend
        assert m.get_commit() == li + 1


# test_leader_acknowledge_commit tests that a log entry is committed once the
# leader that created the entry has replicated it on a majority of the servers.
# Reference: section 5.3
def test_leader_acknowledge_commit():
    l = default_logger()

    class Test:
        def __init__(self, size: int, acceptors: Dict[int, bool], wack: bool):
            self.size = size
            self.acceptors = acceptors
            self.wack = wack

    tests = [
        Test(1, {}, True),
        Test(3, {}, False),
        Test(3, {2: True}, True),
        Test(3, {2: True, 3: True}, True),
        Test(5, {}, False),
        Test(5, {2: True}, False),
        Test(5, {2: True, 3: True}, True),
        Test(5, {2: True, 3: True, 4: True}, True),
        Test(5, {2: True, 3: True, 4: True, 5: True}, True),
    ]

    for i, v in enumerate(tests):
        size, acceptors, wack = v.size, v.acceptors, v.wack
        s = new_storage()
        r = new_test_raft(1, list(range(1, size + 1)), 10, 1, s, l)
        r.raft.become_candidate()
        r.raft.become_leader()
        commit_noop_entry(r, s)
        li = r.raft_log.last_index()
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.persist()

        for m in r.read_messages():
            if m.get_to() in acceptors.keys():
                r.step(accept_and_reply(m))

        g = r.raft_log.get_committed() > li
        assert not (g ^ wack), f"#{i}: ack commit = {g}, want {wack}"


# test_leader_commit_preceding_entries tests that when leader commits a log entry,
# it also commits all preceding entries in the leader’s log, including
# entries created by previous leaders.
# Also, it applies the entry to its local state machine (in log order).
# Reference: section 5.3
def test_leader_commit_preceding_entries():
    l = default_logger()
    tests: List[List[Entry]] = [
        [],
        [empty_entry(2, 1)],
        [empty_entry(1, 1), empty_entry(2, 2)],
        [empty_entry(1, 1)],
    ]

    for i, tt in enumerate(tests):
        cs = ConfState([1, 2, 3], [])
        store = MemStorage.new_with_conf_state(cs)
        store.wl().append(tt)
        cfg = new_test_config(1, 10, 1)
        r = new_test_raft_with_config(cfg, store, l)

        hs = hard_state(2, 0, 0)
        r.raft.load_state(hs)
        r.raft.become_candidate()
        r.raft.become_leader()

        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.persist()

        for m in r.read_messages():
            r.step(accept_and_reply(m))

        li = len(tt)
        tt.extend([empty_entry(3, li + 1), new_entry(3, li + 2, SOME_DATA)])
        g = r.raft_log.next_entries(None)
        wg = tt

        assert g == wg, f"#{i}: ents = {g}, want {wg}"


# test_follower_commit_entry tests that once a follower learns that a log entry
# is committed, it applies the entry to its local state machine (in log order).
# Reference: section 5.3
def test_follower_commit_entry():
    l = default_logger()

    class Test:
        def __init__(self, ents: List[Entry], commit: int):
            self.ents = ents
            self.commit = commit

    tests = [
        Test([new_entry(1, 1, SOME_DATA)], 1),
        Test(
            [
                new_entry(1, 1, SOME_DATA),
                new_entry(1, 2, "somedata2"),
            ],
            2,
        ),
        Test(
            [
                new_entry(1, 1, "somedata2"),
                new_entry(1, 2, SOME_DATA),
            ],
            2,
        ),
        Test(
            [
                new_entry(1, 1, SOME_DATA),
                new_entry(1, 2, "somedata2"),
            ],
            1,
        ),
    ]

    for i, v in enumerate(tests):
        ents, commit = v.ents, v.commit
        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
        r.raft.become_follower(1, 2)

        m = new_message(2, 1, MessageType.MsgAppend, 0)
        m.set_term(1)
        m.set_commit(commit)
        m.set_entries(ents)
        r.step(m)
        r.persist()

        assert (
            r.raft_log.get_committed() == commit
        ), f"#{i}: committed = {r.raft_log.get_committed()}, want {commit}"

        wents = ents[:commit]
        g = r.raft_log.next_entries(None)
        assert g == wents, f"#{i}: next_ents = {g}, want {wents}"


# test_follower_check_msg_append tests that if the follower does not find an
# entry in its log with the same index and term as the one in AppendEntries RPC,
# then it refuses the new entries. Otherwise it replies that it accepts the
# append entries.
# Reference: section 5.3
def test_follower_check_msg_append():
    l = default_logger()
    ents = [empty_entry(1, 1), empty_entry(2, 2)]

    class Test:
        def __init__(
            self,
            term: int,
            index: int,
            windex: int,
            w_commit: int,
            wreject: bool,
            wreject_hint: int,
            w_log_term: int,
        ) -> None:
            self.term = term
            self.index = index
            self.windex = windex
            self.w_commit = w_commit
            self.wreject = wreject
            self.wreject_hint = wreject_hint
            self.w_log_term = w_log_term

    tests = [
        # match with committed entries
        Test(
            0,
            0,
            1,
            1,
            False,
            0,
            0,
        ),
        Test(
            ents[0].get_term(),
            ents[0].get_index(),
            1,
            1,
            False,
            0,
            0,
        ),
        # match with uncommitted entries
        Test(
            ents[1].get_term(),
            ents[1].get_index(),
            2,
            1,
            False,
            0,
            0,
        ),
        # unmatch with existing entry
        Test(
            ents[0].get_term(),
            ents[1].get_index(),
            ents[1].get_index(),
            1,
            True,
            1,
            1,
        ),
        # unexisting entry
        Test(
            ents[1].get_term() + 1,
            ents[1].get_index() + 1,
            ents[1].get_index() + 1,
            1,
            True,
            2,
            2,
        ),
    ]

    for i, v in enumerate(tests):
        term, index, windex, w_commit, wreject, wreject_hint, w_log_term = (
            v.term,
            v.index,
            v.windex,
            v.w_commit,
            v.wreject,
            v.wreject_hint,
            v.w_log_term,
        )

        cs = ConfState([1, 2, 3], [])
        store: MemStorage = MemStorage.new_with_conf_state(cs)
        store.wl().append(ents)
        cfg = new_test_config(1, 10, 1)
        r = new_test_raft_with_config(cfg, store, l)

        hs = hard_state(0, 1, 0)
        r.raft.load_state(hs)
        r.raft.become_follower(2, 2)

        m = new_message(2, 1, MessageType.MsgAppend, 0)
        m.set_term(2)
        m.set_log_term(term)
        m.set_index(index)
        r.step(m)

        msgs = r.read_messages()
        wm = new_message(1, 2, MessageType.MsgAppendResponse, 0)
        wm.set_term(2)
        wm.set_index(windex)
        wm.set_commit(w_commit)

        if wreject:
            wm.set_reject(wreject)
            wm.set_reject_hint(wreject_hint)
            wm.set_log_term(w_log_term)

        excepted_msgs = [wm]
        assert msgs == excepted_msgs, f"#{i}: msgs = {msgs}, want {excepted_msgs}"


# test_follower_append_entries tests that when AppendEntries RPC is valid,
# the follower will delete the existing conflict entry and all that follow it,
# and append any new entries not already in the log.
# Also, it writes the new entry into stable storage.
# Reference: section 5.3
def test_follower_append_entries():
    l = default_logger()

    class Test:
        def __init__(
            self,
            index: int,
            term: int,
            ents: List[Entry],
            wents: List[Entry],
            wunstable: List[Entry],
        ) -> None:
            self.index = index
            self.term = term
            self.ents = ents
            self.wents = wents
            self.wunstable = wunstable

    tests = [
        Test(
            2,
            2,
            [empty_entry(3, 3)],
            [empty_entry(1, 1), empty_entry(2, 2), empty_entry(3, 3)],
            [empty_entry(3, 3)],
        ),
        Test(
            1,
            1,
            [empty_entry(3, 2), empty_entry(4, 3)],
            [empty_entry(1, 1), empty_entry(3, 2), empty_entry(4, 3)],
            [empty_entry(3, 2), empty_entry(4, 3)],
        ),
        Test(0, 0, [empty_entry(1, 1)], [empty_entry(1, 1), empty_entry(2, 2)], []),
        Test(0, 0, [empty_entry(3, 1)], [empty_entry(3, 1)], [empty_entry(3, 1)]),
    ]

    for i, v in enumerate(tests):
        index, term, ents, wents, wunstable = (
            v.index,
            v.term,
            v.ents,
            v.wents,
            v.wunstable,
        )
        cs = ConfState([1, 2, 3], [])
        store = MemStorage.new_with_conf_state(cs)
        store.wl().append([empty_entry(1, 1), empty_entry(2, 2)])
        cfg = new_test_config(1, 10, 1)
        r = new_test_raft_with_config(cfg, store, l)
        r.raft.become_follower(2, 2)

        m = new_message(2, 1, MessageType.MsgAppend, 0)
        m.set_term(2)
        m.set_log_term(term)
        m.set_index(index)
        m.set_entries(ents)
        r.step(m)

        g = r.raft_log.all_entries()
        assert g == wents, f"#{i}: ents = {g}, want {wents}"

        g = r.raft_log.unstable_entries()
        assert g == wunstable, f"#{i}: unstable_entries = {g}, want {wunstable}"


# test_leader_sync_follower_log tests that the leader could bring a follower's log
# into consistency with its own.
# Reference: section 5.3, figure 7
def test_leader_sync_follower_log():
    l = default_logger()
    ents = [
        empty_entry(1, 1),
        empty_entry(1, 2),
        empty_entry(1, 3),
        empty_entry(4, 4),
        empty_entry(4, 5),
        empty_entry(5, 6),
        empty_entry(5, 7),
        empty_entry(6, 8),
        empty_entry(6, 9),
        empty_entry(6, 10),
    ]

    term = 8
    tests = [
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(4, 4),
            empty_entry(4, 5),
            empty_entry(5, 6),
            empty_entry(5, 7),
            empty_entry(6, 8),
            empty_entry(6, 9),
        ],
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(4, 4),
        ],
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(4, 4),
            empty_entry(4, 5),
            empty_entry(5, 6),
            empty_entry(5, 7),
            empty_entry(6, 8),
            empty_entry(6, 9),
            empty_entry(6, 10),
            empty_entry(6, 11),
        ],
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(4, 4),
            empty_entry(4, 5),
            empty_entry(5, 6),
            empty_entry(5, 7),
            empty_entry(6, 8),
            empty_entry(6, 9),
            empty_entry(6, 10),
            empty_entry(7, 11),
            empty_entry(7, 12),
        ],
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(4, 4),
            empty_entry(4, 5),
            empty_entry(4, 6),
            empty_entry(4, 7),
        ],
        [
            empty_entry(1, 1),
            empty_entry(1, 2),
            empty_entry(1, 3),
            empty_entry(2, 4),
            empty_entry(2, 5),
            empty_entry(2, 6),
            empty_entry(3, 7),
            empty_entry(3, 8),
            empty_entry(3, 9),
            empty_entry(3, 10),
            empty_entry(3, 11),
        ],
    ]

    for i, tt in enumerate(tests):
        lead_cs = ConfState([1, 2, 3], [])
        lead_store = MemStorage.new_with_conf_state(lead_cs)
        lead_store.wl().append(ents)
        lead_cfg = new_test_config(1, 10, 1)
        lead = new_test_raft_with_config(lead_cfg, lead_store, l)
        last_index = lead.raft_log.last_index()
        lead_hs = hard_state(term, last_index, 0)
        lead.raft.load_state(lead_hs)

        follower_cs = ConfState([1, 2, 3], [])
        follower_store = MemStorage.new_with_conf_state(follower_cs)
        follower_store.wl().append(tt)

        follower_cfg = new_test_config(2, 10, 1)
        follower = new_test_raft_with_config(follower_cfg, follower_store, l)
        follower_hs = hard_state(term - 1, 0, 0)
        follower.raft.load_state(follower_hs)

        NOP_STEPPER = Interface(None)

        # It is necessary to have a three-node cluster.
        # The second may have more up-to-date log than the first one, so the
        # first node needs the vote from the third node to become the leader.
        n = Network.new([lead, follower, NOP_STEPPER], l)
        m = new_message(1, 1, MessageType.MsgHup, 0)
        n.send([m])

        # The election occurs in the term after the one we loaded with
        # lead.load_state above.
        m = new_message(3, 1, MessageType.MsgRequestVoteResponse, 0)
        m.set_term(term + 1)
        n.send([m])

        m = new_message(1, 1, MessageType.MsgPropose, 0)
        e = Entry.default()
        m.set_entries([e])
        n.send([m])

        lead_str = ltoa(n.peers.get(1).raft_log)
        follower_str = ltoa(n.peers.get(2).raft_log)

        assert (
            lead_str == follower_str
        ), f"#{i}: lead str: {lead_str}, follower_str: {follower_str}"


# test_vote_request tests that the vote request includes information about the candidate’s log
# and are sent to all of the other nodes.
# Reference: section 5.4.1
def test_vote_request():
    l = default_logger()

    class Test:
        def __init__(self, ents: List[Entry], wterm: int) -> None:
            self.ents = ents
            self.wterm = wterm

    tests = [
        Test([empty_entry(1, 1)], 2),
        Test([empty_entry(1, 1), empty_entry(2, 2)], 3),
    ]

    for j, v in enumerate(tests):
        ents, wterm = (v.ents, v.wterm)

        storage = new_storage()
        r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
        m = new_message(2, 1, MessageType.MsgAppend, 0)
        m.set_term(wterm - 1)
        m.set_log_term(0)
        m.set_index(0)
        cloned_ents = list(map(lambda x: x.clone(), ents))
        m.set_entries(cloned_ents)
        r.step(m)
        r.read_messages()

        for _ in range(1, r.raft.election_timeout() * 2):
            r.raft.tick_election()

        msgs = r.read_messages()
        msgs.sort(key=lambda m: str(m))
        assert len(msgs) == 2, f"#{j}: msg count = {len(msgs)}, want 2"

        for i, m in enumerate(msgs):
            assert (
                m.get_msg_type() == MessageType.MsgRequestVote
            ), f"#{j}.{i}: msg_type = {m.get_msg_type()}, want {MessageType.MsgRequestVote}"

            assert m.get_to() == i + 2, f"#{j}.{i}: to = {m.get_to()}, want {i + 2}"

            assert (
                m.get_term() == wterm
            ), f"#{j}.{i}: term = {m.get_term()}, want {wterm}"

            windex = ents[-1].get_index()
            wlogterm = ents[-1].get_term()

            assert (
                m.get_index() == windex
            ), f"#{j}.{i}: index = {m.get_index()}, want {windex}"

            assert (
                m.get_log_term() == wlogterm
            ), f"#{j}.{i}: log_term = {m.get_log_term()}, want {wlogterm}"


# test_voter tests the voter denies its vote if its own log is more up-to-date
# than that of the candidate.
# Reference: section 5.4.1
def test_voter():
    l = default_logger()

    class Test:
        def __init__(
            self, ents: List[Entry], log_term: int, index: int, wreject: bool
        ) -> None:
            self.ents = ents
            self.log_term = log_term
            self.index = index
            self.wreject = wreject

    tests = [
        # same logterm
        Test([empty_entry(1, 1)], 1, 1, False),
        Test([empty_entry(1, 1)], 1, 2, False),
        Test([empty_entry(1, 1), empty_entry(1, 2)], 1, 1, True),
        # candidate higher logterm
        Test([empty_entry(1, 1)], 2, 1, False),
        Test([empty_entry(1, 1)], 1, 2, False),
        Test([empty_entry(1, 1), empty_entry(1, 2)], 2, 1, False),
        # voter higher logterm
        Test([empty_entry(2, 1)], 1, 1, True),
        Test([empty_entry(2, 1)], 1, 2, True),
        Test([empty_entry(2, 1), empty_entry(1, 2)], 1, 1, True),
    ]

    for i, v in enumerate(tests):
        ents, log_term, index, wreject = (v.ents, v.log_term, v.index, v.wreject)
        cs = ConfState([1, 2], [])
        s = MemStorage.new_with_conf_state(cs)
        s.wl().append(ents)
        cfg = new_test_config(1, 10, 1)
        r = new_test_raft_with_config(cfg, s, l)

        m = new_message(2, 1, MessageType.MsgRequestVote, 0)
        m.set_term(3)
        m.set_log_term(log_term)
        m.set_index(index)
        r.step(m)

        msgs = r.read_messages()
        assert len(msgs) == 1, f"#{i}: msg count = {len(msgs)}, want 1"

        assert (
            msgs[0].get_msg_type() == MessageType.MsgRequestVoteResponse
        ), f"#{i}: msg_type = {msgs[0].get_msg_type()}, want {MessageType.MsgRequestVoteResponse}"

        assert (
            msgs[0].get_reject() == wreject
        ), f"#{i}: reject = {msgs[0].get_reject()}, want {wreject}"


# TestLeaderOnlyCommitsLogFromCurrentTerm tests that only log entries from the leader’s
# current term are committed by counting replicas.
# Reference: section 5.4.2
def test_leader_only_commits_log_from_current_term():
    l = default_logger()
    ents = [empty_entry(1, 1), empty_entry(2, 2)]

    class Test:
        def __init__(self, index: int, wcommit: int) -> None:
            self.index = index
            self.wcommit = wcommit

    tests = [
        # do not commit log entries in previous terms
        Test(1, 0),
        Test(2, 0),
        # commit log in current term
        Test(3, 3),
    ]

    for i, v in enumerate(tests):
        index, wcommit = (v.index, v.wcommit)
        cs = ConfState([1, 2], [])
        store = MemStorage.new_with_conf_state(cs)
        store.wl().append(ents)
        cfg = new_test_config(1, 10, 1)
        r = new_test_raft_with_config(cfg, store, l)

        hs = hard_state(2, 0, 0)
        r.raft.load_state(hs)

        # become leader at term 3
        r.raft.become_candidate()
        r.raft.become_leader()
        r.read_messages()

        # propose a entry to current term
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.persist()

        m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
        m.set_term(r.raft.get_term())
        m.set_index(index)
        r.step(m)

        assert (
            r.raft_log.get_committed() == wcommit
        ), f"#{i}: commit = {r.raft_log.get_committed()}, want {wcommit}"
