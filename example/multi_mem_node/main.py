import asyncio
import logging
import os
from asyncio import Queue
from collections import deque
import re
import time
from typing import Dict, Final, List, Optional, Tuple, Deque
from rraft import (
    ConfChange,
    ConfChangeType,
    Config,
    Entry,
    EntryType,
    Logger,
    MemStorage,
    Message,
    MessageType,
    InMemoryRawNode,
    Snapshot,
    StateRole,
    default_logger,
)


class Proposal:
    def __init__(
        self,
        # If it's proposed, it will be set to the index of the entry.
        proposed: int,
        propose_success: Queue[Message],
        *,
        normal: Optional[Tuple[int, str]] = None,
        conf_change: Optional[ConfChange] = None,
        transfer_leader: Optional[int] = None,
    ):
        self._normal = normal
        self._conf_change = conf_change
        self._transfer_leader = transfer_leader
        self.proposed = proposed
        self.propose_success = propose_success

    @staticmethod
    def conf_change(cc: ConfChange) -> "Proposal":
        return Proposal(
            conf_change=cc.clone(),
            proposed=0,
            propose_success=Queue(maxsize=1),
        )

    @staticmethod
    def normal(key: int, value: str) -> "Proposal":
        return Proposal(
            normal=(key, value),
            proposed=0,
            propose_success=Queue(maxsize=1),
        )


def example_config() -> Config:
    cfg = Config.default()
    cfg.set_election_tick(10)
    cfg.set_heartbeat_tick(3)
    return cfg


def setup_logger() -> Logger:
    # Set up slog's log-level to Debug.
    os.environ["RUST_LOG"] = "debug"
    logging.basicConfig(level=logging.DEBUG)
    return default_logger()


def is_initial_msg(msg: Message) -> bool:
    """
    The message can be used to initialize a raft node or not.
    """
    msg_type = msg.get_msg_type()
    return (
        msg_type == MessageType.MsgRequestVote
        or msg_type == MessageType.MsgRequestPreVote
        or (msg_type == MessageType.MsgHeartbeat and msg.get_commit() == 0)
    )


def check_signals() -> bool:
    """
    Check control signals from
    """
    try:
        stop_channel.get_nowait()
        return True
    except asyncio.QueueEmpty:
        return False


logger = setup_logger()

NUM_NODES: Final[int] = 5

# Create `NUM_NODES` mailboxes to send/receive messages. Every node holds a `Queue` to receive
# messages from others, and uses the respective `Sender` to send messages to others.
channels = [Queue[Message]() for _ in range(NUM_NODES)]

stop_channel = Queue[bool]()

# A map[peer_id -> sender]. In the example we create "NUM_NODES" nodes, with ids in [1, NUM_NODES].
mailboxes: Dict[int, Queue[Message]] = {
    i: chan for i, chan in zip(range(1, NUM_NODES + 1), channels)
}

# A global pending proposals queue. New proposals will be pushed back into the queue, and
# after it's committed by the raft cluster, it will be popped from the queue.
proposals: Deque[Proposal] = deque()


async def add_all_followers() -> None:
    """
    Proposes some conf change for peers [2, NUM_NODES].
    """
    for id in range(2, NUM_NODES + 1):
        conf_change = ConfChange.default()
        conf_change.set_node_id(id)
        conf_change.set_change_type(ConfChangeType.AddNode)

        while True:
            proposal = Proposal.conf_change(conf_change)
            proposals.append(proposal)

            if await proposal.propose_success.get():
                break

            await asyncio.sleep(0.1)


async def propose(raft_group: InMemoryRawNode, proposal: Proposal) -> None:
    last_index1 = raft_group.get_raft().get_raft_log().last_index() + 1

    if proposal._normal:
        key, value = proposal._normal
        raft_group.propose([], bytes(f"put {key} {value}", "utf-8"))

    elif proposal._conf_change:
        raft_group.propose_conf_change([], proposal._conf_change.clone())

    elif proposal._transfer_leader:
        # TODO: implement transfer leader.
        raise NotImplementedError

    last_index2 = raft_group.get_raft().get_raft_log().last_index() + 1

    if last_index2 == last_index1:
        # Propose failed, don't forget to respond to the client.
        await proposal.propose_success.put(False)
    else:
        proposal.proposed = last_index1


class Node:
    def __init__(
        self,
        # None if the raft is not initialized.
        raft_group: Optional[InMemoryRawNode],
        my_mailbox: Queue[Message],
        # Key-value pairs after applied. `MemStorage` only contains raft logs,
        # so we need an additional storage engine.
        kv_pairs: Dict[int, str],
    ) -> None:
        self.raft_group = raft_group
        self.my_mailbox = my_mailbox
        self.kv_pairs = kv_pairs

    @staticmethod
    def create_raft_leader(id: int, my_mailbox: Queue[Message]) -> "Node":
        """
        Create a raft leader only with itself in its configuration.
        """
        cfg = example_config()
        cfg.set_id(id)
        s = Snapshot.default()
        # Because we don't use the same configuration to initialize every node, so we use
        # a non-zero index to force new followers catch up logs by snapshot first, which will
        # bring all nodes to the same initial state.
        s.get_metadata().set_index(1)
        s.get_metadata().set_term(1)
        s.get_metadata().get_conf_state().set_voters([1])
        storage = MemStorage()
        storage.wl().apply_snapshot(s)
        raft_group = InMemoryRawNode(cfg, storage, logger)
        return Node(raft_group, my_mailbox, {})

    @staticmethod
    def create_raft_follower(my_mailbox: Queue[Message]) -> "Node":
        """
        Create a raft follower.
        """
        return Node(None, my_mailbox, {})

    def initialize_raft_from_message(self, msg: Message) -> None:
        """
        Initialize raft for followers.
        """

        if not is_initial_msg(msg):
            return

        cfg = example_config()
        cfg.set_id(msg.get_to())
        storage = MemStorage()
        self.raft_group = InMemoryRawNode(cfg, storage, logger)

    def step(self, msg: Message) -> None:
        """
        Step a raft message, initialize the raft if need.
        """
        if self.raft_group is None:
            if is_initial_msg(msg):
                self.initialize_raft_from_message(msg)
            else:
                return

        self.raft_group.step(msg)


async def on_ready(
    raft_group: InMemoryRawNode,
    kv_pairs: Dict[int, str],
) -> None:
    if not raft_group.has_ready():
        return

    store = raft_group.get_raft().get_raft_log().get_store().clone()
    # Get the `Ready` with `RawNode::ready` interface.
    ready = raft_group.ready()

    def handle_messages(msgs: List[Message]) -> None:
        for msg in msgs:
            to = msg.get_to()
            try:
                mailboxes[to].put_nowait(msg)
            except Exception:
                logger.error(f"send raft message to {to} fail, let Raft retry it")

    if ready.messages():
        # Send out the messages come from the node.
        handle_messages(ready.take_messages())

    # Apply the snapshot. It's necessary because in `RawNode::advance` we stabilize the snapshot.
    snapshot_default = Snapshot.default()
    if ready.snapshot() != snapshot_default.make_ref():
        try:
            s = ready.snapshot().clone()
            store.wl().apply_snapshot(s)
        except Exception as e:
            logger.error(f"apply snapshot fail: {e}, let Raft retry it")
            return

    async def handle_committed_entries(
        rn: InMemoryRawNode, committed_entries: List[Entry]
    ):
        for entry in committed_entries:
            if not entry.get_data():
                # From new elected leaders.
                continue

            if entry.get_entry_type() == EntryType.EntryConfChange:
                cc = ConfChange.default()
                new_conf = ConfChange.decode(entry.get_data())

                cc.set_id(new_conf.get_id())
                cc.set_node_id(new_conf.get_node_id())
                cc.set_context(new_conf.get_context())
                cc.set_change_type(new_conf.get_change_type())

                cs = rn.apply_conf_change(cc)
                store.wl().set_conf_state(cs)
            else:
                # For normal proposals, extract the key-value pair and then
                # insert them into the kv engine.
                data = str(entry.get_data(), "utf-8")
                reg = re.compile(r"put ([0-9]+) (.+)")

                if caps := reg.match(data):
                    key, value = int(caps.group(1)), str(caps.group(2))
                    kv_pairs[key] = value

            if rn.get_raft().get_state() == StateRole.Leader:
                # The leader should response to the clients, tell them if their proposals
                # succeeded or not.
                proposal = proposals.popleft()
                await proposal.propose_success.put(True)

    # Apply all committed entries.
    await handle_committed_entries(raft_group, ready.take_committed_entries())

    # Persistent raft logs. It's necessary because in `RawNode::advance` we stabilize
    # raft logs to the latest position.
    try:
        store.wl().append(ready.entries())
    except Exception as e:
        logger.error(f"persist raft log fail: {e}, need to retry or panic")

    if hs := ready.hs():
        # Raft HardState changed, and we need to persist it.
        store.wl().set_hardstate(hs)

    if persisted_msgs := ready.take_persisted_messages():
        handle_messages(persisted_msgs)

    # Call `RawNode::advance` interface to update position flags in the raft.
    light_rd = raft_group.advance(ready.make_ref())
    # Update commit index.
    if commit := light_rd.commit_index():
        store.wl().hard_state().set_commit(commit)

    # Send out the messages.
    handle_messages(light_rd.take_messages())
    # Apply all committed entries.
    await handle_committed_entries(raft_group, light_rd.take_committed_entries())
    # Advance the apply index.
    raft_group.advance_apply()


async def handle(idx: int, chan: Queue) -> None:
    t = time.time()

    # Peer 1 is the leader and other peers are followers.
    node = (
        Node.create_raft_leader(1, chan)
        if idx == 0
        else Node.create_raft_follower(chan)
    )

    while True:
        await asyncio.sleep(0.01)
        while True:
            # Step raft messages.
            try:
                resp = node.my_mailbox.get_nowait()
                node.step(resp)
            except asyncio.QueueEmpty:
                break

        # When Node::raft_group is `None` it means the node is not initialized.
        if node.raft_group is None:
            continue

        elapsed = time.time() - t
        if elapsed >= 0.1:
            # Tick the raft
            node.raft_group.tick()
            t = time.time()

        # Let the leader pick pending proposals from the global queue.
        if node.raft_group.get_raft().get_state() == StateRole.Leader:
            # Handle new proposals.
            for p in proposals:
                if p.proposed == 0:
                    await propose(node.raft_group, p)

        # Handle readies from the raft.
        await on_ready(
            node.raft_group,
            node.kv_pairs,
        )

        # Check control signals from
        if check_signals():
            return


async def main() -> None:
    handles = []

    for idx, chan in enumerate(channels):
        handles.append(asyncio.create_task(handle(idx, chan)))

    # Propose some conf changes so that followers can be initialized.
    await add_all_followers()

    # Put 100 key-value pairs.
    logger.info(
        f"We get a {NUM_NODES} nodes Raft cluster now, now propose 100 proposals"
    )

    count = 0
    for i in range(100):
        proposal = Proposal.normal(i, "hello, world")
        proposals.append(proposal)
        # After we got a response from `chan`, we can assume the put succeeded and following
        # `get` operations can find the key-value pair.
        await proposal.propose_success.get()
        count += 1

    logger.info("Propose 100 proposals success!")

    # Send terminate signals
    for _ in range(NUM_NODES):
        stop_channel.put_nowait(True)

    # Wait for the coroutines to finish
    await asyncio.gather(*handles)


if __name__ == "__main__":
    asyncio.run(main())
