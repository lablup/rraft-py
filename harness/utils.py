from typing import List, Optional
from rraft import (
    ConfChange_Owner,
    ConfChangeSingle_Owner,
    ConfChangeSingle_Ref,
    ConfChangeType,
    ConfChangeV2_Owner,
    ConfState_Owner,
    Config_Owner,
    Entry_Owner,
    Entry_Ref,
    HardState_Owner,
    Logger_Owner,
    Logger_Ref,
    MemStorage_Owner,
    MemStorage_Ref,
    Message_Owner,
    MessageType,
    Raft__MemStorage_Owner,
    RaftLog__MemStorage_Ref,
    Snapshot_Owner,
    SnapshotMetadata_Owner,
    SoftState_Owner,
    StateRole,
    NO_LIMIT,
)

from harness.src.network import Network
from harness.src.interface import Interface


def ltoa(raft_log: RaftLog__MemStorage_Ref) -> str:
    s = f"commited {raft_log.get_committed()}\n"
    s += f"applied {raft_log.get_applied()}\n"
    for i, e in enumerate(raft_log.all_entries()):
        s += f"#{i}: {e}\n"
    return s


def new_storage() -> MemStorage_Owner:
    return MemStorage_Owner()


def new_test_config(id: int, election_tick: int, heartbeat_size: int) -> Config_Owner:
    return Config_Owner(
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
    storage: MemStorage_Owner | MemStorage_Ref,
    logger: Logger_Owner | Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner)

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_prevote(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage_Owner | MemStorage_Ref,
    pre_vote: bool,
    logger: Logger_Owner | Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    config.set_pre_vote(pre_vote)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner)

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_logs(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage_Owner | MemStorage_Ref,
    logs: List[Entry_Owner] | List[Entry_Ref],
    logger: Logger_Owner | Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner)

    storage.wl(lambda core: core.append(logs))

    return new_test_raft_with_config(config, storage, logger)


def new_test_raft_with_config(
    config: Config_Owner,
    storage: MemStorage_Owner | MemStorage_Ref,
    logger: Logger_Owner | Logger_Ref,
) -> Interface:
    return Interface(Raft__MemStorage_Owner(config, storage, logger))


def hard_state(term: int, commit: int, vote: int) -> HardState_Owner:
    hs = HardState_Owner.default()
    hs.set_term(term)
    hs.set_commit(commit)
    hs.set_vote(vote)
    return hs


def soft_state(leader_id: int, raft_state: StateRole) -> SoftState_Owner:
    ss = SoftState_Owner.default()
    ss.set_leader_id(leader_id)
    ss.set_raft_state(raft_state)
    return ss


SOME_DATA = "somedata"


def new_message_with_entries(
    from_: int, to: int, t: MessageType, ents: List[Entry_Owner]
) -> Message_Owner:
    m = Message_Owner()
    m.set_from(from_)
    m.set_to(to)
    m.set_msg_type(t)

    if ents:
        m.set_entries(ents)
    return m


def new_message(from_: int, to: int, t: MessageType, n: int) -> Message_Owner:
    m = new_message_with_entries(from_, to, t, [])
    if n > 0:
        ents = []
        for _ in range(0, n):
            ents.append(new_entry(0, 0, SOME_DATA))

        m.set_entries(ents)
    return m


def new_entry(term: int, index: int, data: Optional[str]) -> Entry_Owner:
    e = Entry_Owner.default()
    e.set_index(index)
    e.set_term(term)
    if data:
        e.set_data(data.encode("utf-8"))
    return e


def empty_entry(term: int, index: int) -> Entry_Owner:
    return new_entry(term, index, None)


def new_snapshot(index: int, term: int, voters: List[int]) -> Snapshot_Owner:
    s = Snapshot_Owner.default()
    s.get_metadata().set_index(index)
    s.get_metadata().set_term(term)
    s.get_metadata().get_conf_state().set_voters(voters)
    return s


def conf_change(ty: ConfChangeType, node_id: int) -> ConfChange_Owner:
    cc = ConfChange_Owner.default()
    cc.set_change_type(ty)
    cc.set_node_id(node_id)
    return cc


def remove_node(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.RemoveNode, node_id)
    return cc.into_v2()


def add_node(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.AddNode, node_id)
    return cc.into_v2()


def add_learner(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.AddLearnerNode, node_id)
    return cc.into_v2()


def conf_state(voters: List[int], learners: List[int]) -> ConfState_Owner:
    cs = ConfState_Owner.default()
    cs.set_voters(voters)
    cs.set_learners(learners)
    return cs


def conf_state_v2(
    voters: List[int],
    learners: List[int],
    voters_outgoing: List[int],
    learners_next: List[int],
    auto_leave: bool,
) -> ConfState_Owner:
    cs = conf_state(voters, learners)
    cs.set_voters_outgoing(voters_outgoing)
    cs.set_learners_next(learners_next)
    cs.set_auto_leave(auto_leave)
    return cs


def conf_change_v2(
    steps: List[ConfChangeSingle_Owner] | List[ConfChangeSingle_Ref],
) -> ConfChangeV2_Owner:
    cc = ConfChangeV2_Owner.default()
    cc.set_changes(steps)
    return cc