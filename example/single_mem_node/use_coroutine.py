import asyncio
from asyncio import Queue
from datetime import datetime, timezone
from typing import Callable, Dict, List
from rraft import (
    Config,
    ConfState,
    EntryRef,
    EntryType,
    LoggerRef,
    Logger,
    MemStorage,
    MessageRef,
    OverflowStrategy,
    InMemoryRawNode,
)

channel: Queue = Queue()


def now() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


async def send_propose(logger: Logger | LoggerRef) -> None:
    # Wait some time and send the request to the Raft.
    await asyncio.sleep(10)
    logger.info("propose a request")

    # Send a command to the Raft, wait for the Raft to apply it
    # and get the result.
    raft_chan: Queue = Queue()

    await channel.put(
        {
            "msg_type": "PROPOSE",
            "id": 1,
            "cb": lambda: raft_chan.put(0),
        }
    )

    n = await raft_chan.get()
    assert n == 0
    logger.info("receive the propose callback")

    await channel.put({"msg_type": "DISCONNECTED"})


async def on_ready(
    raft_group: InMemoryRawNode, cbs: Dict[str, Callable]
) -> None:
    if not raft_group.has_ready():
        return

    store = raft_group.get_raft().get_raft_log().get_store()

    # Get the `Ready` with `RawNode::ready` interface.
    ready = raft_group.ready()

    async def handle_messages(msgs: List[MessageRef]):
        for _msg in msgs:
            # Send messages to other peers.
            continue

    if msgs := ready.messages():
        # Send out the messages come from the node.
        await handle_messages(msgs)

    if ready.snapshot():
        # This is a snapshot, we need to apply the snapshot at first.
        cloned_ready = raft_group.ready()
        store.wl().apply_snapshot(cloned_ready.snapshot())

    _last_apply_index = 0

    async def handle_committed_entries(committed_entries: List[EntryRef]):
        for entry in committed_entries:
            # Mostly, you need to save the last apply index to resume applying
            # after restart. Here we just ignore this because we use a Memory storage.
            nonlocal _last_apply_index
            _last_apply_index = entry.get_index()

            entry_data = entry.get_data()

            if not entry.get_data():
                # Emtpy entry, when the peer becomes Leader it will send an empty entry.
                continue

            if entry.get_entry_type() == EntryType.EntryNormal:
                await cbs[entry_data[0]]()
                del cbs[entry_data[0]]

            # TODO: handle EntryConfChange

    await handle_committed_entries(ready.committed_entries())

    if entries := ready.entries():
        # Append entries to the Raft log.
        store.wl().append(entries)

    if hs := ready.hs():
        # Raft HardState changed, and we need to persist it.
        store.wl().set_hardstate(hs)

    if msgs := ready.persisted_messages():
        # Send out the persisted messages come from the node.
        await handle_messages(msgs)

    # Advance the Raft.
    light_rd = raft_group.advance(ready.make_ref())

    # Update commit index.
    if commit := light_rd.commit_index():
        store.wl().hard_state().set_commit(commit)

    # Send out the messages.
    await handle_messages(light_rd.messages())
    # Apply all committed entries.
    await handle_committed_entries(light_rd.committed_entries())
    # Advance the apply index.
    raft_group.advance_apply()


async def main():
    # Create a storage for Raft, and here we just use a simple memory storage.
    # You need to build your own persistent storage in your production.
    # Please check the Storage trait in src/storage.rs to see how to implement one.
    storage = MemStorage.new_with_conf_state(ConfState(voters=[1], learners=[]))

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
    raw_node = InMemoryRawNode(cfg, storage, logger)

    # Use another task to propose a Raft request.
    asyncio.create_task(send_propose(logger))

    t = now()
    timeout = 100
    # Use a dict to hold the `propose` callbacks.
    cbs: Dict[str, Callable] = {}

    # Loop forever to drive the Raft.
    while True:
        try:
            top = await asyncio.wait_for(channel.get(), timeout / 1000)
            msg_type = top["msg_type"]

            if msg_type == "PROPOSE":
                id, cb = top["id"], top["cb"]
                cbs[id] = cb
                raw_node.propose(context=[], data=[id])
            elif msg_type == "RAFT":
                # Here we don't use Raft Message, so there is no "msg" sender in this example.
                msg = top["msg"]
                raw_node.step(msg)
            elif msg_type == "DISCONNECTED":
                break

        except asyncio.exceptions.TimeoutError:
            pass

        finally:
            d = now() - t
            t = now()

            if d >= timeout:
                timeout = 100
                # We drive Raft every 100ms.
                raw_node.tick()
            else:
                timeout -= d

            await on_ready(raw_node, cbs)


if __name__ == "__main__":
    asyncio.run(main())
