from queue import Queue, Empty as QueueEmptyException
from collections import deque
from time import sleep
from typing import Any, Optional, Tuple, Deque
from rraft import (
    ConfChange,
    ConfChange_Ref,
    ConfChangeType,
    ConfState,
    Config,
    Logger,
    MemStorage,
    OverflowStrategy,
    RawNode__MemStorage_Ref,
)

# Create 5 mailboxes to send/receive messages. Every node holds a `Receiver` to receive
# messages from others, and uses the respective `Sender` to send messages to others.
channel_vec = [Queue()] * 5


def example_config() -> Config:
    return Config(
        election_tick=10,
        heartbeat_tick=3,
    )


class Proposal:
    def __init__(
        self,
        normal: Tuple[int, str],
        conf_change: Optional[ConfChange],
        transfer_leader: Optional[int],
        # If it's proposed, it will be set to the index of the entry.
        proposed: int,
        proposed_success: Any,
    ):
        self.normal = normal
        self.conf_change = conf_change
        self.transfer_leader = transfer_leader
        self.proposed = proposed
        self.proposed_success = proposed_success

    def conf_change(cc: ConfChange_Ref) -> Tuple[Any]:
        channel = Queue()
        proposal = Proposal(None, cc, None, 0, channel)
        return proposal, channel

    def normal(key: int, value: str) -> Tuple[Any]:
        channel = Queue()
        proposal = Proposal((key, value), None, None, 0, channel)
        return proposal, channel


def add_all_followers(proposals: Deque[Proposal]):
    for i in range(2, 65):
        conf_change = ConfChange()
        conf_change.set_node_id(i)
        conf_change.set_change_type(ConfChangeType.AddNode)

        while True:
            proposal, rx = Proposal.conf_change(conf_change)
            proposals.append(proposal)

            sleep(0.1)


def propose(raft_group: RawNode__MemStorage_Ref, proposal: Proposal):
    pass


if __name__ == "__main__":
    # Create a storage for Raft, and here we just use a simple memory storage.
    # You need to build your own persistent storage in your production.
    # Please check the Storage trait in src/storage.rs to see how to implement one.
    cs = ConfState(voters=[1], learners=[])
    storage = MemStorage.new_with_conf_state(cs)

    logger = Logger(
        chan_size=4096, overflow_strategy=OverflowStrategy.Block
    )

    stop_channel = Queue()

    proposals = [deque()]
    handles = []

    for i, chan in enumerate(channel_vec):
        mailboxes =
