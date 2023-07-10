from typing import List, Optional
from rraft import (
    ConfChange,
    ConfChangeSingle,
    ConfChangeSingleRef,
    ConfChangeType,
    ConfChangeV2,
    ConfState,
    Config,
    Entry,
    EntryRef,
    HardState,
    Logger,
    LoggerRef,
    MemStorage,
    MemStorageRef,
    Message,
    MessageType,
    InMemoryRaft,
    InMemoryRaftLogRef,
    Snapshot,
    SoftState,
    StateRole,
    NO_LIMIT,
)

from harness.src.interface import Interface


def ltoa(raft_log: InMemoryRaftLogRef) -> str:
    s = f"commited {raft_log.get_committed()}\n"
    s += f"applied {raft_log.get_applied()}\n"
    for i, e in enumerate(raft_log.all_entries()):
        s += f"#{i}: {e}\n"
    return s


def new_storage() -> MemStorage:
    return MemStorage()


def new_test_config(id: int, election_tick: int, heartbeat_size: int) -> Config:
    return Config(
        id=id,
        election_tick=election_tick,
        heartbeat_tick=heartbeat_size,
        max_size_per_msg=NO_LIMIT,
        max_inflight_msgs=256,
    )


def new_test_raft(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage | MemStorageRef,
    logger: Logger | LoggerRef,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs = ConfState(peers, [])
        storage.initialize_with_conf_state(cs)

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_prevote(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage | MemStorageRef,
    pre_vote: bool,
    logger: Logger | LoggerRef,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    config.set_pre_vote(pre_vote)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs = ConfState(peers, [])
        storage.initialize_with_conf_state(cs)

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_logs(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage | MemStorageRef,
    logs: List[Entry] | List[EntryRef],
    logger: Logger | LoggerRef,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs = ConfState(peers, [])
        storage.initialize_with_conf_state(cs)

    storage.wl().append(logs)

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_config(
    config: Config,
    storage: MemStorage | MemStorageRef,
    logger: Logger | LoggerRef,
) -> Interface:
    return Interface(InMemoryRaft(config, storage, logger))


def hard_state(term: int, commit: int, vote: int) -> HardState:
    hs = HardState.default()
    hs.set_term(term)
    hs.set_commit(commit)
    hs.set_vote(vote)
    return hs


def soft_state(leader_id: int, raft_state: StateRole) -> SoftState:
    ss = SoftState.default()
    ss.set_leader_id(leader_id)
    ss.set_raft_state(raft_state)
    return ss


SOME_DATA = "somedata"


def new_message_with_entries(
    from_: int, to: int, t: MessageType, ents: List[Entry]
) -> Message:
    m = Message()
    m.set_from(from_)
    m.set_to(to)
    m.set_msg_type(t)

    if ents:
        m.set_entries(ents)
    return m


def new_message(from_: int, to: int, t: MessageType, n: int) -> Message:
    m = new_message_with_entries(from_, to, t, [])
    if n > 0:
        ents = []
        for _ in range(0, n):
            ents.append(new_entry(0, 0, SOME_DATA))

        m.set_entries(ents)
    return m


def new_entry(term: int, index: int, data: Optional[str]) -> Entry:
    e = Entry.default()
    e.set_index(index)
    e.set_term(term)
    if data:
        e.set_data(data.encode("utf-8"))
    return e


def empty_entry(term: int, index: int) -> Entry:
    return new_entry(term, index, None)


def new_snapshot(index: int, term: int, voters: List[int]) -> Snapshot:
    s = Snapshot.default()
    s.get_metadata().set_index(index)
    s.get_metadata().set_term(term)
    s.get_metadata().get_conf_state().set_voters(voters)
    return s


def conf_change(ty: ConfChangeType, node_id: int) -> ConfChange:
    cc = ConfChange.default()
    cc.set_change_type(ty)
    cc.set_node_id(node_id)
    return cc


def remove_node(node_id: int) -> ConfChangeV2:
    cc = conf_change(ConfChangeType.RemoveNode, node_id)
    return cc.into_v2()


def add_node(node_id: int) -> ConfChangeV2:
    cc = conf_change(ConfChangeType.AddNode, node_id)
    return cc.into_v2()


def add_learner(node_id: int) -> ConfChangeV2:
    cc = conf_change(ConfChangeType.AddLearnerNode, node_id)
    return cc.into_v2()


def conf_state(voters: List[int], learners: List[int]) -> ConfState:
    cs = ConfState.default()
    cs.set_voters(voters)
    cs.set_learners(learners)
    return cs


def conf_state_v2(
    voters: List[int],
    learners: List[int],
    voters_outgoing: List[int],
    learners_next: List[int],
    auto_leave: bool,
) -> ConfState:
    cs = conf_state(voters, learners)
    cs.set_voters_outgoing(voters_outgoing)
    cs.set_learners_next(learners_next)
    cs.set_auto_leave(auto_leave)
    return cs


def conf_change_v2(
    steps: List[ConfChangeSingle] | List[ConfChangeSingleRef],
) -> ConfChangeV2:
    cc = ConfChangeV2.default()
    cc.set_changes(steps)
    return cc
