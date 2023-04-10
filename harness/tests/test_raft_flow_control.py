from harness.utils import new_message, new_storage, new_test_raft
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
        storage=storage,
        logger=l,
    )

    r.raft.become_candidate()
    r.raft.become_leader()

    # force the progress to be in replicate state
    r.raft.prs().get(2).become_replicate()

    # fill in the inflights window
    for i in range(0, r.raft.get_max_inflight()):
        r.raft.step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 1, f"#{i}: ms count = {ms.len()}, want 1"

    # ensure 1
    assert r.raft.prs().get(2).get_ins().full()

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
        storage=storage,
        logger=l,
    )

    r.raft.become_candidate()
    r.raft.become_leader()

    # force the progress to be in replicate state
    r.raft.prs().get(2).become_replicate()

    # fill in the inflights window
    for i in range(0, r.raft.get_max_inflight()):
        r.raft.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.read_messages()

    # 1 is noop, 2 is the first proposal we just sent.
    # so we start with 2.
    for tt in range(2, r.raft.get_max_inflight()):
        m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
        m.set_index(tt)
        r.step(m)
        r.read_messages()

        # fill in the inflights window again
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        ms = r.read_messages()
        assert len(ms) == 1, f"#{tt}: ms count = {len(ms)}, want 1"

        # ensure 1
        assert r.raft.prs().get(2).get_ins().full()

        # ensure 2
        for i in range(0, tt):
            m = new_message(2, 1, MessageType.MsgAppendResponse, 0)
            m.set_index(i)
            r.step(m)
            assert (
                r.raft.prs().get(2).get_ins().full()
            ), f"#{tt}: inflights.full = {r.raft.prs().get(2).get_ins().full()}, want true"


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
        storage=storage,
        logger=l,
    )

    r.raft.become_candidate()
    r.raft.become_leader()

    # force the progress to be in replicate state
    r.raft.prs().get(2).become_replicate()

    # fill in the inflights window
    for _ in range(0, r.raft.get_max_inflight()):
        r.step(new_message(1, 1, MessageType.MsgPropose, 1))
        r.read_messages()

    for tt in range(1, 5):
        assert (
            r.raft.prs().get(2).get_ins().full()
        ), f"#{tt}: inflights.full = False, want True"

        # recv tt MsgHeartbeatResp and expect one free slot
        for i in range(0, tt):
            r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))
            r.read_messages()
            assert (
                not r.raft.prs().get(2).get_ins().full()
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


def test_msg_app_flow_control_with_freeing_resources():
    l = default_logger()
    s = new_storage()
    r = new_test_raft(1, [1, 2, 3], 5, 1, s, l)

    r.raft.become_candidate()
    r.raft.become_leader()

    for pr in r.raft.prs().collect():
        assert not pr.progress().get_ins().buffer_is_allocated()

    for i in range(1, 3 + 1):
        # Force the progress to be in replicate state.
        r.raft.prs().get(i).become_replicate()

    r.raft.step(new_message(1, 1, MessageType.MsgPropose, 1))

    for pr in r.raft.prs().collect():
        if pr.id() != 1:
            assert pr.progress().get_ins().buffer_is_allocated()
            assert pr.progress().get_ins().count() == 1

    # 1: cap=0/start=0/count=0/buffer=[]
    # 2: cap=256/start=0/count=1/buffer=[2]
    # 3: cap=256/start=0/count=1/buffer=[2]

    resp = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    resp.set_index(r.raft_log.last_index())
    r.step(resp)

    assert r.raft.prs().get(2).get_ins().count() == 0

    # 1: cap=0/start=0/count=0/buffer=[]
    # 2: cap=256/start=1/count=0/buffer=[2]
    # 3: cap=256/start=0/count=1/buffer=[2]

    r.step(new_message(1, 1, MessageType.MsgPropose, 1))

    assert r.raft.prs().get(2).get_ins().count(), 1
    assert r.raft.prs().get(3).get_ins().count(), 2

    # 1: cap=0/start=0/count=0/buffer=[]
    # 2: cap=256/start=1/count=1/buffer=[2,3]
    # 3: cap=256/start=0/count=2/buffer=[2,3]

    resp = new_message(2, 1, MessageType.MsgAppendResponse, 0)
    resp.set_index(r.raft_log.last_index())
    r.step(resp)

    assert r.raft.prs().get(2).get_ins().count() == 0
    assert r.raft.prs().get(3).get_ins().count() == 2
    assert r.raft.inflight_buffers_size() == 4096

    # 1: cap=0/start=0/count=0/buffer=[]
    # 2: cap=256/start=2/count=0/buffer=[2,3]
    # 3: cap=256/start=0/count=2/buffer=[2,3]

    r.raft.maybe_free_inflight_buffers()

    assert not r.raft.prs().get(2).get_ins().buffer_is_allocated()
    assert r.raft.prs().get(2).get_ins().count() == 0
    assert r.raft.inflight_buffers_size() == 2048

    # 1: cap=0/start=0/count=0/buffer=[]
    # 2: cap=0/start=0/count=0/buffer=[]
    # 3: cap=256/start=0/count=2/buffer=[2,3]


def test_disable_progress():
    l = default_logger()
    s = new_storage()
    r = new_test_raft(1, [1, 2], 5, 1, s, l)
    r.raft.become_candidate()
    r.raft.become_leader()

    r.raft.prs().get(2).become_replicate()

    # Disable the progress 2. Internal `free`s shouldn't fail.
    r.raft.adjust_max_inflight_msgs(2, 0)
    r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))

    assert r.raft.prs().get(2).get_ins().full()
    assert not r.raft.prs().get(2).get_ins().count()

    # Progress 2 is disabled.
    msgs = r.read_messages()
    assert not msgs

    # After the progress gets enabled and a heartbeat response is received,
    # its leader can continue to append entries to it.
    r.raft.adjust_max_inflight_msgs(2, 10)
    r.step(new_message(2, 1, MessageType.MsgHeartbeatResponse, 0))

    msgs = r.read_messages()
    assert len(msgs) == 1
    assert msgs[0].get_msg_type() == MessageType.MsgAppend
