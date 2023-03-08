def conf_change():
    pass

def must_cmp_ready():
    pass

def new_raw_node():
    pass

def new_raw_node_with_config():
    pass

# Ensures that RawNode::step ignore local message.
def test_raw_node_step():
    pass

# Ensures that MsgReadIndex to old leader gets forwarded to the new leader and
# 'send' method does not attach its term.
def test_raw_node_read_index_to_old_leader():
    pass

# Tests the configuration change mechanism. Each test case sends a configuration
# change which is either simple or joint, verifies that it applies and that the
# resulting ConfState matches expectations, and for joint configurations makes
# sure that they are exited successfully.
def test_raw_node_propose_and_conf_change():
    pass

# Tests the configuration change auto leave even leader lost leadership.
def test_raw_node_joint_auto_leave():
    pass

# Ensures that two proposes to add the same node should not affect the later propose
# to add new node.
def test_raw_node_propose_add_duplicate_node():
    pass

def test_raw_node_propose_add_learner_node():
    pass

# Ensures that RawNode.read_index sends the MsgReadIndex message to the underlying
# raft. It also ensures that ReadState can be read out.
def test_raw_node_read_index():
    pass

# Ensures that a node can be started correctly. Note that RawNode requires the
# application to bootstrap the state, i.e. it does not accept peers and will not
# create faux configuration change entries.
def test_raw_node_start():
    pass

def test_raw_node_restart():
    pass

def test_raw_node_restart_from_snapshot():
    pass

# test_skip_bcast_commit ensures that empty commit message is not sent out
# when skip_bcast_commit is true.
def test_skip_bcast_commit():
    pass

# test_set_priority checks the set_priority function in RawNode.
def test_set_priority():
    pass

# TestNodeBoundedLogGrowthWithPartition tests a scenario where a leader is
# partitioned from a quorum of nodes. It verifies that the leader's log is
# protected from unbounded growth even as new entries continue to be proposed.
# This protection is provided by the max_uncommitted_size configuration.
def test_bounded_uncommitted_entries_growth_with_partition():
    pass

def prepare_async_entries():
    pass

# Test entries are handled properly when they are fetched asynchronously
def test_raw_node_with_async_entries():
    pass

# Test if async fetch entries works well when there is a remove node conf-change.
def test_raw_node_with_async_entries_to_removed_node():
    pass

# Test if async fetch entries works well when there is a leader step-down.
def test_raw_node_with_async_entries_on_follower():
    pass

def test_raw_node_async_entries_with_leader_change():
    pass

def test_raw_node_with_async_apply():
    pass

# Test if the ready process is expected when a follower receives a snapshot
# and some committed entries after its snapshot.
def test_raw_node_entries_after_snapshot():
    pass

# Test if the given committed entries are persisted when some persisted
# entries are overwritten by a new leader.
def test_raw_node_overwrite_entries():
    pass

# Test if async ready process is expected when a leader receives
# the append response and persist its entries.
def test_async_ready_leader():
    pass

# Test if async ready process is expected when a follower receives
# some append msg and snapshot.
def test_async_ready_follower():
    pass

# Test if a new leader immediately sends all messages recorded before without
# persisting.
def test_async_ready_become_leader():
    pass

def test_async_ready_multiple_snapshot():
    pass

def test_committed_entries_pagination():
    pass

# Test with `commit_since_index`, committed entries can be fetched correctly after restart.
#
# Case steps:
# - Node learns that index 10 is committed
# - `next_entries` returns entries [2..11) in committed_entries (but index 10 already
#   exceeds maxBytes), which isn't noticed internally by Raft
# - Commit index gets bumped to 10
# - The node persists the `HardState`, but crashes before applying the entries
# - Upon restart, the storage returns the same entries, but `slice` takes a
#   different code path and removes the last entry.
# - Raft does not emit a HardState, but when the app calls advance(), it bumps
#   its internal applied index cursor to 10 (when it should be 9)
# - The next `Ready` asks the app to apply index 11 (omitting index 10), losing a
#   write.
def test_committed_entries_pagination_after_restart():
    pass
