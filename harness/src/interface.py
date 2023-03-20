from typing import List

from rraft import (
    Message_Owner,
    Message_Ref,
    Raft__MemStorage_Owner,
    RaftLog__MemStorage_Ref,
)

# A simulated Raft facade for testing.
#
# If the contained value is a `Some` operations happen. If they are a `None` operations are
# a no-op.
#
# Compare to upstream, we use struct instead of trait here.
# Because to be able to cast Interface later, we have to make
# Raft derive Any, which will require a lot of dependencies to derive Any.
# That's not worthy for just testing purpose.


class Interface:
    # Create a new interface to a new raft.
    def __init__(self, r: Raft__MemStorage_Owner) -> None:
        self.raft = r

    def __repr__(self) -> str:
        if not self.raft:
            return "Interface {{ empty }}"
        return f"Interface {{ id: {self.raft.get_id()} }}"

    @property
    def raft_log(self) -> RaftLog__MemStorage_Ref:
        return self.raft.get_raft_log()

    # Step the raft, if it exists.
    def step(self, message: Message_Owner | Message_Ref) -> None:
        if self.raft:
            self.raft.step(message)

    # Read messages out of the raft.
    def read_messages(self) -> List[Message_Owner]:
        if self.raft:
            return self.raft.take_msgs()
        return []

    # Persist the unstable snapshot and entries.
    def persist(self) -> None:
        if self.raft:
            if snapshot := self.raft_log.unstable_snapshot():
                snap = snapshot.clone()
                index = snap.get_metadata().get_index()
                self.raft_log.stable_snap(index)
                self.raft_log.get_store().wl(lambda core: core.apply_snapshot(snap))
                self.raft.on_persist_snap(index)
                self.raft.commit_apply(index)

            if unstable := self.raft_log.unstable_entries():
                e = unstable[-1]
                cloned_unstable = list(map(lambda x: x.clone(), unstable))

                last_idx, last_term = e.get_index(), e.get_term()
                self.raft_log.stable_entries(last_idx, last_term)
                self.raft_log.get_store().wl(lambda core: core.append(cloned_unstable))
                self.raft.on_persist_entries(last_idx, last_term)
