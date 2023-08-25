"""
Type hints for Native Rust Extension
"""
from abc import ABCMeta, abstractmethod
from typing import Any, Final, List, Optional, Set, Tuple

"""
A number to represent that there is no limit.
"""
NO_LIMIT: Final[Any]

"""
CAMPAIGN_ELECTION represents a normal (time-based) election (the second phase
of the election when Config.pre_vote is true).
"""
CAMPAIGN_ELECTION: Final[Any]

"""
CAMPAIGN_PRE_ELECTION represents the first phase of a normal election when
Config.pre_vote is true.
"""
CAMPAIGN_PRE_ELECTION: Final[Any]

"""
CAMPAIGN_TRANSFER represents the type of leader transfer.
"""
CAMPAIGN_TRANSFER: Final[Any]

"""
A constant represents invalid id of raft.
"""
INVALID_ID: Final[Any]

"""
A constant represents invalid index of raft log.
"""
INVALID_INDEX: Final[Any]

def majority(total: int) -> int:
    """
    Get the majority number of given nodes count.
    """

def default_logger() -> "Logger":
    """
    The default logger we fall back to when passed `None` in external_bindings facing constructors.

    Currently, this is a `log` adaptor behind a `Once` to ensure there is no clobbering.
    """

def vote_resp_msg_type(t: "MessageType") -> "MessageType":
    """
    Maps vote and pre_vote message types to their correspond responses.
    """

class __Cloneable(metaclass=ABCMeta):
    @abstractmethod
    def clone(self) -> Any: ...

class __Encoder:
    def encode(self) -> bytes:
        """ """

class __Decoder:
    @staticmethod
    def decode(v: bytes) -> Any:
        """ """

def set_snapshot_data_deserializer(cb: Any) -> None:
    """ """

def set_message_context_deserializer(cb: Any) -> None:
    """ """

def set_confchange_context_deserializer(cb: Any) -> None:
    """ """

def set_confchangev2_context_deserializer(cb: Any) -> None:
    """ """

def set_entry_data_deserializer(cb: Any) -> None:
    """ """

def set_entry_context_deserializer(cb: Any) -> None:
    """ """

class OverflowStrategy:
    """ """

    Block: Final[Any]
    Drop: Final[Any]
    DropAndReport: Final[Any]

class SnapshotStatus:
    """The status of the snapshot."""

    """
    Represents that the snapshot is finished being created.
    """
    Finish: Final[Any]

    """
    Indicates that the snapshot failed to build or is not ready.
    """
    Failure: Final[Any]

class ProgressState:
    """The state of the progress."""

    """
    Whether it's probing.
    """
    Probe: Final[Any]

    """
    Whether it's replicating.
    """
    Replicate: Final[Any]

    """
    Whether it's a snapshot.
    """
    Snapshot: Final[Any]

class StateRole:
    """The role of the node."""

    """
    The node could become a leader.
    """
    Candidate: Final[Any]

    """
    The node is a follower of the leader.
    """
    Follower: Final[Any]

    """
    The node is a leader.
    """
    Leader: Final[Any]

    """
    The node could become a candidate, if `prevote` is enabled.
    """
    PreCandidate: Final[Any]

class ReadOnlyOption:
    """Determines the relative safety of and consistency of read only requests."""

    """
    Safe guarantees the linearizability of the read only request by
    communicating with the quorum. It is the default and suggested option.
    """
    Safe: Final[Any]

    """
    LeaseBased ensures linearizability of the read only request by
    relying on the leader lease. It can be affected by clock drift.
    If the clock drift is unbounded, leader might keep the lease longer than it
    should (clock can move backward/pause without any bound). ReadIndex is not safe
    in that case.
    """
    LeaseBased: Final[Any]

class MessageType:
    """ """

    MsgHup: Final[Any]
    MsgBeat: Final[Any]
    MsgPropose: Final[Any]
    MsgAppend: Final[Any]
    MsgAppendResponse: Final[Any]
    MsgRequestVote: Final[Any]
    MsgRequestVoteResponse: Final[Any]
    MsgSnapshot: Final[Any]
    MsgHeartbeat: Final[Any]
    MsgHeartbeatResponse: Final[Any]
    MsgUnreachable: Final[Any]
    MsgSnapStatus: Final[Any]
    MsgCheckQuorum: Final[Any]
    MsgTransferLeader: Final[Any]
    MsgTimeoutNow: Final[Any]
    MsgReadIndex: Final[Any]
    MsgReadIndexResp: Final[Any]
    MsgRequestPreVote: Final[Any]
    MsgRequestPreVoteResponse: Final[Any]
    @staticmethod
    def from_int(v: int) -> "MessageType": ...

class ConfChangeTransition:
    """ """

    """
    Automatically use the simple protocol if possible, otherwise fall back
    to ConfChangeType::Implicit. Most applications will want to use this.
    """
    Auto: Final[Any]

    """
    Use joint consensus unconditionally, and transition out of them
    automatically (by proposing a zero configuration change).

    This option is suitable for applications that want to minimize the time
    spent in the joint configuration and do not store the joint configuration
    in the state machine (outside of InitialState).
    """
    Implicit: Final[Any]

    """
    Use joint consensus and remain in the joint configuration until the
    application proposes a no-op configuration change. This is suitable for
    applications that want to explicitly control the transitions, for example
    to use a custom payload (via the Context field).
    """
    Explicit: Final[Any]
    @staticmethod
    def from_int(v: int) -> "ConfChangeTransition": ...

class ConfChangeType:
    """ """

    AddNode: Final[Any]
    AddLearnerNode: Final[Any]
    RemoveNode: Final[Any]
    @staticmethod
    def from_int(v: int) -> "ConfChangeType": ...

class EntryType:
    """ """

    EntryConfChange: Final[Any]
    EntryConfChangeV2: Final[Any]
    EntryNormal: Final[Any]
    @staticmethod
    def from_int(v: int) -> "EntryType": ...

class __API_Logger:
    def info(self, s: str) -> None:
        """
        Log info level record

        See `slog_log` for documentation.
        """
    def debug(self, s: str) -> None:
        """
        Log debug level record

        See `slog_debug` for documentation.
        """
    def trace(self, s: str) -> None:
        """
        Log trace level record

        See `slog_trace` for documentation.
        """
    def crit(self, s: str) -> None:
        """
        Log crit level record

        See `slog_crit` for documentation.
        """
    def error(self, s: str) -> None:
        """
        Log error level record

        See `slog_error` for documentation.
        """

class Logger(__API_Logger):
    """ """

    def __init__(
        self, chan_size: int, overflow_strategy: "OverflowStrategy"
    ) -> None: ...
    @staticmethod
    def new_file_logger(log_path: str): ...
    def make_ref(self) -> "LoggerRef": ...

class LoggerRef(__API_Logger):
    """ """

class __API_RaftState(__Cloneable):
    def clone(self) -> "RaftState": ...
    def initialized(self) -> bool:
        """
        Indicates the `RaftState` is initialized or not.
        """
    def get_conf_state(self) -> "ConfStateRef":
        """
        `conf_state`: Records the current node IDs like `[1, 2, 3]` in the cluster. Every Raft node must have a
        unique ID in the cluster;
        """
    def set_conf_state(self, cs: "ConfStateRef") -> None:
        """
        `conf_state`: Records the current node IDs like `[1, 2, 3]` in the cluster. Every Raft node must have a
        unique ID in the cluster;
        """
    def get_hard_state(self) -> "HardStateRef":
        """
        `hard_state`: Contains the last meta information including commit index, the vote leader, and the vote term.
        """
    def set_hard_state(self, hs: "HardStateRef") -> None:
        """
        `hard_state`: Contains the last meta information including commit index, the vote leader, and the vote term.
        """

class RaftState(__API_RaftState):
    """
    Holds both the hard state (commit index, vote leader, term) and the configuration state
    (Current node IDs)
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "RaftStateRef": ...
    @staticmethod
    def default() -> "RaftState": ...

class RaftStateRef(__API_RaftState):
    """
    Reference type of :class:`RaftState`.
    """

class __API_StorageCore:
    def append(self, ents: List["Entry"] | List["EntryRef"]) -> None:
        """
        Append the new entries to storage.

        # Panics

        Panics if `ents` contains compacted entries, or there's a gap between `ents` and the last
        received entry in the storage.
        """
    def apply_snapshot(self, snapshot: "Snapshot" | "SnapshotRef") -> None:
        """
        Overwrites the contents of this Storage object with those of the given snapshot.

        # Panics

        Panics if the snapshot index is less than the storage's first index.
        """
    def compact(self, compact_index: int) -> None:
        """
        Discards all log entries prior to compact_index.
        It is the application's responsibility to not attempt to compact an index
        greater than RaftLog.applied.

        # Panics

        Panics if `compact_index` is higher than `Storage::last_index(&self) + 1`.
        """
    def commit_to(self, index: int) -> None:
        """
        Commit to an index.

        # Panics

        Panics if there is no such entry in raft logs.
        """
    def commit_to_and_set_conf_states(
        self, idx: int, cs: Optional["ConfState"] | Optional["ConfStateRef"]
    ) -> None:
        """
        Commit to `idx` and set configuration to the given states. Only used for tests.
        """
    def set_conf_state(self, cs: "ConfState" | "ConfStateRef") -> None:
        """
        Saves the current conf state.
        """
    def hard_state(self) -> "HardStateRef":
        """
        Get the hard state.
        """
    def set_hardstate(self, hs: "HardState" | "HardStateRef") -> None:
        """
        Saves the current HardState.
        """
    def trigger_snap_unavailable(self) -> None:
        """
        Trigger a SnapshotTemporarilyUnavailable error.
        """
    def trigger_log_unavailable(self, v: bool) -> None:
        """
        Set a LogTemporarilyUnavailable error.
        """
    def take_get_entries_context(self) -> Optional["GetEntriesContext"]:
        """
        Take get entries context.
        """

class MemStorageCore(__API_StorageCore):
    """
    The Memory Storage Core instance holds the actual state of the storage struct. To access this
    value, use the `rl` and `wl` functions on the main MemStorage implementation.
    """

    def make_ref(self) -> "MemStorageCoreRef": ...
    @staticmethod
    def default() -> "MemStorageCore": ...

class MemStorageCoreRef(__API_StorageCore):
    """
    Reference type of :class:`MemStorage`.
    """

class StorageCore(__API_StorageCore):
    """ """

    def make_ref(self) -> "StorageCoreRef": ...
    @staticmethod
    def default() -> "StorageCore": ...

class StorageCoreRef(__API_StorageCore):
    """
    Reference type of :class:`StorageCore`.
    """

class __API_Storage(__Cloneable):
    def clone(self) -> Any: ...
    def initialize_with_conf_state(
        self, conf_state: "ConfState" | "ConfStateRef"
    ) -> None:
        """
        Initialize a `MemStorage` with a given `Config`.

        You should use the same input to initialize all nodes.
        """
    def initial_state(self) -> RaftState:
        """
        Implements the Storage trait.
        """
    def entries(
        self,
        low: int,
        high: int,
        context: "GetEntriesContextRef",
        max_size: Optional[int],
    ) -> List["Entry"]:
        """
        Implements the Storage trait.
        """
    def term(self, idx: int) -> int:
        """
        Implements the Storage trait.
        """
    def first_index(self) -> int:
        """
        Implements the Storage trait.
        """
    def last_index(self) -> int:
        """
        Implements the Storage trait.
        """
    def snapshot(self, request_index: int, to: int) -> "Snapshot":
        """
        Implements the Storage trait.
        """

class MemStorage(__API_Storage):
    """
    `MemStorage` is a thread-safe but incomplete implementation of `Storage`, mainly for tests.

    A real `Storage` should save both raft logs and applied data. However `MemStorage` only
    contains raft logs. So you can call `MemStorage::append` to persist new received unstable raft
    logs and then access them with `Storage` APIs. The only exception is `Storage::snapshot`. There
    is no data in `Snapshot` returned by `MemStorage::snapshot` because applied data is not stored
    in `MemStorage`.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "MemStorageRef": ...
    def clone(self) -> "MemStorage": ...
    @staticmethod
    def default() -> "MemStorage": ...
    @staticmethod
    def new_with_conf_state(
        conf_state: "ConfState" | "ConfStateRef",
    ) -> "MemStorage":
        """
        Create a new `MemStorage` with a given `Config`. The given `Config` will be used to
        initialize the storage.

        You should use the same input to initialize all nodes.
        """
    def wl(self) -> "MemStorageCoreRef":
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self) -> "MemStorageCoreRef":
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class MemStorageRef(__API_Storage):
    """
    Reference type of :class:`MemStorage`.
    """

    def clone(self) -> "MemStorage": ...
    def wl(self) -> "MemStorageCoreRef":
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self) -> "MemStorageCoreRef":
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class Storage(__API_Storage):
    """
    Storage saves all the information about the current Raft implementation, including Raft Log,
    commit index, the leader to vote for, etc.

    If any Storage method returns an error, the raft instance will
    become inoperable and refuse to participate in elections; the
    application is responsible for cleanup and recovery in this case.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "StorageRef": ...
    def clone(self) -> "Storage": ...
    @staticmethod
    def default() -> "Storage": ...
    @staticmethod
    def new_with_conf_state(
        conf_state: "ConfState" | "ConfStateRef",
    ) -> "Storage":
        """ """
    def wl(self) -> Any:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self) -> Any:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class StorageRef(__API_Storage):
    """
    Reference type of :class:`Storage`.
    """

    def clone(self) -> "Storage": ...
    def wl(self) -> Any:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self) -> Any:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class __API_Ready:
    def hs(self) -> Optional["HardStateRef"]:
        """
        The current state of a Node to be saved to stable storage.
        HardState will be None state if there is no update.
        """
    def ss(self) -> Optional["SoftStateRef"]:
        """
        The current volatile state of a Node.
        SoftState will be None if there is no update.
        It is not required to consume or store SoftState.
        """
    def must_sync(self) -> bool:
        """
        MustSync is false if and only if
        1. no HardState or only its commit is different from before
        2. no Entries and Snapshot
        If it's false, an asynchronous write of HardState is permissible before calling
        [`RawNode::on_persist_ready`] or [`RawNode::advance`] or its families.
        """
    def number(self) -> int:
        """
        The number of current Ready.
        It is used for identifying the different Ready and ReadyRecord.
        """
    def snapshot(self) -> "SnapshotRef":
        """
        Snapshot specifies the snapshot to be saved to stable storage.
        """
    def committed_entries(self) -> List["EntryRef"]:
        """
        CommittedEntries specifies entries to be committed to a
        store/state-machine. These have previously been committed to stable
        store.
        """
    def take_committed_entries(self) -> List["Entry"]:
        """
        Take the CommitEntries.
        """
    def entries(self) -> List["EntryRef"]:
        """
        Entries specifies entries to be saved to stable storage.
        """
    def take_entries(self) -> List["Entry"]:
        """
        Take the Entries.
        """
    def messages(self) -> List["MessageRef"]:
        """
        Messages specifies outbound messages to be sent.
        If it contains a MsgSnap message, the application MUST report back to raft
        when the snapshot has been received or has failed by calling ReportSnapshot.
        """
    def take_messages(self) -> List["Message"]:
        """
        Take the Messages.
        """
    def persisted_messages(self) -> List["MessageRef"]:
        """
        Persisted Messages specifies outbound messages to be sent AFTER the HardState,
        Entries and Snapshot are persisted to stable storage.
        """
    def take_persisted_messages(self) -> List["Message"]:
        """
        Take the Persisted Messages.
        """
    def read_states(self) -> List["ReadStateRef"]:
        """
        ReadStates specifies the state for read only query.
        """
    def take_read_states(self) -> List["ReadState"]:
        """
        ReadStates specifies the state for read only query.
        """

class Ready(__API_Ready):
    """
    Ready encapsulates the entries and messages that are ready to read,
    be saved to stable storage, committed or sent to other peers.
    """

    def make_ref(self) -> "ReadyRef": ...
    @staticmethod
    def default() -> "Ready": ...

class ReadyRef(__API_Ready):
    """
    Reference type of :class:`Ready`.
    """

class __API_RawNode:
    def advance_apply(self) -> None:
        """
        Advance apply to the index of the last committed entries given before.
        """
    def advance_apply_to(self, applied: int) -> None:
        """
        Advance apply to the passed index.
        """
    def advance(self, rd: "ReadyRef") -> "LightReady":
        """
        Advances the ready after fully processing it.

        Fully processing a ready requires to persist snapshot, entries and hard states, apply all
        committed entries, send all messages.

        Returns the LightReady that contains commit index, committed entries and messages. [`LightReady`]
        contains updates that only valid after persisting last ready. It should also be fully processed.
        Then [`Self::advance_apply`] or [`Self::advance_apply_to`] should be used later to update applying
        progress.
        """
    def advance_append(self, rd: "ReadyRef") -> "LightReady":
        """
        Advances the ready without applying committed entries. [`Self::advance_apply`] or
        [`Self::advance_apply_to`] should be used later to update applying progress.

        Returns the LightReady that contains commit index, committed entries and messages.

        Since Ready must be persisted in order, calling this function implicitly means
        all ready collected before have been persisted.
        """
    def advance_append_async(self, rd: "ReadyRef") -> None:
        """
        Same as [`Self::advance_append`] except that it allows to only store the updates in cache.
        [`Self::on_persist_ready`] should be used later to update the persisting progress.

        Raft works on an assumption persisted updates should not be lost, which usually requires expensive
        operations like `fsync`. `advance_append_async` allows you to control the rate of such operations and
        get a reasonable batch size. However, it's still required that the updates can be read by raft from the
        `Storage` trait before calling `advance_append_async`.
        """
    def has_ready(self) -> bool:
        """
        HasReady called when RawNode user need to check if any Ready pending.
        """
    def tick(self) -> bool:
        """
        Tick advances the internal logical clock by a single tick.

        Returns true to indicate that there will probably be some readiness which
        needs to be handled.
        """
    def set_batch_append(self, batch_append: bool) -> None:
        """
        Set whether to batch append msg at runtime.
        """
    def set_priority(self, priority: int) -> None:
        """
        Sets priority of node.
        """
    def report_snapshot(self, id: int, snapshot: "SnapshotStatus") -> None:
        """
        ReportSnapshot reports the status of the sent snapshot.
        """
    def report_unreachable(self, id: int) -> None:
        """
        ReportUnreachable reports the given node is not reachable for the last send.
        """
    def transfer_leader(self, transferee: int) -> None:
        """
        TransferLeader tries to transfer leadership to the given transferee.
        """
    def snap(self) -> Optional["SnapshotRef"]:
        """
        Grabs the snapshot from the raft if available.
        """
    def step(self, msg: "Message" | "MessageRef") -> None:
        """
        Step advances the state machine using the given message.
        """
    def skip_bcast_commit(self, skip: bool) -> None:
        """
        Set whether skip broadcast empty commit messages at runtime.
        """
    def campaign(self) -> None:
        """
        Campaign causes this RawNode to transition to candidate state.
        """
    def propose(self, context: bytes, data: bytes) -> None:
        """
        Propose proposes data be appended to the raft log.
        """
    def propose_conf_change(
        self, context: bytes, cc: "ConfChange" | "ConfChangeRef"
    ) -> None:
        """
        ProposeConfChange proposes a config change.

        If the node enters joint state with `auto_leave` set to true, it's
        caller's responsibility to propose an empty conf change again to force
        leaving joint state.
        """
    def propose_conf_change_v2(
        self, context: bytes, cc: "ConfChangeV2" | "ConfChangeV2Ref"
    ) -> None:
        """
        ProposeConfChange proposes a config change.

        If the node enters joint state with `auto_leave` set to true, it's
        caller's responsibility to propose an empty conf change again to force
        leaving joint state.
        """
    def apply_conf_change(self, cc: "ConfChange" | "ConfChangeRef") -> ConfState:
        """
        Applies a config change to the local node. The app must call this when it
        applies a configuration change, except when it decides to reject the
        configuration change, in which case no call must take place.
        """
    def apply_conf_change_v2(
        self, cc: "ConfChangeV2" | "ConfChangeV2Ref"
    ) -> "ConfState":
        """
        Applies a config change to the local node. The app must call this when it
        applies a configuration change, except when it decides to reject the
        configuration change, in which case no call must take place.
        """
    def ping(self) -> None:
        """
        Broadcast heartbeats to all the followers.

        If it's not leader, nothing will happen.
        """
    def on_persist_ready(self, number: int) -> None:
        """
        Notifies that the ready of this number has been persisted.

        Since Ready must be persisted in order, calling this function implicitly means
        all readies with numbers smaller than this one have been persisted.

        [`Self::has_ready`] and [`Self::ready`] should be called later to handle further
        updates that become valid after ready being persisted.
        """
    def read_index(self, rctx: bytes) -> None:
        """
        ReadIndex requests a read state. The read state will be set in ready.
        Read State has a read index. Once the application advances further than the read
        index, any linearizable read requests issued before the read request can be
        processed safely. The read state will have the same rctx attached.
        """
    def ready(self) -> Ready:
        """
        Returns the outstanding work that the application needs to handle.

        This includes appending and applying entries or a snapshot, updating the HardState,
        and sending messages. The returned `Ready` *MUST* be handled and subsequently
        passed back via `advance` or its families. Before that, *DO NOT* call any function like
        `step`, `propose`, `campaign` to change internal state.

        [`Self::has_ready`] should be called first to check if it's necessary to handle the ready.
        """
    def request_snapshot(self) -> "Ready":
        """
        Request a snapshot from a leader.
        The snapshot's index must be greater or equal to the request_index (last_index) or
        the leader's term must be greater than the request term (last_index's term).
        """
    def on_entries_fetched(self) -> None:
        """
        A callback when entries are fetched asynchronously.
        The context should provide the context passed from Storage.entires().
        See more in the comment of Storage.entires().

        # Panics

        Panics if passed with the context of context.can_async() == false
        """

class InMemoryRawNode(__API_RawNode):
    """
    RawNode is a thread-unsafe Node.
    The methods of this struct correspond to the methods of Node and are described
    more fully there.
    """

    def __init__(
        self,
        cfg: "Config" | "ConfigRef",
        store: "MemStorage" | "MemStorageRef",
        logger: "Logger" | "LoggerRef",
    ) -> None: ...
    def make_ref(self) -> "InMemoryRawNodeRef": ...
    def get_raft(self) -> "InMemoryRaftRef":
        """ """
    def store(self) -> "MemStorageRef":
        """Returns the store as a mutable reference."""

class InMemoryRawNodeRef(__API_RawNode):
    """
    Reference type of :class:`InMemoryRawNode`.
    """

    def get_raft(self) -> "InMemoryRaftRef":
        """ """
    def store(self) -> "MemStorageRef":
        """Returns the store as a mutable reference."""
    # def status(self) -> InMemoryStatus:
    #     """
    #     Status returns the current status of the given group.
    #     """

class RawNode(__API_RawNode):
    """
    RawNode is a thread-unsafe Node.
    The methods of this struct correspond to the methods of Node and are described
    more fully there.
    """

    def __init__(
        self,
        cfg: "Config" | "ConfigRef",
        store: "Storage" | "StorageRef",
        logger: "Logger" | "LoggerRef",
    ) -> None: ...
    def make_ref(self) -> "RawNodeRef": ...
    def get_raft(self) -> "RaftRef":
        """ """
    def store(self) -> "StorageRef":
        """Returns the store as a mutable reference."""
    # def status(self) -> Status:
    #     """
    #     Status returns the current status of the given group.
    #     """

class RawNodeRef(__API_RawNode):
    """
    Reference type of :class:`RawNode`.
    """

    def get_raft(self) -> "RaftRef":
        """ """
    def store(self) -> "StorageRef":
        """Returns the store as a mutable reference."""
    # def status(self) -> InMemoryStatus:
    #     """
    #     Status returns the current status of the given group.
    #     """

class __API_Peer:
    def get_id(self) -> int:
        """
        `id`: The ID of the peer.
        """
    def set_id(self, id: int) -> None:
        """
        `id`: The ID of the peer.
        """
    def get_context(self) -> bytes:
        """
        `context`: If there is context associated with the peer (like connection information), it can be
        serialized and stored here.
        """
    def set_context(self, context: bytes) -> None:
        """
        `context`: If there is context associated with the peer (like connection information), it can be
        serialized and stored here.
        """

class Peer(__API_Peer):
    """
    Represents a Peer node in the cluster.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "PeerRef": ...

class PeerRef(__API_Peer):
    """
    Reference type of :class:`Peer`.
    """

class __API_LightReady:
    def commit_index(self) -> Optional[int]:
        """
        The current commit index.
        It will be None state if there is no update.
        It is not required to save it to stable storage.
        """
    def committed_entries(self) -> List["EntryRef"]:
        """
        CommittedEntries specifies entries to be committed to a
        store/state-machine. These have previously been committed to stable
        store.
        """
    def take_committed_entries(self) -> List["Entry"]:
        """
        Take the CommitEntries.
        """
    def messages(self) -> List["MessageRef"]:
        """
        Messages specifies outbound messages to be sent.
        """
    def take_messages(self) -> List["Message"]:
        """
        Take the Messages.
        """

class LightReady(__API_LightReady):
    """
    LightReady encapsulates the commit index, committed entries and
    messages that are ready to be applied or be sent to other peers.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "LightReadyRef": ...
    @staticmethod
    def default() -> "LightReady": ...

class LightReadyRef(__API_LightReady):
    """
    Reference type of :class:`LightReady`.
    """

class __API_SnapshotMetadata(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "SnapshotMetadata": ...
    def get_index(self) -> int:
        """
        `index`: The applied index.
        """
    def set_index(self, index: int) -> None:
        """
        `index`: The applied index.
        """
    def clear_index(self) -> None:
        """
        `index`: The applied index.
        """
    def get_term(self) -> int:
        """
        `term`: The term of the applied index.
        """
    def set_term(self, term: int) -> None:
        """
        `term`: The term of the applied index.
        """
    def clear_term(self) -> None:
        """
        `term`: The term of the applied index.
        """
    def get_conf_state(self) -> "ConfStateRef":
        """
        `conf_state`: The current `ConfState`.
        """
    def set_conf_state(self, conf_state: "ConfState" | "ConfStateRef") -> None:
        """
        `conf_state`: The current `ConfState`.
        """
    def clear_conf_state(self) -> None:
        """
        `conf_state`: The current `ConfState`.
        """
    def has_conf_state(self) -> bool:
        """
        `conf_state`: The current `ConfState`.
        """

class SnapshotMetadata(__API_SnapshotMetadata):
    """ """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> "SnapshotMetadata": ...
    @staticmethod
    def decode(v: bytes) -> "SnapshotMetadata": ...
    def make_ref(self) -> "SnapshotMetadataRef": ...

class SnapshotMetadataRef(__API_SnapshotMetadata):
    """
    Reference type of :class:`SnapshotMetadata`.
    """

class __API_Snapshot(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "Snapshot": ...
    def get_data(self) -> bytes:
        """ """
    def set_data(self, data: bytes) -> None:
        """ """
    def clear_data(self) -> None:
        """ """
    def get_metadata(self) -> "SnapshotMetadataRef":
        """ """
    def set_metadata(
        self, meta_data: "SnapshotMetadata" | "SnapshotMetadataRef"
    ) -> None:
        """ """
    def clear_metadata(self) -> None:
        """ """
    def has_metadata(self) -> bool:
        """ """

class Snapshot(__API_Snapshot):
    """ """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> "Snapshot": ...
    @staticmethod
    def decode(v: bytes) -> "Snapshot": ...
    def make_ref(self) -> "SnapshotRef": ...

class SnapshotRef(__API_Snapshot):
    """
    Reference type of :class:`Snapshot`.
    """

class __API_Message(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "Message": ...
    def get_commit(self) -> int:
        """ """
    def set_commit(self, commit: int) -> None:
        """ """
    def clear_commit(self) -> None:
        """ """
    def get_commit_term(self) -> int:
        """ """
    def set_commit_term(self, commit_term: int) -> None:
        """ """
    def clear_commit_term(self) -> None:
        """ """
    def get_from(self) -> int:
        """ """
    def set_from(self, from_: int) -> None:
        """ """
    def clear_from(self) -> None:
        """ """
    def get_index(self) -> int:
        """ """
    def set_index(self, index: int) -> None:
        """ """
    def clear_index(self) -> None:
        """ """
    def get_term(self) -> int:
        """ """
    def set_term(self, term: int) -> None:
        """ """
    def clear_term(self) -> None:
        """ """
    def get_log_term(self) -> int:
        """
        `logTerm`: logTerm is generally used for appending Raft logs to followers. For example,
        (type=MsgAppend,index=100,log_term=5) means leader appends entries starting at
        index=101, and the term of entry at index 100 is 5.
        (type=MsgAppendResponse,reject=true,index=100,log_term=5) means follower rejects some
        entries from its leader as it already has an entry with term 5 at index 100.
        """
    def set_log_term(self, log_index: int) -> None:
        """
        `logTerm`: logTerm is generally used for appending Raft logs to followers. For example,
        (type=MsgAppend,index=100,log_term=5) means leader appends entries starting at
        index=101, and the term of entry at index 100 is 5.
        (type=MsgAppendResponse,reject=true,index=100,log_term=5) means follower rejects some
        entries from its leader as it already has an entry with term 5 at index 100.
        """
    def clear_log_term(self) -> None:
        """
        `logTerm`: logTerm is generally used for appending Raft logs to followers. For example,
        (type=MsgAppend,index=100,log_term=5) means leader appends entries starting at
        index=101, and the term of entry at index 100 is 5.
        (type=MsgAppendResponse,reject=true,index=100,log_term=5) means follower rejects some
        entries from its leader as it already has an entry with term 5 at index 100.
        """
    def get_priority(self) -> int:
        """
        `priority`: If this new field is not set, then use the above old field; otherwise
        use the new field. When broadcasting request vote, both fields are
        set if the priority is larger than 0. This change is not a fully
        compatible change, but it makes minimal impact that only new priority
        is not recognized by the old nodes during rolling update.
        """
    def set_priority(self, priority: int) -> None:
        """
        `priority`: If this new field is not set, then use the above old field; otherwise
        use the new field. When broadcasting request vote, both fields are
        set if the priority is larger than 0. This change is not a fully
        compatible change, but it makes minimal impact that only new priority
        is not recognized by the old nodes during rolling update.
        """
    def clear_priority(self) -> None:
        """
        `priority`: If this new field is not set, then use the above old field; otherwise
        use the new field. When broadcasting request vote, both fields are
        set if the priority is larger than 0. This change is not a fully
        compatible change, but it makes minimal impact that only new priority
        is not recognized by the old nodes during rolling update.
        """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_reject_hint(self) -> int:
        """ """
    def set_reject_hint(self, reject_hint: bool) -> None:
        """ """
    def clear_reject_hint(self) -> None:
        """ """
    def get_entries(self) -> List["EntryRef"]:
        """ """
    def set_entries(self, ents: List["Entry"] | List["EntryRef"]) -> None:
        """ """
    def clear_entries(self) -> None:
        """ """
    def get_msg_type(self) -> "MessageType":
        """ """
    def set_msg_type(self, typ: "MessageType") -> None:
        """ """
    def clear_msg_type(self) -> None:
        """ """
    def get_reject(self) -> bool:
        """ """
    def set_reject(self, reject: bool) -> None:
        """ """
    def clear_reject(self) -> None:
        """ """
    def get_snapshot(self) -> "SnapshotRef":
        """ """
    def set_snapshot(self, snapshot: "Snapshot" | "SnapshotRef") -> None:
        """ """
    def clear_snapshot(self) -> None:
        """ """
    def get_to(self) -> int:
        """ """
    def set_to(self, to: int) -> None:
        """ """
    def clear_to(self) -> None:
        """ """
    def get_request_snapshot(self) -> int:
        """ """
    def set_request_snapshot(self, request_snapshot: int) -> None:
        """ """
    def clear_request_snapshot(self) -> None:
        """ """
    def has_snapshot(self) -> bool:
        """ """
    def compute_size(self) -> int:
        """
        Compute and cache size of this message and all nested messages
        """

class Message(__API_Message):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> "MessageRef": ...
    @staticmethod
    def default() -> "Message": ...
    @staticmethod
    def decode(v: bytes) -> "Message": ...

class MessageRef(Message):
    """
    Reference type of :class:`Message`.
    """

class __API_HardState(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "HardState": ...
    def get_term(self) -> int:
        """ """
    def set_term(self, term: int) -> None:
        """ """
    def clear_term(self) -> None:
        """ """
    def get_vote(self) -> int:
        """ """
    def set_vote(self, vote: int) -> None:
        """ """
    def clear_vote(self) -> None:
        """ """
    def get_commit(self) -> int:
        """ """
    def set_commit(self, commit: int) -> None:
        """ """
    def clear_commit(self) -> None:
        """ """

class HardState(__API_HardState):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> "HardStateRef": ...
    @staticmethod
    def default() -> "HardState": ...
    @staticmethod
    def decode(v: bytes) -> "HardState": ...

class HardStateRef(__API_HardState):
    """
    Reference type of :class:`HardState`.
    """

class __API_GetEntriesContext:
    def can_async(self) -> bool:
        """
        Check if the caller's context support fetching entries asynchronously.
        """

class GetEntriesContext(__API_GetEntriesContext):
    """
    Records the context of the caller who calls entries() of Storage trait.
    """

    @staticmethod
    def empty(can_async: bool) -> "GetEntriesContext":
        """
        Used for callers out of raft. Caller can customize if it supports async.
        """
    def make_ref(self) -> "GetEntriesContextRef": ...

class GetEntriesContextRef(__API_GetEntriesContext):
    """
    Reference type of :class:`GetEntriesContext`.
    """

class __API_Entry(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "Entry": ...
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_data(self) -> bytes:
        """ """
    def set_data(self, data: bytes) -> None:
        """ """
    def clear_data(self) -> None:
        """ """
    def get_entry_type(self) -> "EntryType":
        """ """
    def set_entry_type(self, typ: "EntryType") -> None:
        """ """
    def clear_entry_type(self) -> None:
        """ """
    def get_term(self) -> int:
        """ """
    def set_term(self, term: int) -> None:
        """ """
    def clear_term(self) -> None:
        """ """
    def get_index(self) -> int:
        """ """
    def set_index(self, index: int) -> None:
        """ """
    def clear_index(self) -> None:
        """ """
    def get_sync_log(self) -> bool:
        """
        Deprecated! It is kept for backward compatibility.
        TODO: remove it in the next major release.
        """
    def set_sync_log(self, sync_log: bool) -> None:
        """
        Deprecated! It is kept for backward compatibility.
        TODO: remove it in the next major release.
        """
    def clear_sync_log(self) -> None:
        """
        Deprecated! It is kept for backward compatibility.
        TODO: remove it in the next major release.
        """

class Entry(__API_Entry):
    """
    The entry is a type of change that needs to be applied. It contains two data fields.
    While the fields are built into the model; their usage is determined by the entry_type.

    For normal entries, the data field should contain the data change that should be applied.
    The context field can be used for any contextual data that might be relevant to the
    application of the data.

    For configuration changes, the data will contain the ConfChange message and the
    context will provide anything needed to assist the configuration change. The context
    if for the user to set and use in this case.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "EntryRef": ...
    @staticmethod
    def default() -> "Entry": ...
    @staticmethod
    def decode(v: bytes) -> "Entry": ...

class EntryRef(__API_Entry):
    """
    Reference type of :class:`Entry`.
    """

class __API_ConfState(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "ConfState": ...
    def get_auto_leave(self) -> bool:
        """ """
    def set_auto_leave(self, auto_leave: bool) -> None:
        """ """
    def clear_auto_leave(self) -> None:
        """ """
    def get_learners(self) -> List[int]:
        """ """
    def set_learners(self, learners: List[int]) -> None:
        """ """
    def clear_learners(self) -> None:
        """ """
    def get_learners_next(self) -> List[int]:
        """ """
    def set_learners_next(self, learners_next: List[int]) -> None:
        """ """
    def clear_learners_next(self) -> None:
        """ """
    def get_voters(self) -> List[int]:
        """ """
    def set_voters(self, voters: List[int]) -> None:
        """ """
    def clear_voters(self) -> None:
        """ """
    def get_voters_outgoing(self) -> List[int]:
        """ """
    def set_voters_outgoing(self, voters_outgoing: List[int]) -> None:
        """ """
    def clear_voters_outgoing(self) -> None:
        """ """

class ConfState(__API_ConfState):
    """ """

    def __init__(
        self, voters: Optional[List[int]], learners: Optional[List[int]]
    ) -> None: ...
    def make_ref(self) -> "ConfStateRef": ...
    @staticmethod
    def default() -> "ConfState": ...
    @staticmethod
    def decode(v: bytes) -> "ConfState": ...

class ConfStateRef(__API_ConfState):
    """
    Reference type of :class:`ConfState`.
    """

class __API_ConfChangeV2(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "ConfChangeV2": ...
    def get_changes(self) -> List["ConfChangeSingleRef"]:
        """ """
    def set_changes(
        self, changes: List["ConfChangeSingle"] | List["ConfChangeSingleRef"]
    ) -> None:
        """ """
    def clear_changes(self) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_transition(self) -> "ConfChangeTransition":
        """ """
    def set_transition(self, transition: "ConfChangeTransition") -> None:
        """ """
    def clear_transition(self) -> None:
        """ """
    def enter_joint(self) -> Optional[bool]:
        """
        Checks if uses Joint Consensus.

        It will return Some if and only if this config change will use Joint Consensus,
        which is the case if it contains more than one change or if the use of Joint
        Consensus was requested explicitly. The bool indicates whether the Joint State
        will be left automatically.
        """
    def merge_from_bytes(self, b: bytes) -> None:
        """
        Update this message object with fields read from given stream.
        """
    def leave_joint(self) -> bool:
        """
        Checks if the configuration change leaves a joint configuration.

        This is the case if the ConfChangeV2 is zero, with the possible exception of
        the Context field.
        """
    def as_v1(self) -> Optional["ConfChangeRef"]:
        """
        Converts conf change to `ConfChange`.

        `ConfChangeV2` can't be changed back to `ConfChange`.
        """
    def as_v2(self) -> "ConfChangeV2":
        """
        Gets conf change as `ConfChangeV2`.
        """
    def into_v2(self) -> "ConfChangeV2":
        """
        Converts conf change to `ConfChangeV2`.
        """

class ConfChangeV2(__API_ConfChangeV2):
    """
    ConfChangeV2 messages initiate configuration changes. They support both the
    simple "one at a time" membership change protocol and full Joint Consensus
    allowing for arbitrary changes in membership.

    The supplied context is treated as an opaque payload and can be used to
    attach an action on the state machine to the application of the config change
    proposal. Note that contrary to Joint Consensus as outlined in the Raft
    paper[1], configuration changes become active when they are *applied* to the
    state machine (not when they are appended to the log).

    The simple protocol can be used whenever only a single change is made.

    Non-simple changes require the use of Joint Consensus, for which two
    configuration changes are run. The first configuration change specifies the
    desired changes and transitions the Raft group into the joint configuration,
    in which quorum requires a majority of both the pre-changes and post-changes
    configuration. Joint Consensus avoids entering fragile intermediate
    configurations that could compromise survivability. For example, without the
    use of Joint Consensus and running across three availability zones with a
    replication factor of three, it is not possible to replace a voter without
    entering an intermediate configuration that does not survive the outage of
    one availability zone.

    The provided ConfChangeTransition specifies how (and whether) Joint Consensus
    is used, and assigns the task of leaving the joint configuration either to
    Raft or the application. Leaving the joint configuration is accomplished by
    proposing a ConfChangeV2 with only and optionally the Context field
    populated.

    For details on Raft membership changes, see:

    [1]: https://github.com/ongardie/dissertation/blob/master/online-trim.pdf
    """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> "ConfChangeV2": ...
    def make_ref(self) -> "ConfChangeV2Ref": ...
    @staticmethod
    def decode(v: bytes) -> "ConfChangeV2": ...

class ConfChangeV2Ref(__API_ConfChangeV2):
    """
    Reference type of :class:`ConfChangeV2`.
    """

class __API_ConfChangeSingle(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "ConfChangeSingle": ...
    def get_node_id(self) -> int:
        """ """
    def set_node_id(self, node_id: int):
        """ """
    def clear_node_id(self) -> None:
        """ """
    def get_change_type(self) -> "ConfChangeType":
        """ """
    def set_change_type(self, typ: "ConfChangeType") -> None:
        """ """
    def clear_change_type(self) -> None:
        """ """

class ConfChangeSingle(__API_ConfChangeSingle):
    """
    ConfChangeSingle is an individual configuration change operation. Multiple
    such operations can be carried out atomically via a ConfChangeV2.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "ConfChangeSingleRef": ...
    @staticmethod
    def default() -> "ConfChangeSingle": ...
    @staticmethod
    def decode(v: bytes) -> "ConfChangeSingle": ...

class ConfChangeSingleRef(__API_ConfChangeSingle):
    """
    Reference type of :class:`ConfChangeSingle`.
    """

class __API_ConfChange(__Cloneable, __Encoder, __Decoder):
    def clone(self) -> "ConfChange": ...
    def get_id(self) -> int:
        """ """
    def set_id(self, id: int) -> None:
        """ """
    def clear_id(self) -> None:
        """ """
    def get_node_id(self) -> int:
        """ """
    def set_node_id(self, node_id: int) -> None:
        """ """
    def clear_node_id(self) -> None:
        """ """
    def get_change_type(self) -> "ConfChangeType":
        """ """
    def set_change_type(self, typ: "ConfChangeType") -> None:
        """ """
    def clear_change_type(self) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def merge_from_bytes(self, b: bytes) -> None:
        """
        Update this message object with fields read from given stream.
        """
    def as_v1(self) -> Optional["ConfChangeRef"]:
        """
        Converts conf change to `ConfChange`.

        `ConfChangeV2` can't be changed back to `ConfChange`.
        """
    def as_v2(self) -> "ConfChangeV2":
        """
        Gets conf change as `ConfChangeV2`.
        """
    def into_v2(self) -> "ConfChangeV2":
        """
        Converts conf change to `ConfChangeV2`.
        """

class ConfChange(__API_ConfChange):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> "ConfChangeRef": ...
    @staticmethod
    def default() -> "ConfChange": ...
    @staticmethod
    def decode(v: bytes) -> "ConfChange": ...

class ConfChangeRef(__API_ConfChange):
    """
    Reference type of :class:`ConfChange`.
    """

class __API_Unstable:
    def maybe_first_index(self) -> Optional[int]:
        """
        Returns the index of the first possible entry in entries
        if it has a snapshot.
        """
    def maybe_last_index(self) -> Optional[int]:
        """
        Returns the last index if it has at least one unstable entry or snapshot.
        """
    def maybe_term(self) -> Optional[int]:
        """
        Returns the term of the entry at index idx, if there is any.
        """
    def must_check_outofbounds(self, lo: int, hi: int) -> None:
        """
        Asserts the `hi` and `lo` values against each other and against the
        entries themselves.
        """
    def slice(self, lo: int, hi: int) -> List["EntryRef"]:
        """
        Returns a slice of entries between the high and low.

        # Panics

        Panics if the `lo` or `hi` are out of bounds.
        Panics if `lo > hi`.
        """
    def stable_snap(self, index: int) -> None:
        """
        Clears the unstable snapshot.
        """
    def stable_entries(self, index: int, term: int) -> None:
        """
        Clears the unstable entries and moves the stable offset up to the
        last index, if there is any.
        """
    def restore(self, snap: "SnapshotRef") -> None:
        """
        From a given snapshot, restores the snapshot to self, but doesn't unpack.
        """
    def truncate_and_append(self, ents: List["Entry"] | List["EntryRef"]) -> None:
        """
        Append entries to unstable, truncate local block first if overlapped.

        # Panics

        Panics if truncate logs to the entry before snapshot
        """
    def get_entries_size(self) -> int:
        """
        `entries_size`: The size of entries
        """
    def set_entries_size(self, entries_size: int) -> None:
        """
        `entries_size`: The size of entries
        """
    def get_offset(self) -> int:
        """
        `offset`: The offset from the vector index.
        """
    def set_offset(self, offset: int) -> None:
        """
        `offset`: The offset from the vector index.
        """
    def get_entries(self) -> List["EntryRef"]:
        """
        `entries`: All entries that have not yet been written to storage.
        """
    def set_entries(self, ents: List["Entry"] | List["EntryRef"]) -> None:
        """
        `entries`: All entries that have not yet been written to storage.
        """
    def get_logger(self) -> "LoggerRef":
        """
        `logger`: The tag to use when logging.
        """
    def set_logger(self, logger: "Logger" | "LoggerRef") -> None:
        """
        `logger`: The tag to use when logging.
        """
    def get_snapshot(self) -> Optional["SnapshotRef"]:
        """
        `snapshot`: The incoming unstable snapshot, if any.
        """
    def set_snapshot(self, snapshot: "Snapshot" | "SnapshotRef") -> None:
        """
        `snapshot`: The incoming unstable snapshot, if any.
        """

class Unstable(__API_Unstable):
    """
    The `unstable.entries[i]` has raft log position `i+unstable.offset`.
    Note that `unstable.offset` may be less than the highest log
    position in storage; this means that the next write to storage
    might need to truncate the log before persisting unstable.entries.
    """

    def __init__(self, offset: int, logger: "Logger" | "LoggerRef") -> None: ...
    def make_ref(self) -> "UnstableRef": ...

class UnstableRef(__API_Unstable):
    """
    Reference type of :class:`Unstable`.
    """

class __API_SoftState:
    def get_leader_id(self) -> int:
        """
        `leader_id`: The potential leader of the cluster.
        """
    def set_leader_id(self, leader_id: int) -> None:
        """
        `leader_id`: The potential leader of the cluster.
        """
    def get_raft_state(self) -> "StateRole":
        """
        `raft_state`: The soft role this node may take.
        """
    def set_raft_state(self, role: "StateRole") -> None:
        """
        `raft_state`: The soft role this node may take.
        """

class SoftState(__API_SoftState):
    """
    SoftState provides state that is useful for logging and debugging.
    The state is volatile and does not need to be persisted to the WAL.
    """

    def make_ref(self) -> "SoftStateRef": ...
    @staticmethod
    def default() -> "SoftState": ...

class SoftStateRef(__API_SoftState):
    """
    Reference type of :class:`SoftState`.
    """

class __API_ReadState(__Cloneable):
    def clone(self) -> "ReadState": ...
    def get_index(self) -> int:
        """
        `index`: The index of the read state.
        """
    def set_index(self, idx: int) -> None:
        """
        `index`: The index of the read state.
        """
    def get_request_ctx(self) -> bytes:
        """
        `request_ctx`: A datagram consisting of context about the request.
        """
    def set_request_ctx(self, request_ctx: bytes) -> None:
        """
        `request_ctx`: A datagram consisting of context about the request.
        """

class ReadState(__API_ReadState):
    """
    ReadState provides state for read only query.
    It's caller's responsibility to send MsgReadIndex first before getting
    this state from ready. It's also caller's duty to differentiate if this
    state is what it requests through request_ctx, e.g. given a unique id as
    request_ctx.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> "ReadStateRef": ...

class ReadStateRef(__API_ReadState):
    """
    Reference type of :class:`ReadState`.
    """

class __API_RaftLog:
    def entries(
        self, idx: int, context: "GetEntriesContextRef", max_size: Optional[int]
    ) -> List["Entry"]:
        """
        Returns entries starting from a particular index and not exceeding a bytesize.
        """
    def all_entries(self) -> List["Entry"]:
        """
        Returns all the entries. Only used by tests.
        """
    def append(self, ents: List["Entry"] | List["EntryRef"]) -> int:
        """
        Appends a set of entries to the unstable list.
        """
    def applied(self) -> int:
        """
        Returns the last applied index.
        """
    def find_conflict(self, ents: List["Entry"] | List["EntryRef"]) -> int:
        """
        Finds the index of the conflict.

        It returns the first index of conflicting entries between the existing
        entries and the given entries, if there are any.

        If there are no conflicting entries, and the existing entries contain
        all the given entries, zero will be returned.

        If there are no conflicting entries, but the given entries contains new
        entries, the index of the first new entry will be returned.

        An entry is considered to be conflicting if it has the same index but
        a different term.

        The first entry MUST have an index equal to the argument 'from'.
        The index of the given entries MUST be continuously increasing.
        """
    def find_conflict_by_term(self, index: int, term: int) -> Tuple[int, Optional[int]]:
        """
        find_conflict_by_term takes an (`index`, `term`) pair (indicating a conflicting log
        entry on a leader/follower during an append) and finds the largest index in
        log with log.term <= `term` and log.index <= `index`. If no such index exists
        in the log, the log's first index is returned.

        The index provided MUST be equal to or less than self.last_index(). Invalid
        inputs log a warning and the input index is returned.

        Return (index, term)
        """
    def commit_to(self, to_commit: int) -> None:
        """
        Sets the last committed value to the passed in value.

        # Panics

        Panics if the index goes past the last index.
        """
    def commit_info(self) -> Tuple[int, int]:
        """
        Returns the committed index and its term.
        """
    def store(self) -> "MemStorageRef":
        """ """
    def next_entries(self, max_size: Optional[int]) -> Optional[List["Entry"]]:
        """
        Returns all the available entries for execution.
        If applied is smaller than the index of snapshot, it returns all committed
        entries after the index of snapshot.
        """
    def next_entries_since(
        self, since_idx: int, max_size: Optional[int]
    ) -> Optional[List["Entry"]]:
        """
        Returns committed and persisted entries since max(`since_idx` + 1, first_index).
        """
    def has_next_entries(self) -> bool:
        """
        Returns whether there are new entries.
        """
    def has_next_entries_since(self, since_idx: int) -> bool:
        """
        Returns whether there are committed and persisted entries since
        max(`since_idx` + 1, first_index).
        """
    def is_up_to_date(self, last_index: int, term: int) -> bool:
        """
        Determines if the given (lastIndex,term) log is more up-to-date
        by comparing the index and term of the last entry in the existing logs.
        If the logs have last entry with different terms, then the log with the
        later term is more up-to-date. If the logs end with the same term, then
        whichever log has the larger last_index is more up-to-date. If the logs are
        the same, the given log is up-to-date.
        """
    def maybe_commit(self, max_index: int, term: int) -> bool:
        """
        Attempts to commit the index and term and returns whether it did.
        """
    def maybe_persist(self, index: int, term: int) -> bool:
        """
        Attempts to persist the index and term and returns whether it did.
        """
    def maybe_persist_snap(self, index: int) -> bool:
        """
        Attempts to persist the snapshot and returns whether it did.
        """
    def maybe_append(
        self,
        idx: int,
        term: int,
        committed: int,
        ents: List["Entry"] | List["EntryRef"],
    ) -> Optional[Tuple[int, int]]:
        """
        Returns None if the entries cannot be appended. Otherwise,
        it returns Some((conflict_index, last_index)).

        # Panics

        Panics if it finds a conflicting index less than committed index.
        """
    def snapshot(self, request_index: int, to: int) -> "SnapshotRef":
        """
        Returns the current snapshot
        """
    def stable_entries(self, index: int, term: int) -> None:
        """
        Clears the unstable entries and moves the stable offset up to the
        last index, if there is any.
        """
    def stable_snap(self, index: int) -> None:
        """
        Clears the unstable snapshot.
        """
    def term(self, idx: int) -> int:
        """
        For a given index, finds the term associated with it.
        """
    def last_term(self) -> int:
        """
        Grabs the term from the last entry.

        # Panics

        Panics if there are entries but the last term has been discarded.
        """
    def match_term(self, idx: int, term: int) -> bool:
        """
        Answers the question: Does this index belong to this term?
        """
    def first_index(self) -> int:
        """
        Returns th first index in the store that is available via entries

        # Panics

        Panics if the store doesn't have a first index.
        """
    def last_index(self) -> int:
        """
        Returns the last index in the store that is available via entries.

        # Panics

        Panics if the store doesn't have a last index.
        """
    def unstable(self) -> "UnstableRef":
        """
        Returns a reference to the unstable log.
        """
    def unstable_entries(self) -> List["EntryRef"]:
        """
        Returns slice of entries that are not persisted.
        """
    def unstable_snapshot(self) -> Optional["SnapshotRef"]:
        """
        Returns the snapshot that are not persisted.
        """
    def get_applied(self) -> int:
        """
        `applied`: The highest log position that the application has been instructed
        to apply to its state machine.

        Invariant: applied <= min(committed, persisted)
        """
    def set_applied(self, applied: int) -> None:
        """
        `applied`: The highest log position that the application has been instructed
        to apply to its state machine.

        Invariant: applied <= min(committed, persisted)
        """
    def get_committed(self) -> int:
        """
        `committed`: The highest log position that is known to be in stable storage
        on a quorum of nodes.

        Invariant: applied <= committed
        """
    def set_committed(self, committed: int) -> None:
        """
        `committed`: The highest log position that is known to be in stable storage
        on a quorum of nodes.

        Invariant: applied <= committed
        """
    def get_persisted(self) -> int:
        """
        `persisted`: The highest log position that is known to be persisted in stable
        storage. It's used for limiting the upper bound of committed and
        persisted entries.

        Invariant: persisted < unstable.offset && applied <= persisted
        """
    def set_persisted(self, persisted: int) -> None:
        """
        `persisted`: The highest log position that is known to be persisted in stable
        storage. It's used for limiting the upper bound of committed and
        persisted entries.

        Invariant: persisted < unstable.offset && applied <= persisted
        """
    def slice(
        self,
        low: int,
        high: int,
        max_size: Optional[int],
        context: "GetEntriesContextRef",
    ) -> List["EntryRef"]:
        """
        Grabs a slice of entries from the raft. Unlike a rust slice pointer, these are
        returned by value. The result is truncated to the max_size in bytes.
        """
    def restore(self, snapshot: "Snapshot" | "SnapshotRef") -> None:
        """
        Restores the current log from a snapshot.
        """

class InMemoryRaftLog(__API_RaftLog):
    """
    Raft log implementation
    """

    def __init__(
        self, store: "MemStorageRef", logger: "Logger" | "LoggerRef"
    ) -> None: ...
    def make_ref(self) -> "InMemoryRaftLogRef": ...
    def get_store(self) -> "MemStorageRef":
        """
        Grab a read-only reference to the underlying storage.
        """

class InMemoryRaftLogRef(__API_RaftLog):
    """
    Reference type of :class:`InMemoryRaftLog`.
    """

    def get_store(self) -> "MemStorageRef":
        """
        Grab a read-only reference to the underlying storage.
        """

class RaftLog(__API_RaftLog):
    """ """

    def __init__(self, store: "StorageRef", logger: "Logger" | "LoggerRef") -> None: ...
    def make_ref(self) -> "RaftLogRef": ...
    def get_store(self) -> "StorageRef":
        """
        Grab a read-only reference to the underlying storage.
        """

class RaftLogRef(__API_RaftLog):
    """
    Reference type of :class:`RaftLog`.
    """

    def get_store(self) -> "StorageRef":
        """
        Grab a read-only reference to the underlying storage.
        """

class __API_Raft:
    def append_entry(self, ents: List["Entry"] | List["EntryRef"]) -> bool:
        """
        Appends a slice of entries to the log.
        The entries are updated to match the current index and term.
        Only called by leader currently
        """
    def send_append(self, to: int) -> None:
        """
        Sends an append RPC with new entries (if any) and the current commit index to the given
        peer.
        """
    def on_persist_entries(self, index: int, term: int) -> None:
        """
        Notifies that these raft logs have been persisted.
        """
    def apply_to_current_term(self) -> bool:
        """
        Checks if logs are applied to current term.
        """
    def commit_to_current_term(self) -> bool:
        """
        Checks if logs are committed to its term.

        The check is useful usually when raft is leader.
        """
    def group_commit(self) -> bool:
        """
        Whether enable group commit.
        """
    def enable_group_commit(self, enable: bool) -> None:
        """
        Configures group commit.

        If group commit is enabled, only logs replicated to at least two
        different groups are committed.

        You should use `assign_commit_groups` to configure peer groups.
        """
    def clear_commit_group(self) -> None:
        """
        Removes all commit group configurations.
        """
    def check_group_commit_consistent(self) -> Optional[bool]:
        """
        Checks whether the raft group is using group commit and consistent
        over group.

        If it can't get a correct answer, `None` is returned.
        """
    def assign_commit_groups(self, ids: List[Tuple[int, int]]) -> None:
        """
        Assigns groups to peers.

        The tuple is (`peer_id`, `group_id`). `group_id` should be larger than 0.

        The group information is only stored in memory. So you need to configure
        it every time a raft state machine is initialized or a snapshot is applied.
        """
    def commit_apply(self, applied: int) -> None:
        """
        Commit that the Raft peer has applied up to the given index.

        Registers the new applied index to the Raft log.

        # Hooks

        * Post: Checks to see if it's time to finalize a Joint Consensus state.
        """
    def maybe_commit(self) -> bool:
        """
        Attempts to advance the commit index. Returns true if the commit index
        changed (in which case the caller should call `r.bcast_append`).
        """
    def uncommitted_size(self) -> int:
        """
        Return current uncommitted size recorded by uncommitted_state
        """
    def maybe_increase_uncommitted_size(
        self, ents: List["Entry"] | List["EntryRef"]
    ) -> bool:
        """
        Increase size of 'ents' to uncommitted size. Return true when size limit
        is satisfied. Otherwise return false and uncommitted size remains unchanged.
        For raft with no limit(or non-leader raft), it always return true.
        """
    def reduce_uncommitted_size(self, ents: List["Entry"] | List["EntryRef"]) -> None:
        """
        Reduce size of 'ents' from uncommitted size.
        """
    def bcast_append(self) -> None:
        """
        Sends RPC, with entries to all peers that are not up-to-date
        according to the progress recorded in r.prs().
        """
    def bcast_heartbeat(self) -> None:
        """
        Sends RPC, without entries to all the peers.
        """
    def should_bcast_commit(self) -> bool:
        """
        Specifies if the commit should be broadcast.
        """
    def skip_bcast_commit(self, skip: bool) -> None:
        """
        Set whether skip broadcast empty commit messages at runtime.
        """
    def become_leader(self) -> None:
        """
        Makes this raft the leader.

        # Panics

        Panics if this is a follower node.
        """
    def become_follower(self, term: int, leader_id: int) -> None:
        """
        Converts this node to a follower.
        """
    def become_pre_candidate(self) -> None:
        """
        Converts this node to a pre-candidate

        # Panics

        Panics if a leader already exists.
        """
    def become_candidate(self) -> None:
        """
        Converts this node to a candidate

        # Panics

        Panics if a leader already exists.
        """
    def heartbeat_timeout(self) -> int:
        """
        Fetch the length of the heartbeat timeout
        """
    def heartbeat_elapsed(self) -> int:
        """
        Fetch the number of ticks elapsed since last heartbeat.
        """
    def election_timeout(self) -> int:
        """
        Fetch the length of the election timeout.
        """
    def randomized_election_timeout(self) -> int:
        """
        Return the length of the current randomized election timeout.
        """
    def set_randomized_election_timeout(self, randomized_election_timeout: int) -> None:
        """
        For testing leader lease
        """
    def reset_randomized_election_timeout(self) -> None:
        """
        Regenerates and stores the election timeout.
        """
    def pass_election_timeout(self) -> bool:
        """
        `pass_election_timeout` returns true if `election_elapsed` is greater
        than or equal to the randomized election timeout in
        [`election_timeout`, 2 * `election_timeout` - 1].
        """
    def send_timeout_now(self, to: int) -> None:
        """
        Issues a message to timeout immediately.
        """
    def ready_read_count(self) -> int:
        """
        Returns how many read states exist.
        """
    def pending_read_count(self) -> int:
        """
        Returns the number of pending read-only messages.
        """
    def load_state(self, hs: "HardState" | "HardStateRef") -> None:
        """
        For a given hardstate, load the state into self.
        """
    def soft_state(self) -> "SoftState":
        """
        Returns a value representing the softstate at the time of calling.
        """
    def hard_state(self) -> "HardState":
        """
        Returns a value representing the hardstate at the time of calling.
        """
    def ping(self) -> None:
        """
        Broadcasts heartbeats to all the followers if it's leader.
        """
    def tick(self) -> bool:
        """
        Returns true to indicate that there will probably be some readiness need to be handled.
        """
    def tick_election(self) -> bool:
        """
        Run by followers and candidates after self.election_timeout.

        Returns true to indicate that there will probably be some readiness need to be handled.
        """
    def step(self, msg: "Message" | "MessageRef") -> None:
        """
        Steps the raft along via a message. This should be called everytime your raft receives a
        message from a peer.
        """
    def has_pending_conf(self) -> bool:
        """
        Check if there is any pending confchange.

        This method can be false positive.
        """
    def promotable(self) -> bool:
        """
        Indicates whether state machine can be promoted to leader,
        which is true when it's a voter and its own id is in progress list.
        """
    def post_conf_change(self) -> "ConfStateRef":
        """
        Updates the in-memory state and, when necessary, carries out additional actions
        such as reacting to the removal of nodes or changed quorum requirements.
        """
    def in_lease(self) -> bool:
        """
        Returns whether the current raft is in lease.
        """
    def handle_heartbeat(self, msg: "Message" | "MessageRef") -> None:
        """For a message, commit and send out heartbeat."""
    def handle_append_entries(self, msg: "Message" | "MessageRef") -> None:
        """For a given message, append the entries to the log."""
    def request_snapshot(self) -> None:
        """
        Request a snapshot from a leader.
        """
    def prs(self) -> "ProgressTrackerRef":
        """
        Returns a read-only reference to the progress set.
        """
    def reset(self, term: int) -> None:
        """
        Resets the current node to a given term.
        """
    def restore(self, snapshot: "Snapshot" | "SnapshotRef") -> bool:
        """
        Recovers the state machine from a snapshot. It restores the log and the
        configuration of state machine.
        """
    def snap(self) -> Optional["SnapshotRef"]:
        """
        Grabs a reference to the snapshot
        """
    def store(self) -> "MemStorageRef":
        """
        Grabs an immutable reference to the store.
        """
    def on_persist_snap(self, index: int) -> None:
        """
        Notifies that the snapshot have been persisted.
        """
    def abort_leader_transfer(self) -> None:
        """
        Stops the transfer of a leader.
        """
    def campaign(self, typ: str) -> None:
        """
        Campaign to attempt to become a leader.

        If prevote is enabled, this is handled as well.
        """
    def get_lead_transferee(self) -> Optional[int]:
        """
        `lead_transferee`: ID of the leader transfer target when its value is not None.

        If this is Some(id), we follow the procedure defined in raft thesis 3.10.
        """
    def set_lead_transferee(self, lead_transferee: int) -> None:
        """
        `lead_transferee`: ID of the leader transfer target when its value is not None.

        If this is Some(id), we follow the procedure defined in raft thesis 3.10.
        """
    def get_term(self) -> int:
        """
        `term`: The current election term.
        """
    def set_term(self, term: int) -> None:
        """
        `term`: The current election term.
        """
    def get_vote(self) -> int:
        """
        `vote`: Which peer this raft is voting for.
        """
    def set_vote(self, vote: int) -> None:
        """
        `vote`: Which peer this raft is voting for.
        """
    def get_priority(self) -> int:
        """
        `priority`: The election priority of this node.
        """
    def set_priority(self, priority: int) -> None:
        """
        `priority`: The election priority of this node.
        """
    def get_leader_id(self) -> int:
        """
        `leader_id`: The leader id
        """
    def set_leader_id(self, leader_id: int) -> None:
        """
        `leader_id`: The leader id
        """
    def get_max_msg_size(self) -> int:
        """
        `max_msg_size`: The maximum length (in bytes) of all the entries.
        """
    def set_max_msg_size(self, max_msg_size: int) -> None:
        """
        `max_msg_size`: The maximum length (in bytes) of all the entries.
        """
    def get_pending_conf_index(self) -> int:
        """
        `pending_conf_index`: Only one conf change may be pending (in the log, but not yet
        applied) at a time. This is enforced via `pending_conf_index`, which
        is set to a value >= the log index of the latest pending
        configuration change (if any). Config changes are only allowed to
        be proposed if the leader's applied index is greater than this
        value.

        This value is conservatively set in cases where there may be a configuration change pending,
        but scanning the log is possibly expensive. This implies that the index stated here may not
        necessarily be a config change entry, and it may not be a `BeginMembershipChange` entry, even if
        we set this to one.
        """
    def set_pending_conf_index(self, pending_conf_index: int) -> None:
        """
        `pending_conf_index`: Only one conf change may be pending (in the log, but not yet
        applied) at a time. This is enforced via `pending_conf_index`, which
        is set to a value >= the log index of the latest pending
        configuration change (if any). Config changes are only allowed to
        be proposed if the leader's applied index is greater than this
        value.

        This value is conservatively set in cases where there may be a configuration change pending,
        but scanning the log is possibly expensive. This implies that the index stated here may not
        necessarily be a config change entry, and it may not be a `BeginMembershipChange` entry, even if
        we set this to one.
        """
    def get_pending_request_snapshot(self) -> int:
        """
        `pending_request_snapshot`: The peer is requesting snapshot, it is the index that the follower
        needs it to be included in a snapshot.
        """
    def set_pending_request_snapshot(self, pending_request_snapshot: int) -> None:
        """
        `pending_request_snapshot`: The peer is requesting snapshot, it is the index that the follower
        needs it to be included in a snapshot.
        """
    def get_id(self) -> int:
        """
        `id`: The ID of this node.
        """
    def set_id(self, id: int) -> None:
        """
        `id`: The ID of this node.
        """
    def get_msgs(self) -> List["MessageRef"]:
        """
        `msgs`: The list of messages.
        """
    def set_msgs(self, msgs: List["Message" | "MessageRef"]) -> None:
        """
        `msgs`: The list of messages.
        """
    def take_msgs(self) -> List["Message"]:
        """
        `msgs`: The list of messages.
        """
    def get_max_inflight(self) -> int:
        """
        `max_inflight`: The maximum number of messages that can be inflight.
        """
    def set_max_inflight(self, max_inflight: int) -> None:
        """
        `max_inflight`: The maximum number of messages that can be inflight.
        """
    def get_state(self) -> "StateRole":
        """
        `state`: The current role of this node.
        """
    def set_state(self, state_role: "StateRole") -> None:
        """
        `state`: The current role of this node.
        """
    def get_election_elapsed(self) -> int:
        """
        `election_elapsed`: Ticks since it reached last electionTimeout when it is leader or candidate.
        Number of ticks since it reached last electionTimeout or received a
        valid message from current leader when it is a follower.
        """
    def set_election_elapsed(self, election_elapsed: int) -> None:
        """
        `election_elapsed`: Ticks since it reached last electionTimeout when it is leader or candidate.
        Number of ticks since it reached last electionTimeout or received a
        valid message from current leader when it is a follower.
        """
    def get_check_quorum(self) -> bool:
        """
        `check_quorum`: Whether to check the quorum
        """
    def set_check_quorum(self, check_quorum: bool) -> None:
        """
        `check_quorum`: Whether to check the quorum
        """
    def get_pre_vote(self) -> bool:
        """
        `pre_vote`: Enable the prevote algorithm.

        This enables a pre-election vote round on Candidates prior to disrupting the cluster.

        Enable this if greater cluster stability is preferred over faster elections.
        """
    def set_pre_vote(self, pre_vote: bool) -> None:
        """
        `pre_vote`: Enable the prevote algorithm.

        This enables a pre-election vote round on Candidates prior to disrupting the cluster.

        Enable this if greater cluster stability is preferred over faster elections.
        """
    def apply_conf_change(self, conf_change: "ConfChangeV2Ref") -> "ConfChangeRef":
        """ """
    def get_read_states(self) -> List["ReadState"]:
        """
        `read_states`: The current read states.
        """
    def set_read_states(
        self, read_states: List["ReadState"] | List["ReadStateRef"]
    ) -> None:
        """
        `read_states`: The current read states.
        """
    def get_read_only_option(self) -> "ReadOnlyOption":
        """
        `read_only_option`: Choose the linearizability mode or the lease mode to read data. If you don’t care about the read consistency and want a higher read performance, you can use the lease mode.
        Setting this to `LeaseBased` requires `check_quorum = true`.
        """
    def set_read_only_option(self, option: "ReadOnlyOption") -> None:
        """
        `read_only_option`: Choose the linearizability mode or the lease mode to read data. If you don’t care about the read consistency and want a higher read performance, you can use the lease mode.
        Setting this to `LeaseBased` requires `check_quorum = true`.
        """
    def inflight_buffers_size(self) -> int:
        """Get the inflight buffer size."""
    def maybe_free_inflight_buffers(self) -> None:
        """
        A Raft leader allocates a vector with capacity `max_inflight_msgs` for every peer.
        It takes a lot of memory if there are too many Raft groups. `maybe_free_inflight_buffers`
        is used to free memory if necessary.
        """
    def adjust_max_inflight_msgs(self, target: int, cap: int) -> None:
        """
        To adjust `max_inflight_msgs` for the specified peer.
        Set to `0` will disable the progress.
        """
    def get_readonly_read_index_queue(self) -> List[List[int]]:
        """ """
    def set_batch_append(self, batch_append: bool) -> None:
        """
        Set whether batch append msg at runtime.
        """
    def set_max_committed_size_per_ready(self, size: int) -> None:
        """
        Set `max_committed_size_per_ready` to `size`.
        """

class InMemoryRaft(__API_Raft):
    """
    A struct that represents the raft consensus itself. Stores details concerning the current
    and possible state the system can take.
    """

    def __init__(
        self,
        cfg: "Config" | "ConfigRef",
        store: "MemStorage" | "MemStorageRef",
        logger: "Logger" | "LoggerRef",
    ) -> None: ...
    def make_ref(self) -> "InMemoryRaftRef": ...
    def get_raft_log(self) -> "InMemoryRaftLogRef":
        """ """

class InMemoryRaftRef(__API_Raft):
    """
    Reference type of :class:`InMemoryRaft`.
    """

    def get_raft_log(self) -> "InMemoryRaftLogRef":
        """ """

class Raft(__API_Raft):
    """
    A struct that represents the raft consensus itself. Stores details concerning the current
    and possible state the system can take.
    """

    def __init__(
        self,
        cfg: "Config" | "ConfigRef",
        store: "Storage" | "StorageRef",
        logger: "Logger" | "LoggerRef",
    ) -> None: ...
    def make_ref(self) -> "RaftRef": ...
    def get_raft_log(self) -> "RaftLogRef":
        """ """

class RaftRef(__API_Raft):
    """
    Reference type of :class:`Raft`.
    """

    def get_raft_log(self) -> "RaftLogRef":
        """ """

class ProgressMapItem:
    def id(self) -> int: ...
    def progress(self) -> "Progress": ...

class __API_ProgressTracker(__Cloneable):
    def clone(self) -> "ProgressTracker": ...
    def get(self, id: int) -> Optional["ProgressRef"]:
        """"""
    def group_commit(self) -> bool:
        """
        Whether enable group commit.
        """
    def enable_group_commit(self, enable: bool) -> None:
        """
        Configures group commit.
        """
    def has_quorum(self, potential_quorum: Set[int]) -> bool:
        """
        Determine if a quorum is formed from the given set of nodes.

        This is the only correct way to verify you have reached a quorum for the whole group.
        """
    def is_singleton(self) -> bool:
        """
        Returns true if (and only if) there is only one voting member
        (i.e. the leader) in the current configuration.
        """
    def quorum_recently_active(self, perspective_of: int) -> bool:
        """
        Determines if the current quorum is active according to the this raft node.
        Doing this will set the `recent_active` of each peer to false.

        This should only be called by the leader.
        """
    def maximal_committed_index(self) -> Tuple[int, bool]:
        """
        Returns the maximal committed index for the cluster. The bool flag indicates whether
        the index is computed by group commit algorithm successfully

        Eg. If the matched indexes are `[2,2,2,4,5]`, it will return `2`.
        If the matched indexes and groups are `[(1, 1), (2, 2), (3, 2)]`, it will return `1`.
        """
    def record_vote(self, id: int, vote: bool) -> None:
        """
        Records that the node with the given id voted for this Raft
        instance if v == true (and declined it otherwise).
        """
    def reset_votes(self) -> None:
        """
        Prepares for a new round of vote counting via recordVote.
        """
    def conf_voters(self) -> "JointConfigRef":
        """ """
    def conf_learners(self) -> Set[int]:
        """ """
    def collect(self) -> List["ProgressMapItem"]:
        """ """

class ProgressTracker(__API_ProgressTracker):
    """
    `ProgressTracker` contains several `Progress`es,
    which could be `Leader`, `Follower` and `Learner`.
    """

    def __init__(self, max_inflight: int) -> None: ...
    def make_ref(self) -> "ProgressTrackerRef": ...

class ProgressTrackerRef(__API_ProgressTracker):
    """
    Reference type of :class:`ProgressTracker`.
    """

class __API_Progress(__Cloneable):
    def clone(self) -> "Progress": ...
    def become_probe(self) -> None:
        """Changes the progress to a probe."""
    def become_replicate(self) -> None:
        """Changes the progress to a Replicate."""
    def become_snapshot(self, snapshot_idx: int) -> None:
        """Changes the progress to a snapshot."""
    def maybe_update(self, n: int) -> bool:
        """
        Returns false if the given n index comes from an outdated message.
        Otherwise it updates the progress and returns true.
        """
    def maybe_decr_to(
        self, rejected: int, match_hint: int, request_snapshot: int
    ) -> bool:
        """
        Returns false if the given index comes from an out of order message.
        Otherwise it decreases the progress next index to min(rejected, last)
        and returns true.
        """
    def snapshot_failure(self) -> None:
        """
        Sets the snapshot to failure.
        """
    def pause(self) -> None:
        """
        Pause progress.
        """
    def is_paused(self) -> bool:
        """
        Determine whether progress is paused.
        """
    def is_snapshot_caught_up(self) -> bool:
        """
        Returns true if Match is equal or higher than the pendingSnapshot.
        """
    def resume(self) -> None:
        """
        Resume progress
        """
    def update_state(self, last: int) -> None:
        """
        Update inflight msgs and next_idx
        """
    def update_committed(self, committed_index: int) -> None:
        """
        Update committed_index.
        """
    def optimistic_update(self, n: int) -> None:
        """
        Optimistically advance the index
        """
    def get_ins(self) -> "InflightsRef":
        """
        `ins`: Inflights is a sliding window for the inflight messages.
        When inflights is full, no more message should be sent.
        When a leader sends out a message, the index of the last
        entry should be added to inflights. The index MUST be added
        into inflights in order.
        When a leader receives a reply, the previous inflights should
        be freed by calling inflights.freeTo.
        """
    def set_ins(self, inflights: "Inflights" | "InflightsRef") -> None:
        """
        `ins`: Inflights is a sliding window for the inflight messages.
        When inflights is full, no more message should be sent.
        When a leader sends out a message, the index of the last
        entry should be added to inflights. The index MUST be added
        into inflights in order.
        When a leader receives a reply, the previous inflights should
        be freed by calling inflights.freeTo.
        """
    def get_commit_group_id(self) -> int:
        """
        `commit_group_id`: Only logs replicated to different group will be committed if any group is configured.
        """
    def set_commit_group_id(self, commit_group_id: int) -> None:
        """
        `commit_group_id`: Only logs replicated to different group will be committed if any group is configured.
        """
    def get_committed_index(self) -> int:
        """
        `committed_index`: Committed index in raft_log
        """
    def set_committed_index(self, committed_index: int) -> None:
        """
        `committed_index`: Committed index in raft_log
        """
    def get_matched(self) -> int:
        """
        `matched`: How much state is matched.
        """
    def set_matched(self, matched: int) -> None:
        """
        `matched`: How much state is matched.
        """
    def get_next_idx(self) -> int:
        """
        `next_idx`: The next index to apply
        """
    def set_next_idx(self, next_idx: int) -> None:
        """
        `next_idx`: The next index to apply
        """
    def get_pending_snapshot(self) -> int:
        """
        `pending_snapshot`: This field is used in ProgressStateSnapshot.
        If there is a pending snapshot, the pendingSnapshot will be set to the
        index of the snapshot. If pendingSnapshot is set, the replication process of
        this Progress will be paused. raft will not resend snapshot until the pending one
        is reported to be failed.
        """
    def set_pending_snapshot(self, pending_snapshot: int) -> None:
        """
        `pending_snapshot`: This field is used in ProgressStateSnapshot.
        If there is a pending snapshot, the pendingSnapshot will be set to the
        index of the snapshot. If pendingSnapshot is set, the replication process of
        this Progress will be paused. raft will not resend snapshot until the pending one
        is reported to be failed.
        """
    def get_pending_request_snapshot(self) -> int:
        """
        `pending_request_snapshot`: This field is used in request snapshot.
        If there is a pending request snapshot, this will be set to the request
        index of the snapshot.
        """
    def set_pending_request_snapshot(self, pending_request_snapshot: int) -> None:
        """
        `pending_request_snapshot`: This field is used in request snapshot.
        If there is a pending request snapshot, this will be set to the request
        index of the snapshot.
        """
    def get_recent_active(self) -> bool:
        """
        `recent_active`: This is true if the progress is recently active. Receiving any messages
        from the corresponding follower indicates the progress is active.
        RecentActive can be reset to false after an election timeout.
        """
    def set_recent_active(self, recent_active: bool) -> None:
        """
        `recent_active`: This is true if the progress is recently active. Receiving any messages
        from the corresponding follower indicates the progress is active.
        RecentActive can be reset to false after an election timeout.
        """
    def get_paused(self) -> bool:
        """
        `paused`: Paused is used in ProgressStateProbe.
        When Paused is true, raft should pause sending replication message to this peer.
        """
    def set_paused(self, paused: bool) -> None:
        """
        `paused`: Paused is used in ProgressStateProbe.
        When Paused is true, raft should pause sending replication message to this peer.
        """
    def get_state(self) -> "ProgressState":
        """
        `state`: When in ProgressStateProbe, leader sends at most one replication message
        per heartbeat interval. It also probes actual progress of the follower.

        When in ProgressStateReplicate, leader optimistically increases next
        to the latest entry sent after sending replication message. This is
        an optimized state for fast replicating log entries to the follower.

        When in ProgressStateSnapshot, leader should have sent out snapshot
        before and stop sending any replication message.
        """
    def set_state(self, state: "ProgressState") -> None:
        """
        `state`: When in ProgressStateProbe, leader sends at most one replication message
        per heartbeat interval. It also probes actual progress of the follower.

        When in ProgressStateReplicate, leader optimistically increases next
        to the latest entry sent after sending replication message. This is
        an optimized state for fast replicating log entries to the follower.

        When in ProgressStateSnapshot, leader should have sent out snapshot
        before and stop sending any replication message.
        """

class Progress(__API_Progress):
    """
    The progress of catching up from a restart.
    """

    def __init__(self, next_idx: int, ins_size: int) -> None: ...
    def make_ref(self) -> "ProgressRef": ...

class ProgressRef(__API_Progress):
    """
    Reference type of :class:`Progress`.
    """

class __API_JointConfig(__Cloneable):
    def clone(self) -> "JointConfig": ...
    def clear(self) -> None:
        """Clears all IDs."""
    def contains(self, id: int) -> bool:
        """Check if an id is a voter."""
    def ids() -> Set[int]:
        """Returns an iterator over two hash set without cloning."""
    def is_singleton(self) -> bool:
        """
        Returns true if (and only if) there is only one voting member
        (i.e. the leader) in the current configuration.
        """

class JointConfig(__API_JointConfig):
    """
    A configuration of two groups of (possibly overlapping) majority configurations.
    Decisions require the support of both majorities.
    """

    def __init__(self, voters: Set[int]) -> None: ...
    def make_ref(self) -> "JointConfigRef": ...

class JointConfigRef(__API_JointConfig):
    """
    Reference type of :class:`JointConfig`.
    """

class __API_MajorityConfig(__Cloneable):
    def clone(self) -> "MajorityConfig": ...
    def raw_slice(self) -> List[int]:
        """
        Returns the MajorityConfig as a slice.
        """
    def capacity(self) -> int:
        """"""
    def extend(self, other_set: Set[int]) -> None:
        """"""
    def get(self, index: int) -> Optional[int]:
        """"""
    def insert(self, value: int) -> bool:
        """"""
    def replace(self, value: int) -> int:
        """"""
    def is_disjoint(self, other: Set[int]) -> bool:
        """"""
    def is_superset(self, other: Set[int]) -> bool:
        """"""
    def is_subset(self, other: Set[int]) -> bool:
        """"""
    def reserve(self, additional: int) -> None:
        """"""
    def remove(self, value: int) -> bool:
        """"""
    def shrink_to(self, min_capacity: int) -> None:
        """"""
    def shrink_to_fit(self) -> None:
        """"""
    def try_reserve(self, additional: int) -> None:
        """"""

class MajorityConfig(__API_MajorityConfig):
    """
    A set of IDs that uses majority quorums to make decisions.
    """

    def __init__(self, voters: Set[int]) -> None: ...
    def make_ref(self) -> "MajorityConfigRef": ...

class MajorityConfigRef(__API_MajorityConfig):
    """
    Reference type of :class:`MajorityConfig`.
    """

class __API_Inflights(__Cloneable):
    def clone(self) -> "Inflights": ...
    def add(self, inflight: int) -> None:
        """Adds an inflight into inflights"""
    def full(self) -> bool:
        """Returns true if the inflights is full."""
    def reset(self) -> None:
        """Frees all inflights."""
    def free_to(self, to: int) -> None:
        """Frees the inflights smaller or equal to the given `to` flight."""
    def free_first_one(self) -> None:
        """Frees the first buffer entry."""
    def maybe_free_buffer(self) -> None:
        """Free unused memory"""
    def buffer_capacity(self) -> int:
        """Capacity of the internal buffer."""
    def buffer_is_allocated(self) -> bool:
        """Whether buffer is allocated or not. It's for tests."""
    def count(self) -> int:
        """Number of inflight messages. It's for tests."""
    def set_cap(self, incoming_cap: int) -> None:
        """
        Adjust inflight buffer capacity. Set it to `0` will disable the progress.
        Calling it between `self.full()` and `self.add()` can cause a panic.
        """

class Inflights(__API_Inflights):
    """
    A buffer of inflight messages.
    """

    def __init__(self, cap: int) -> None: ...
    def make_ref(self) -> "InflightsRef": ...

class InflightsRef(__API_Inflights):
    """
    Reference type of :class:`InflightsRef`.
    """

class __API_Config(__Cloneable):
    def clone(self) -> "Config": ...
    def min_election_tick(self) -> int:
        """
        `min_election_tick`: The minimum number of ticks before an election.
        """
    def set_min_election_tick(self, min_election_tick: int) -> None:
        """
        `min_election_tick`: The minimum number of ticks before an election.
        """
    def max_election_tick(self) -> int:
        """
        `max_election_tick`: The maximum number of ticks before an election.
        """
    def set_max_election_tick(self, max_election_tick: int) -> None:
        """
        `max_election_tick`: The maximum number of ticks before an election.
        """
    def get_read_only_option(self) -> "ReadOnlyOption":
        """
        `read_only_option`: Choose the linearizability mode or the lease mode to read data. If you don’t care about the read consistency and want a higher read performance, you can use the lease mode.
        Setting this to `LeaseBased` requires `check_quorum = true`.
        """
    def set_read_only_option(self, read_only_option: "ReadOnlyOption") -> None:
        """
        `read_only_option`: Choose the linearizability mode or the lease mode to read data. If you don’t care about the read consistency and want a higher read performance, you can use the lease mode.
        Setting this to `LeaseBased` requires `check_quorum = true`.
        """
    def get_id(self) -> int:
        """
        `id`: The identity of the local raft. It cannot be 0, and must be unique in the group.
        """
    def set_id(self, id: int) -> None:
        """
        `id`: The identity of the local raft. It cannot be 0, and must be unique in the group.
        """
    def get_election_tick(self) -> int:
        """
        `election_tick`: The number of node.tick invocations that must pass between
        elections. That is, if a follower does not receive any message from the
        leader of current term before ElectionTick has elapsed, it will become
        candidate and start an election. election_tick must be greater than
        HeartbeatTick. We suggest election_tick = 10 * HeartbeatTick to avoid
        unnecessary leader switching
        """
    def set_election_tick(self, election_tick: int) -> None:
        """
        `election_tick`: The number of node.tick invocations that must pass between
        elections. That is, if a follower does not receive any message from the
        leader of current term before ElectionTick has elapsed, it will become
        candidate and start an election. election_tick must be greater than
        HeartbeatTick. We suggest election_tick = 10 * HeartbeatTick to avoid
        unnecessary leader switching
        """
    def get_heartbeat_tick(self) -> int:
        """
        `heartbeat_tick`: HeartbeatTick is the number of node.tick invocations that must pass between
        heartbeats. That is, a leader sends heartbeat messages to maintain its
        leadership every heartbeat ticks.
        """
    def set_heartbeat_tick(self, heartbeat_tick: int) -> None:
        """
        `heartbeat_tick`: HeartbeatTick is the number of node.tick invocations that must pass between
        heartbeats. That is, a leader sends heartbeat messages to maintain its
        leadership every heartbeat ticks.
        """
    def get_max_size_per_msg(self) -> int:
        """
        `max_size_per_msg`: Limit the max size of each append message. Smaller value lowers
        the raft recovery cost(initial probing and message lost during normal operation).
        On the other side, it might affect the throughput during normal replication.
        Note: math.MaxUusize64 for unlimited, 0 for at most one entry per message.
        """
    def set_max_size_per_msg(self, max_size_per_msg: int) -> None:
        """
        `max_size_per_msg`: Limit the max size of each append message. Smaller value lowers
        the raft recovery cost(initial probing and message lost during normal operation).
        On the other side, it might affect the throughput during normal replication.
        Note: math.MaxUusize64 for unlimited, 0 for at most one entry per message.
        """
    def get_max_inflight_msgs(self) -> int:
        """
        `max_inflight_msgs`: Limit the max number of in-flight append messages during optimistic
        replication phase. The application transportation layer usually has its own sending
        buffer over TCP/UDP. Set to avoid overflowing that sending buffer.
        """
    def set_max_inflight_msgs(self, max_inflight_msgs: int) -> None:
        """
        `max_inflight_msgs`: Limit the max number of in-flight append messages during optimistic
        replication phase. The application transportation layer usually has its own sending
        buffer over TCP/UDP. Set to avoid overflowing that sending buffer.
        """
    def get_applied(self) -> int:
        """
        `applied`: Applied is the last applied index. It should only be set when restarting
        raft. raft will not return entries to the application smaller or equal to Applied.
        If Applied is unset when restarting, raft might return previous applied entries.
        This is a very application dependent configuration.
        """
    def set_applied(self, applied: int) -> None:
        """
        `applied`: Applied is the last applied index. It should only be set when restarting
        raft. raft will not return entries to the application smaller or equal to Applied.
        If Applied is unset when restarting, raft might return previous applied entries.
        This is a very application dependent configuration.
        """
    def get_check_quorum(self) -> bool:
        """
        `check_quorum`: Specify if the leader should check quorum activity. Leader steps down when
        quorum is not active for an electionTimeout.
        """
    def set_check_quorum(self, check_quorum: bool) -> None:
        """
        `check_quorum`: Specify if the leader should check quorum activity. Leader steps down when
        quorum is not active for an electionTimeout.
        """
    def get_pre_vote(self) -> bool:
        """
        `pre_vote`: Enables the Pre-Vote algorithm described in raft thesis section
        9.6. This prevents disruption when a node that has been partitioned away
        rejoins the cluster.
        """
    def set_pre_vote(self, pre_vote: bool) -> None:
        """
        `pre_vote`: Enables the Pre-Vote algorithm described in raft thesis section
        9.6. This prevents disruption when a node that has been partitioned away
        rejoins the cluster.
        """
    def get_batch_append(self) -> bool:
        """
        `batch_append`: Batches every append msg if any append msg already exists
        """
    def set_batch_append(self, batch_append: bool) -> None:
        """
        `batch_append`: Batches every append msg if any append msg already exists
        """
    def get_skip_bcast_commit(self) -> bool:
        """
        `skip_bcast_commit`: Don't broadcast an empty raft entry to notify follower to commit an entry.
        This may make follower wait a longer time to apply an entry. This configuration
        May affect proposal forwarding and follower read.
        """
    def set_skip_bcast_commit(self, skip_bcast_commit: bool) -> None:
        """
        `skip_bcast_commit`: Don't broadcast an empty raft entry to notify follower to commit an entry.
        This may make follower wait a longer time to apply an entry. This configuration
        May affect proposal forwarding and follower read.
        """
    def get_priority(self) -> int:
        """
        `priority`: The election priority of this node.
        """
    def set_priority(self, priority: int) -> None:
        """
        `priority`: The election priority of this node.
        """
    def get_max_uncommitted_size(self) -> int:
        """
        `max_uncommitted_size`: Specify maximum of uncommitted entry size.
        When this limit is reached, all proposals to append new log will be dropped
        """
    def set_max_uncommitted_size(self, max_uncommitted_size: int) -> None:
        """
        `max_uncommitted_size`: Specify maximum of uncommitted entry size.
        When this limit is reached, all proposals to append new log will be dropped
        """
    def get_max_committed_size_per_ready(self) -> int:
        """
        `max_committed_size_per_ready`: Max size for committed entries in a `Ready`.
        """
    def set_max_committed_size_per_ready(
        self, max_committed_size_per_ready: int
    ) -> None:
        """
        `max_committed_size_per_ready`: Max size for committed entries in a `Ready`.
        """
    def validate(self) -> None:
        """Runs validations against the config."""

class Config(__API_Config):
    """
    Config contains the parameters to start a raft.
    """

    def __init__(
        self,
        *,
        id: Optional[int] = None,
        election_tick: Optional[int] = None,
        heartbeat_tick: Optional[int] = None,
        applied: Optional[int] = None,
        max_size_per_msg: Optional[int] = None,
        max_inflight_msgs: Optional[int] = None,
        check_quorum: Optional[bool] = None,
        pre_vote: Optional[bool] = None,
        min_election_tick: Optional[int] = None,
        max_election_tick: Optional[int] = None,
        read_only_option: Optional["ReadOnlyOption"] = None,
        skip_bcast_commit: Optional[bool] = None,
        batch_append: Optional[bool] = None,
        priority: Optional[int] = None,
        max_uncommitted_size: Optional[int] = None,
        max_committed_size_per_ready: Optional[int] = None,
    ) -> None:
        """
        :param id: The identity of the local raft. It cannot be 0, and must be unique in the group.

        :param election_tick: The number of node.tick invocations that must pass between
        elections. That is, if a follower does not receive any message from the
        leader of current term before ElectionTick has elapsed, it will become
        candidate and start an election. election_tick must be greater than
        HeartbeatTick. We suggest election_tick = 10 * HeartbeatTick to avoid
        unnecessary leader switching

        :param heartbeat_tick: HeartbeatTick is the number of node.tick invocations that must pass between
        heartbeats. That is, a leader sends heartbeat messages to maintain its
        leadership every heartbeat ticks.

        :param applied: Applied is the last applied index. It should only be set when restarting
        raft. raft will not return entries to the application smaller or equal to Applied.
        If Applied is unset when restarting, raft might return previous applied entries.
        This is a very application dependent configuration.

        :param max_size_per_msg: Limit the max size of each append message. Smaller value lowers
        the raft recovery cost(initial probing and message lost during normal operation).
        On the other side, it might affect the throughput during normal replication.
        Note: math.MaxUusize64 for unlimited, 0 for at most one entry per message.

        :param max_inflight_msgs: Limit the max number of in-flight append messages during optimistic
        replication phase. The application transportation layer usually has its own sending
        buffer over TCP/UDP. Set to avoid overflowing that sending buffer.

        :param check_quorum: Specify if the leader should check quorum activity. Leader steps down when
        quorum is not active for an electionTimeout.

        :param pre_vote: Enables the Pre-Vote algorithm described in raft thesis section
        9.6. This prevents disruption when a node that has been partitioned away
        rejoins the cluster.

        :param min_election_tick: The range of election timeout. In some cases, we hope some nodes has less possibility
        to become leader. This configuration ensures that the randomized election_timeout
        will always be suit in [min_election_tick, max_election_tick).
        If it is 0, then election_tick will be chosen.

        :param max_election_tick: If it is 0, then 2 * election_tick will be chosen.

        :param read_only_option: Choose the linearizability mode or the lease mode to read data. If you don’t care about the read consistency and want a higher read performance, you can use the lease mode.
        Setting this to `LeaseBased` requires `check_quorum = true`.

        :param skip_bcast_commit: Don't broadcast an empty raft entry to notify follower to commit an entry.
        This may make follower wait a longer time to apply an entry. This configuration
        May affect proposal forwarding and follower read.

        :param batch_append: Batches every append msg if any append msg already exists

        :param priority: The election priority of this node.

        :param max_uncommitted_size: Specify maximum of uncommitted entry size.
        When this limit is reached, all proposals to append new log will be dropped

        :param max_committed_size_per_ready: Max size for committed entries in a `Ready`.
        """
    def make_ref(self) -> "ConfigRef": ...
    @staticmethod
    def default() -> "Config": ...

class ConfigRef(__API_Config):
    """
    Reference type of :class:`InflightsRef`.
    """

# TODO: Add below implementation if needed, otherwise remove below codes.
# class __API_Status:
#     def get_applied(self) -> int:
#         """ """
#     def set_applied(self, applied: int) -> None:
#         """ """
#     def get_id(self) -> int:
#         """ """
#     def set_id(self, id: int) -> None:
#         """ """
#     def get_hs(self) -> HardStateRef:
#         """ """
#     def set_hs(self, hs: HardStateRef) -> None:
#         """ """
#     def get_ss(self) -> SoftStateRef:
#         """ """
#     def set_ss(self, ss: SoftStateRef) -> None:
#         """ """
#     def get_progress(self) -> Optional[ProgressTrackerRef]:
#         """ """
#     def set_progress(
#         self, tracker: Optional[ProgressTracker] | Optional[ProgressTrackerRef]
#     ) -> None:
#         """ """

# class InMemoryStatus(__API_Status):
#     """
#     Represents the current status of the raft
#     """

#     def __init__(self, raft: InMemoryRaft) -> None: ...
#     def make_ref(self) -> Status__MemstorageRef: ...

# class InMemoryStatusRef(__API_Status):
#     """
#     Reference type of :class:`Status__Memstorage`.
#     """

class DestroyedRefUsedError(Exception):
    """ """

class RaftError(Exception):
    """ """

class ExistsError(RaftError):
    """
    The node {id} already exists in the {set} set.
    """

    id: int
    set: str

class NotExists(RaftError):
    """
    The node {id} is not in the {set} set.
    """

    id: int
    set: str

class CodecError(RaftError):
    """
    A protobuf message codec failed in some manner.
    """

class ConfigInvalidError(RaftError):
    """
    The configuration is invalid.
    """

class ProposalDroppedError(RaftError):
    """
    The proposal of changes was dropped.
    """

class RequestSnapshotDroppedError(RaftError):
    """
    The request snapshot is dropped.
    """

class ConfChangeError(RaftError):
    """
    ConfChange proposal is invalid.
    """

class IoError(RaftError):
    """
    An IO error occurred.
    """

class StoreError(RaftError):
    """
    A storage error occurred.
    """

class StepLocalMsg(RaftError):
    """
    Raft cannot step the local message.
    """

class StepPeerNotFound(RaftError):
    """
    The raft peer is not found and thus cannot step.
    """

class RaftStorageError(Exception):
    """
    An error with the storage.
    """

class CompactedError(RaftStorageError):
    """
    The storage was compacted and not accessible
    """

class UnavailableError(RaftStorageError):
    """
    The log is not available.
    """

class LogTemporarilyUnavailableError(RaftStorageError):
    """
    The log is being fetched.
    """

class SnapshotOutOfDateError(RaftStorageError):
    """
    The snapshot is out of date.
    """

class SnapshotTemporarilyUnavailable(RaftStorageError):
    """
    The snapshot is being created.
    """

class OtherError(RaftStorageError):
    """
    Some other error occurred.
    """
