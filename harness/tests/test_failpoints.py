from harness.utils import hard_state, new_message, new_test_raft, new_storage
from rraft import MessageType, default_logger


# test_reject_stale_term_message tests that if a server receives a request with
# a stale term number, it rejects the request.
# Our implementation ignores the request instead.
# Reference: section 5.1
def test_reject_stale_term_message():
    l = default_logger()
    storage = new_storage()
    r = new_test_raft(1, [1, 2, 3], 10, 1, storage, l)
    hs = hard_state(2, 0, 0)
    r.raft.load_state(hs)

    m = new_message(0, 0, MessageType.MsgAppend, 0)
    m.set_term(r.raft.get_term() - 1)
    r.step(m)


# ensure that the Step function ignores the message from old term and does not pass it to the
# actual stepX function.
def test_step_ignore_old_term_msg():
    l = default_logger()
    storage = new_storage()
    sm = new_test_raft(1, [1], 10, 1, storage, l)
    sm.raft.set_term(2)
    m = new_message(0, 0, MessageType.MsgAppend, 0)
    m.set_term(1)
    sm.step(m)
