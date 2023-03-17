from typing import List, Optional
from rraft import (
    ConfChange_Owner,
    ConfChangeSingle_Owner,
    ConfChangeType,
    ConfChangeV2_Owner,
    ConfState_Owner,
    Config,
    Entry_Owner,
    Entry_Ref,
    HardState_Owner,
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

import os
import sys

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "../src"))
sys.path.append(parent_dir)

from interface import Interface

# from harness.src.network import Network
# from harness.src.interface import Interface


def ltoa(raft_log: RaftLog__MemStorage_Ref) -> str:
    s = f"commited {raft_log.get_committed()}\n"
    s += f"applied {raft_log.get_applied()}\n"
    for i, e in enumerate(raft_log.all_entries()):
        s += f"#{i}: {e}\n"
    return s


def new_storage() -> MemStorage_Owner:
    return MemStorage_Owner()


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
    storage: MemStorage_Ref,
    logger: Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.make_ref().initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.make_ref().initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner.make_ref())

    return new_test_raft_with_config(config.make_ref(), storage, logger)


def new_test_raft_with_prevote(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage_Ref,
    pre_vote: bool,
    logger: Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    config.make_ref().set_pre_vote(pre_vote)
    initial_state = storage.initial_state()

    assert not (
        initial_state.make_ref().initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.make_ref().initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner.make_ref())

    return new_test_raft_with_config(config.make_ref(), storage, logger)


def new_test_raft_with_logs(
    id: int,
    peers: List[int],
    election: int,
    heartbeat: int,
    storage: MemStorage_Ref,
    logs: List[Entry_Ref],
    logger: Logger_Ref,
) -> Interface:
    config = new_test_config(id, election, heartbeat)
    initial_state = storage.initial_state()

    assert not (
        initial_state.make_ref().initialized() and not peers
    ), "new_test_raft with empty peers on initialized store"

    if peers and not initial_state.make_ref().initialized():
        cs_owner = ConfState_Owner(peers, [])
        storage.initialize_with_conf_state(cs_owner.make_ref())

    storage.wl(lambda core: core.append(logs))

    return new_test_raft_with_config(config.make_ref(), storage, logger)


def new_test_raft_with_config(
    config: Config,
    storage: MemStorage_Ref,
    logger: Logger_Ref,
) -> Interface:
    return Interface(Raft__MemStorage_Owner(config, storage, logger))


def hard_state(term: int, commit: int, vote: int) -> HardState_Owner:
    hs = HardState_Owner()
    hs.make_ref().set_term(term)
    hs.make_ref().set_commit(commit)
    hs.make_ref().set_vote(vote)
    return hs


def soft_state(leader_id: int, raft_state: StateRole) -> SoftState_Owner:
    ss = SoftState_Owner()
    ss.make_ref().set_leader_id(leader_id)
    ss.make_ref().set_raft_state(raft_state)
    return ss


SOME_DATA = "somedata"


def new_message_with_entries(
    from_: int, to: int, t: MessageType, ents: List[Entry_Owner]
) -> Message_Owner:
    m = Message_Owner()
    m.make_ref().set_from(from_)
    m.make_ref().set_to(to)
    m.make_ref().set_msg_type(t)

    if ents:
        m.make_ref().set_entries(ents)
    return m


def new_message(from_: int, to: int, t: MessageType, n: int) -> Message_Owner:
    m = new_message_with_entries(from_, to, t, [])
    if n > 0:
        ents = []
        for _ in range(0, n):
            ents.append(new_entry(0, 0, SOME_DATA))

        m.make_ref().set_entries(list(map(lambda x: x.make_ref(), ents)))
    return m


def new_entry(term: int, index: int, data: Optional[str]) -> Entry_Owner:
    e = Entry_Owner()
    e.make_ref().set_index(index)
    e.make_ref().set_term(term)
    if data:
        # TODO: Resolve below issue.
        # Maybe it would be better to pass 'bytes' itself or through 'memoryview' object instead of creating a new list.
        e.make_ref().set_data(list(data.encode("utf-8")))
    return e


def empty_entry(term: int, index: int) -> Entry_Owner:
    return new_entry(term, index, None)


def new_snapshot(index: int, term: int, voters: List[int]) -> Snapshot_Owner:
    s = Snapshot_Owner()
    meta = SnapshotMetadata_Owner()
    meta.make_ref().set_index(index)
    meta.make_ref().set_term(term)
    cs_ref = meta.make_ref().get_conf_state()
    cs_ref.set_voters(voters)

    s.make_ref().set_metadata(meta.make_ref())
    return s


def conf_change(ty: ConfChangeType, node_id: int) -> ConfChange_Owner:
    cc = ConfChange_Owner()
    cc.make_ref().set_change_type(ty)
    cc.make_ref().set_node_id(node_id)
    return cc


def remove_node(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.RemoveNode, node_id)
    return cc.make_ref().into_v2()


def add_node(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.AddNode, node_id)
    return cc.make_ref().into_v2()


def add_learner(node_id: int) -> ConfChangeV2_Owner:
    cc = conf_change(ConfChangeType.AddLearnerNode, node_id)
    return cc.make_ref().into_v2()


def conf_state(voters: List[int], learners: List[int]) -> ConfState_Owner:
    cs = ConfState_Owner()
    cs.make_ref().set_voters(voters)
    cs.make_ref().set_learners(learners)
    return cs


def conf_state_v2(
    voters: List[int],
    learners: List[int],
    voters_outgoing: List[int],
    learners_next: List[int],
    auto_leave: bool,
) -> ConfState_Owner:
    cs = conf_state(voters, learners)
    cs.make_ref().set_voters_outgoing(voters_outgoing)
    cs.make_ref().set_learners_next(learners_next)
    cs.make_ref().set_auto_leave(auto_leave)
    return cs


def conf_change_v2(steps: List[ConfChangeSingle_Owner]) -> ConfChangeV2_Owner:
    cc = ConfChangeV2_Owner()
    cc.make_ref().set_changes(steps)
    return cc
