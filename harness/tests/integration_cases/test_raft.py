def read_messages():
    pass


def ents_with_config():
    pass


def assert_raft_log():
    pass


# voted_with_config creates a raft state machine with vote and term set
# to the given value but no log entries (indicating that it voted in
# the given term but has not receive any logs).
def voted_with_config():
    pass


# Persist committed index and fetch next entries.
def next_ents():
    pass


def test_progress_committed_index():
    pass


def test_progress_leader():
    pass


def test_progress_resume_by_heartbeat_resp():
    pass


def test_progress_paused():
    pass


def test_progress_flow_control():
    pass


def test_leader_election():
    pass


def test_leader_election_pre_vote():
    pass


def test_leader_election_with_config():
    pass


def test_leader_cycle():
    pass


def test_leader_cycle_pre_vote():
    pass


# test_leader_cycle verifies that each node in a cluster can campaign
# and be elected in turn. This ensures that elections (including
# pre-vote) work when not starting from a clean state (as they do in
# test_leader_election)
def test_leader_cycle_with_config():
    pass


def test_leader_election_overwrite_newer_logs():
    pass


def test_leader_election_overwrite_newer_logs_pre_vote():
    pass


# test_leader_election_overwrite_newer_logs tests a scenario in which a
# newly-elected leader does *not* have the newest (i.e. highest term)
# log entries, and must overwrite higher-term log entries with
# lower-term ones.
def test_leader_election_overwrite_newer_logs_with_config():
    pass


def test_vote_from_any_state():
    pass


def test_prevote_from_any_state():
    pass


def test_vote_from_any_state_for_type():
    pass


def test_log_replication():
    pass


def test_log_replication():
    pass


def test_single_node_commit():
    pass


# test_cannot_commit_without_new_term_entry tests the entries cannot be committed
# when leader changes, no new proposal comes in and ChangeTerm proposal is
# filtered.
def test_cannot_commit_without_new_term_entry():
    pass


# test_commit_without_new_term_entry tests the entries could be committed
# when leader changes, no new proposal comes in.
def test_commit_without_new_term_entry():
    pass


def test_dueling_candidates():
    pass


def test_dueling_pre_candidates():
    pass


def test_candidate_concede():
    pass


def test_single_node_candidate():
    pass


def test_sinle_node_pre_candidate():
    pass


def test_old_messages():
    pass


def test_proposal():
    pass


def test_proposal_by_proxy():
    pass


def test_commit():
    pass


def test_pass_election_timeout():
    pass


# test_handle_msg_append ensures:
# 1. Reply false if log doesn’t contain an entry at prevLogIndex whose term matches prevLogTerm.
# 2. If an existing entry conflicts with a new one (same index but different terms),
#    delete the existing entry and all that follow it; append any new entries not already in the
#    log.
# 3. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry).
def test_handle_msg_append():
    pass


# test_handle_heartbeat ensures that the follower commits to the commit in the message.
def test_handle_heartbeat():
    pass


# test_handle_heartbeat_resp ensures that we re-send log entries when we get a heartbeat response.
def test_handle_heartbeat_resp():
    pass


# test_raft_frees_read_only_mem ensures raft will free read request from
# ReadOnly read_index_queue and pending_read_index map.
# related issue: https://github.com/coreos/etcd/issues/7571
def test_raft_frees_read_only_mem():
    pass


# test_msg_append_response_wait_reset verifies the waitReset behavior of a leader
# MsgAppResp.
def test_msg_append_response_wait_reset():
    pass


def test_recv_msg_request_vote():
    pass


def test_recv_msg_request_vote_for_type():
    pass


def test_state_transition():
    pass


def test_all_server_stepdown():
    pass


def test_candidate_reset_term_msg_heartbeat():
    pass


def test_candidate_reset_term_msg_append():
    pass


# test_candidate_reset_term tests when a candidate receives a
# MsgHeartbeat or MsgAppend from leader, "step" resets the term
# with leader's and reverts back to follower.
def test_candidate_reset_term():
    pass


def test_leader_stepdown_when_quorum_active():
    pass


def test_leader_stepdown_when_quorum_lost():
    pass


def test_leader_superseding_with_check_quorum():
    pass


def test_leader_election_with_check_quorum():
    pass


# test_free_stuck_candidate_with_check_quorum ensures that a candidate with a higher term
# can disrupt the leader even if the leader still "officially" holds the lease, The
# leader is expected to step down and adopt the candidate's term
def test_free_stuck_candidate_with_check_quorum():
    pass


def test_non_promotable_voter_with_check_quorum():
    pass


# `test_disruptive_follower` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a candidate with an increased term. Then, the
# candiate's response to late leader heartbeat forces the leader
def test_disruptive_follower():
    pass


# `test_disruptive_follower_pre_vote` tests isolated follower,
# with slow network incoming from leader, election times out
# to become a pre-candidate with less log than current leader.
# Then pre-vote phase prevents this isolated node from forcing
# current leader to step down, thus less disruptions.
def test_disruptive_follower_pre_vote():
    pass


def test_read_only_option_safe():
    pass


def test_read_only_with_learner():
    pass


def test_read_only_option_lease():
    pass


def test_read_only_option_lease_without_check_quorum():
    pass


# `test_read_only_for_new_leader` ensures that a leader only accepts MsgReadIndex message
# when it commits at least one log entry at it term.
def test_read_only_for_new_leader():
    pass


# `test_advance_commit_index_by_read_index_response` ensures that read index response
# can advance the follower's commit index if it has new enough logs
def test_advance_commit_index_by_read_index_response():
    pass


def test_leader_append_response():
    pass


# When the leader receives a heartbeat tick, it should
# send a MsgApp with m.Index = 0, m.LogTerm=0 and empty entries.
def test_bcast_beat():
    pass


# tests the output of the statemachine when receiving MsgBeat
def test_recv_msg_beat():
    pass


def test_leader_increase_next():
    pass


def test_send_append_for_progress_probe():
    pass


def test_send_append_for_progress_replicate():
    pass


def test_send_append_for_progress_snapshot():
    pass


def test_recv_msg_unreachable():
    pass


def test_restore():
    pass


def test_restore_ignore_snapshot():
    pass


def test_provide_snap():
    pass


def test_ignore_providing_snapshot():
    pass


def test_restore_from_snap_msg():
    pass


def test_slow_node_restore():
    pass


# test_step_config tests that when raft step msgProp in EntryConfChange type,
# it appends the entry to log and sets pendingConf to be true.
def test_step_config():
    pass


def test_step_ignore_config():
    pass


# test_new_leader_pending_config tests that new leader sets its pending_conf_index
# based on uncommitted entries.
def test_new_leader_pending_config():
    pass


# test_add_node tests that add_node could update nodes correctly.
def test_add_node():
    pass


def test_add_node_check_quorum():
    pass


# test_remove_node tests that removeNode could update pendingConf, nodes and
# and removed list correctly.
def test_remove_node():
    pass


def test_remove_node_itself():
    pass


def test_promotable():
    pass


def test_raft_nodes():
    pass


def test_campaign_while_leader():
    pass


def test_campaign_while_leader_with_pre_vote():
    pass


# test_commit_after_remove_node verifies that pending commands can become
# committed when a config change reduces the quorum requirements.
def test_commit_after_remove_node():
    pass


# test_leader_transfer_to_uptodate_node verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
def test_leader_transfer_to_uptodate_node():
    pass


# test_leader_transfer_to_uptodate_node_from_follower verifies transferring should succeed
# if the transferee has the most up-to-date log entries when transfer starts.
# Not like test_leader_transfer_to_uptodate_node, where the leader transfer message
# is sent to the leader, in this test case every leader transfer message is sent
# to the follower.
def test_leader_transfer_to_uptodate_node_from_follower():
    pass


# TestLeaderTransferWithCheckQuorum ensures transferring leader still works
# even the current leader is still under its leader lease
def test_leader_transfer_with_check_quorum():
    pass


def test_leader_transfer_to_slow_follower():
    pass


def test_leader_transfer_after_snapshot():
    pass


def test_leader_transfer_to_self():
    pass


def test_leader_transfer_to_non_existing_node():
    pass


def test_leader_transfer_to_learner():
    pass


def test_leader_transfer_timeout():
    pass


def test_leader_transfer_ignore_proposal():
    pass


def test_leader_transfer_receive_higher_term_vote():
    pass


def test_leader_transfer_remove_node():
    pass


# test_leader_transfer_back verifies leadership can transfer
# back to self when last transfer is pending.
def test_leader_transfer_back():
    pass


# test_leader_transfer_second_transfer_to_another_node verifies leader can transfer to another node
# when last transfer is pending.
def test_leader_transfer_second_transfer_to_another_node():
    pass


# test_leader_transfer_second_transfer_to_same_node verifies second transfer leader request
# to the same node should not extend the timeout while the first one is pending.
def test_leader_transfer_second_transfer_to_same_node():
    pass


def check_leader_transfer_state():
    pass


# test_transfer_non_member verifies that when a MsgTimeoutNow arrives at
# a node that has been removed from the group, nothing happens.
# (previously, if the node also got votes, it would panic as it
# transitioned to StateRole::Leader)
def test_transfer_non_member():
    pass


# TestNodeWithSmallerTermCanCompleteElection tests the scenario where a node
# that has been partitioned away (and fallen behind) rejoins the cluster at
# about the same time the leader node gets partitioned away.
# Previously the cluster would come to a standstill when run with PreVote
# enabled.
def test_node_with_smaller_term_can_complete_election():
    pass


def new_test_learner_raft():
    pass


def new_test_learner_raft_with_prevote():
    pass


# TestLearnerElectionTimeout verifies that the leader should not start election
# even when times out.
def test_learner_election_timeout():
    pass


# TestLearnerPromotion verifies that the leaner should not election until
# it is promoted to a normal peer.
def test_learner_promotion():
    pass


# TestLearnerLogReplication tests that a learner can receive entries from the leader.
def test_learner_log_replication():
    pass


# TestRestoreWithLearner restores a snapshot which contains learners.
def test_restore_with_learner():
    pass


# Tests if outgoing voters can restore snapshot correctly.
def test_restore_with_voters_outgoing():
    pass


# Verifies that a voter can be depromoted by snapshot.
def test_restore_depromote_voter():
    pass


def test_restore_learner():
    pass


# TestRestoreLearnerPromotion checks that a learner can become to a follower after
# restoring snapshot.
def test_restore_learner_promotion():
    pass


# TestLearnerReceiveSnapshot tests that a learner can receive a snapshot from leader.
def test_learner_receive_snapshot():
    pass


# TestAddLearner tests that addLearner could update nodes correctly.
def test_add_learner():
    pass


# TestRemoveLearner tests that removeNode could update nodes and
# and removed list correctly.
def test_remove_learner():
    pass


# simulate rolling update a cluster for Pre-Vote. cluster has 3 nodes [n1, n2, n3].
# n1 is leader with term 2
# n2 is follower with term 2
# n3 is partitioned, with term 4 and less log, state is candidate
def new_prevote_migration_cluster():
    pass


def test_prevote_migration_can_complete_election():
    pass


def test_prevote_migration_with_free_stuck_pre_candidate():
    pass


def test_learner_respond_vote():
    pass


def test_election_tick_range():
    pass


# TestPreVoteWithSplitVote verifies that after split vote, cluster can complete
# election in next round.
def test_prevote_with_split_vote():
    pass


# ensure that after a node become pre-candidate, it will checkQuorum correctly.
def test_prevote_with_check_quorum():
    pass


# ensure a new Raft returns a Error::ConfigInvalid with an invalid config
def test_new_raft_with_bad_config_errors():
    pass


# tests whether MsgAppend are batched
def test_batch_msg_append():
    pass


# Tests if unapplied conf change is checked before campaign.
def test_conf_change_check_before_campaign():
    pass


def test_advance_commit_index_by_vote_request():
    pass


def test_advance_commit_index_by_direct_vote_request():
    pass


# Tests the commit index can be advanced by direct vote request
def test_advance_commit_index_by_prevote_request():
    pass


# Tests the commit index can be advanced by prevote request
def test_advance_commit_index_by_vote_response():
    pass


# Tests the commit index can be forwarded by direct vote response
def test_advance_commit_index_by_direct_vote_response():
    pass


# Tests the commit index can be forwarded by prevote response
def test_advance_commit_index_by_prevote_response():
    pass


def prepare_request_snapshot():
    pass


# Test if an up-to-date follower can request a snapshot from leader.
def test_follower_request_snapshot():
    pass


# Test if request snapshot can make progress when it meets SnapshotTemporarilyUnavailable.
def test_request_snapshot_unavailable():
    pass


# Test if request snapshot can make progress when matched is advanced.
def test_request_snapshot_matched_change():
    pass


# Test if request snapshot can make progress when the peer is not Replicate.
def test_request_snapshot_none_replicate():
    pass


# Test if request snapshot can make progress when leader steps down.
def test_request_snapshot_step_down():
    pass


# Abort request snapshot if it becomes leader or candidate.
def test_request_snapshot_on_role_change():
    pass


# Tests group commit.
#
# 1. Logs should be replicated to at least different groups before committed;
# 2. all peers are configured to the same group, simple quorum should be used.
def test_group_commit():
    pass


def test_group_commit_consistent():
    pass


# test_election_with_priority_log verifies the correctness
# of the election with both priority and log.
def test_election_with_priority_log():
    pass


# test_election_after_change_priority verifies that a peer can win an election
# by raising its priority and lose election by lowering its priority.
def test_election_after_change_priority():
    pass


# `test_read_when_quorum_becomes_less` tests read requests could be handled earlier
# if quorum becomes less in configuration changes.
def test_read_when_quorum_becomes_less():
    pass


def test_uncommitted_entries_size_limit():
    pass


def test_uncommitted_entry_after_leader_election():
    pass


def test_uncommitted_state_advance_ready_from_last_term():
    pass


def test_fast_log_rejection():
    pass


def test_switching_check_quorum():
    pass
