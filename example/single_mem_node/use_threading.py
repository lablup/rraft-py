from datetime import datetime, timezone
from queue import Queue, Empty as QueueEmptyException
from threading import Thread
from time import sleep
from typing import Dict, List, Callable, cast
from rraft import (
    Entry_Ref,
    HardState_Ref,
    Logger_Ref,
    MemStorage,
    ConfState,
    EntryType,
    Config,
    Logger,
    Message_Ref,
    RawNode__MemStorage,
    OverflowStrategy,
)

channel: Queue = Queue()


def now() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def send_propose(logger: Logger | Logger_Ref) -> None:
    def _send_propose():
        # Wait some time and send the request to the Raft.
        sleep(10)
        logger.info("propose a request")

        raft_chan = Queue()

        # Send a command to the Raft, wait for the Raft to apply it
        # and get the result.
        channel.put(
            {
                "msg_type": "PROPOSE",
                "id": 1,
                "cb": lambda: raft_chan.put(0, block=True),
            },
            block=True,
        )

        n = raft_chan.get(block=True)
        assert n == 0
        logger.info("receive the propose callback")

        channel.put(
            {
                "msg_type": "DISCONNECTED",
            },
            block=True,
        )

    Thread(name="single_mem_node", target=_send_propose).start()


def on_ready(
    raft_group_ref: RawNode__MemStorage, cbs: Dict[str, Callable]
) -> None:
    if not raft_group_ref.has_ready():
        return

    store_ref = raft_group_ref.get_raft().get_raft_log().get_store()

    # Get the `Ready` with `RawNode::ready` interface.
    ready = raft_group_ref.ready()
    ready_ref = ready.make_ref()

    def handle_messages(msg_refs: List[Message_Ref]):
        for _msg_ref in msg_refs:
            # Send messages to other peers.
            continue

    if msgs := ready_ref.messages():
        # Send out the messages come from the node.
        handle_messages(msgs)

    if ready_ref.snapshot():
        # This is a snapshot, we need to apply the snapshot at first.
        cloned_ready = raft_group_ref.ready()
        store_ref.wl(lambda core: core.apply_snapshot(cloned_ready.snapshot()))

    _last_apply_index = 0

    def handle_committed_entries(committed_entry_refs: List[Entry_Ref]):
        for entry_ref in committed_entry_refs:
            # Mostly, you need to save the last apply index to resume applying
            # after restart. Here we just ignore this because we use a Memory storage.
            nonlocal _last_apply_index
            _last_apply_index = entry_ref.get_index()

            entry_data = entry_ref.get_data()

            if not entry_ref.get_data():
                # Emtpy entry, when the peer becomes Leader it will send an empty entry.
                continue

            if entry_ref.get_entry_type() == EntryType.EntryNormal:
                cbs[entry_data[0]]()
                del cbs[entry_data[0]]

            # TODO: handle EntryConfChange

    handle_committed_entries(ready_ref.committed_entries())

    if entry_refs := ready_ref.entries():
        # Append entries to the Raft log.
        store_ref.wl(lambda core: core.append(entry_refs))

    if hs_ref := ready_ref.hs():
        # Raft HardState changed, and we need to persist it.
        store_ref.wl(lambda core: core.set_hardstate(cast(HardState_Ref, hs_ref)))

    if msg_refs := ready_ref.persisted_messages():
        # Send out the persisted messages come from the node.
        handle_messages(msg_refs)

    # Advance the Raft.
    light_rd = raft_group_ref.advance(ready_ref)
    light_rd_ref = light_rd

    # Update commit index.
    if commit := light_rd_ref.commit_index():
        store_ref.wl(lambda core: core.hard_state().set_commit(cast(int, commit)))

    # Send out the messages.
    handle_messages(light_rd_ref.messages())
    # Apply all committed entries.
    handle_committed_entries(light_rd_ref.committed_entries())
    # Advance the apply index.
    raft_group_ref.advance_apply()


# A simple example about how to use the Raft library in Python.
if __name__ == "__main__":
    # Create a storage for Raft, and here we just use a simple memory storage.
    # You need to build your own persistent storage in your production.
    # Please check the Storage trait in src/storage.rs to see how to implement one.
    storage = MemStorage.new_with_conf_state(
        ConfState(voters=[1], learners=[])
    )

    # Create the configuration for the Raft node.
    cfg = Config(
        # The unique ID for the Raft node.
        id=1,
        # Election tick is for how long the follower may campaign again after
        # it doesn't receive any message from the leader.
        election_tick=10,
        # Heartbeat tick is for how long the leader needs to send
        # a heartbeat to keep alive.
        heartbeat_tick=3,
        # The max size limits the max size of each appended message. Mostly, 1 MB is enough.
        max_size_per_msg=1024 * 1024 * 1024,
        # Max inflight msgs that the leader sends messages to follower without
        # receiving ACKs.
        max_inflight_msgs=256,
        # The Raft applied index.
        # You need to save your applied index when you apply the committed Raft logs.
        applied=0,
    )

    logger = Logger(chan_size=4096, overflow_strategy=OverflowStrategy.Block)

    # Create the Raft node.
    raw_node = RawNode__MemStorage(cfg, storage, logger)
    raw_node_ref = raw_node

    # Use another thread to propose a Raft request.
    send_propose(logger)

    t = now()
    timeout = 100
    # Use a HashMap to hold the `propose` callbacks.
    cbs = {}

    # Loop forever to drive the Raft.
    while True:
        try:
            top = channel.get(block=True, timeout=timeout / 1000)
            msg_type = top["msg_type"]

            if msg_type == "PROPOSE":
                id, cb = top["id"], top["cb"]
                cbs[id] = cb
                raw_node_ref.propose(context=[], data=[id])
            elif msg_type == "RAFT":
                # Here we don't use Raft Message, so there is no "msg" sender in this example.
                msg = top["msg"]
                raw_node_ref.step(msg)
            elif msg_type == "DISCONNECTED":
                break
            else:
                assert False, "Invalid msg_type."

        except QueueEmptyException:
            pass

        finally:
            d = now() - t
            t = now()

            if d >= timeout:
                timeout = 100
                # We drive Raft every 100ms.
                raw_node_ref.tick()
            else:
                timeout -= d

            on_ready(raw_node_ref, cbs)
