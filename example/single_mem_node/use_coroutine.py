import asyncio
from asyncio import Queue
from datetime import datetime, timezone
from typing import Callable, Dict, List
from rraft import (
    Config_Owner,
    ConfState_Owner,
    EntryType,
    Entry_Ref,
    Logger_Owner,
    Logger_Ref,
    MemStorage_Owner,
    Message_Ref,
    OverflowStrategy,
    RawNode__MemStorage_Owner,
    RawNode__MemStorage_Ref,
)

channel: Queue = Queue()


def now() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


async def send_propose(logger: Logger_Ref) -> None:
    # Wait some time and send the request to the Raft.
    await asyncio.sleep(10)
    logger.info("propose a request")

    # Send a command to the Raft, wait for the Raft to apply it
    # and get the result.
    raft_chan = Queue()

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
    raft_group_ref: RawNode__MemStorage_Ref, cbs: Dict[str, Callable]
) -> None:
    if not raft_group_ref.has_ready():
        return

    store_ref = raft_group_ref.get_raft().get_raft_log().get_store()

    # Get the `Ready` with `RawNode::ready` interface.
    ready_owner = raft_group_ref.ready()
    ready_ref = ready_owner.make_ref()

    async def handle_messages(msg_refs: List[Message_Ref]):
        for _msg_ref in msg_refs:
            # Send messages to other peers.
            continue

    if msgs := ready_ref.messages():
        # Send out the messages come from the node.
        await handle_messages(msgs)

    if ready_ref.snapshot():
        # This is a snapshot, we need to apply the snapshot at first.
        cloned_ready_owner = raft_group_ref.ready()
        store_ref.wl(lambda core: core.apply_snapshot(cloned_ready_owner.snapshot()))

    _last_apply_index = 0

    async def handle_committed_entries(committed_entries: List[Entry_Ref]):
        for entry_ref in committed_entries:
            # Mostly, you need to save the last apply index to resume applying
            # after restart. Here we just ignore this because we use a Memory storage.
            nonlocal _last_apply_index
            _last_apply_index = entry_ref.get_index()

            entry_data = entry_ref.get_data()

            if not entry_ref.get_data():
                # Emtpy entry, when the peer becomes Leader it will send an empty entry.
                continue

            if entry_ref.get_entry_type() == EntryType.EntryNormal:
                await cbs[entry_data[0]]()
                del cbs[entry_data[0]]

            # TODO: handle EntryConfChange

    await handle_committed_entries(ready_ref.committed_entries())

    if entry_refs := ready_ref.entries():
        # Append entries to the Raft log.
        store_ref.wl(lambda core: core.append(entry_refs))

    if hs_ref := ready_ref.hs():
        # Raft HardState changed, and we need to persist it.
        store_ref.wl(lambda core: core.set_hardstate(hs_ref))

    if msg_refs := ready_ref.persisted_messages():
        # Send out the persisted messages come from the node.
        handle_messages(msg_refs)

    # Advance the Raft.
    light_rd_owner = raft_group_ref.advance(ready_ref)
    light_rd_ref = light_rd_owner
    ready_ref = None

    # Update commit index.
    if commit := light_rd_ref.commit_index():
        store_ref.wl(lambda core: core.hard_state().set_commit(commit))

    # Send out the messages.
    await handle_messages(light_rd_ref.messages())
    # Apply all committed entries.
    await handle_committed_entries(light_rd_ref.committed_entries())
    # Advance the apply index.
    raft_group_ref.advance_apply()


async def main():
    # Create a storage for Raft, and here we just use a simple memory storage.
    # You need to build your own persistent storage in your production.
    # Please check the Storage trait in src/storage.rs to see how to implement one.
    storage = MemStorage_Owner.new_with_conf_state(
        ConfState_Owner(voters=[1], learners=[])
    )

    # Create the configuration for the Raft node.
    cfg = Config_Owner(
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

    logger = Logger_Owner(chan_size=4096, overflow_strategy=OverflowStrategy.Block)

    # Create the Raft node.
    raw_node_owner = RawNode__MemStorage_Owner(cfg, storage, logger)
    raw_node_ref = raw_node_owner

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
                raw_node_ref.propose(context=[], data=[id])
            elif msg_type == "RAFT":
                # Here we don't use Raft Message, so there is no "msg" sender in this example.
                msg = top["msg"]
                raw_node_ref.step(msg)
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
                raw_node_ref.tick()
            else:
                timeout -= d

            await on_ready(raw_node_ref, cbs)


if __name__ == "__main__":
    asyncio.run(main())
