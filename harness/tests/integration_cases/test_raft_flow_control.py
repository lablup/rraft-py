from test_utils import new_message, new_storage, new_test_raft
from rraft import MessageType, default_logger


# test_msg_app_flow_control_full ensures:
# 1. msgApp can fill the sending window until full
# 2. when the window is full, no more msgApp can be sent.
def test_msg_app_flow_control_full():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(
        id=1,
        peers=[1, 2],
        election=5,
        heartbeat=1,
        storage=storage.make_ref(),
        logger=l.make_ref(),
    )

    r.raft.make_ref().become_candidate()
    r.raft.make_ref().become_leader()

    # force the progress to be in replicate state
    r.raft.make_ref().prs().get(2).become_replicate()

    # fill in the inflights window
    for i in range(0, r.raft.make_ref().get_max_inflight()):
        r.raft.make_ref().step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 1, f"#{i}: ms count = {ms.len()}, want 1"

    # ensure 1
    assert r.raft.make_ref().prs().get(2).get_ins().full()

    # ensure 2
    for i in range(0, 10):
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 0, f"#{i}: ms count = {len(ms)}, want 0"


# test_msg_app_flow_control_move_forward ensures msgAppResp can move
# forward the sending window correctly:
# 1. valid msgAppResp.index moves the windows to pass all smaller or equal index.
# 2. out-of-dated msgAppResp has no effect on the sliding window.
def test_msg_app_flow_control_move_forward():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(
        id=1,
        peers=[1, 2],
        election=5,
        heartbeat=1,
        storage=storage.make_ref(),
        logger=l.make_ref(),
    )

    r.raft.make_ref().become_candidate()
    r.raft.make_ref().become_leader()

    # force the progress to be in replicate state
    r.raft.make_ref().prs().get(2).become_replicate()

    # fill in the inflights window
    for i in range(0, r.raft.make_ref().get_max_inflight()):
        r.raft.make_ref().step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.read_messages()

    # 1 is noop, 2 is the first proposal we just sent.
    # so we start with 2.
    for tt in range(2, r.raft.make_ref().get_max_inflight()):
        m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
        m.make_ref().set_index(tt)
        r.step(m)
        r.read_messages()

        # fill in the inflights window again
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 1, f"#{tt}: ms count = {len(ms)}, want 1"

        # ensure 1
        assert r.raft.make_ref().prs().get(2).get_ins().full()

        # ensure 2
        for i in range(0, tt):
            m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
            m.make_ref().set_index(i)
            r.step(m)
            assert (
                r.raft.make_ref().prs().get(2).get_ins().full()
            ), f"#{tt}: inflights.full = {r.raft.make_ref().prs().get(2).get_ins().full()}, want true"


# test_msg_app_flow_control_recv_heartbeat ensures a heartbeat response
# frees one slot if the window is full.
def test_msg_app_flow_control_recv_heartbeat():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(
        id=1,
        peers=[1, 2],
        election=5,
        heartbeat=1,
        storage=storage.make_ref(),
        logger=l.make_ref(),
    )

    r.raft.make_ref().become_candidate()
    r.raft.make_ref().become_leader()

    # force the progress to be in replicate state
    r.raft.make_ref().prs().get(2).become_replicate()

    # fill in the inflights window
    for _ in range(0, r.raft.make_ref().get_max_inflight()):
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.read_messages()

    for tt in range(1, 5):
        assert (
            r.raft.make_ref().prs().get(2).get_ins().full()
        ), f"#{tt}: inflights.full = False, want True"

        # recv tt MsgHeartbeatResp and expect one free slot
        for i in range(0, tt):
            r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
            r.read_messages()
            assert (
                not r.raft.make_ref().prs().get(2).get_ins().full()
            ), f"#{tt}.{i}: inflights.full = True, want False"

        # one slot
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 1, f"#{tt}: free slot = 0, want 1"

        # and just one slot
        for i in range(0, 10):
            r.step(new_message(1, 1, MessageType.MsgPropose, 1))
            msl = r.read_messages()
            assert len(msl) == 0, f"#{tt}.{i}, ms1 should be empty."

        # clear all pending messages
        r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
        r.read_messages()


# TODO: Add below test after upgrading raft-rs v0.7.
def test_msg_app_flow_control_with_freeing_resources():
    pass


# TODO: Add below test after upgrading raft-rs v0.7.
def test_disable_progress():
    pass
