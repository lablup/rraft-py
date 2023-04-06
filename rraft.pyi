"""
Type hints for Native Rust Extension

Ideally this file could eventually be generated automatically.
but for now this should be handwritten.
See https://github.com/PyO3/pyo3/issues/2454
"""
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Final, List, Optional, Set, Tuple

NO_LIMIT: Final[Any]
CAMPAIGN_ELECTION: Final[Any]
CAMPAIGN_PRE_ELECTION: Final[Any]
CAMPAIGN_TRANSFER: Final[Any]
INVALID_ID: Final[Any]
INVALID_INDEX: Final[Any]

def majority(total: int) -> int:
    """
    Get the majority number of given nodes count.
    """

def default_logger() -> Logger_Owner:
    """
    The default logger we fall back to when passed `None` in external_bindings facing constructors.

    Currently, this is a `log` adaptor behind a `Once` to ensure there is no clobbering.
    """

def vote_resp_msg_type(t: MessageType) -> MessageType:
    """
    Maps vote and pre_vote message types to their correspond responses.
    """

class OverflowStrategy:
    """ """

    Block: Final[Any]
    Drop: Final[Any]
    DropAndReport: Final[Any]

class SnapshotStatus:
    """ """

    Finish: Final[Any]
    Failure: Final[Any]

class ProgressState:
    """ """

    Probe: Final[Any]
    Replicate: Final[Any]
    Snapshot: Final[Any]

class StateRole:
    """ """

    Candidate: Final[Any]
    Follower: Final[Any]
    Leader: Final[Any]
    PreCandidate: Final[Any]

class ReadOnlyOption:
    """ """

    Safe: Final[Any]
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

class ConfChangeTransition:
    """ """

    Auto: Final[Any]
    Explicit: Final[Any]
    Implicit: Final[Any]

class ConfChangeType:
    """ """

    AddNode: Final[Any]
    AddLearnerNode: Final[Any]
    RemoveNode: Final[Any]

class EntryType:
    """ """

    EntryConfChange: Final[Any]
    EntryConfChangeV2: Final[Any]
    EntryNormal: Final[Any]

class __Cloneable(metaclass=ABCMeta):
    @abstractmethod
    def clone(self) -> Any: ...

class __Logger:
    def info(self, s: str) -> None:
        """
        Log info level record

        See `slog_log` for documentation.
        """
    def debug(self, s: str) -> None:
        """
        Log debug level record

        See `log` for documentation.
        """
    def trace(self, s: str) -> None:
        """
        Log trace level record

        See `log` for documentation.
        """
    def crit(self, s: str) -> None:
        """
        Log crit level record

        See `log` for documentation.
        """
    def error(self, s: str) -> None:
        """
        Log error level record

        See `log` for documentation.
        """

class Logger_Owner(__Logger):
    """ """

    def __init__(self, chan_size: int, overflow_strategy: OverflowStrategy) -> None: ...
    def make_ref(self) -> Logger_Ref: ...

class Logger_Ref(__Logger):
    """ """

class __RaftState(__Cloneable):
    def clone(self) -> RaftState_Owner: ...
    def initialized(self) -> bool:
        """
        Indicates the `RaftState` is initialized or not.
        """
    def get_conf_state(self) -> ConfState_Ref:
        """ """
    def set_conf_state(self, cs: ConfState_Ref) -> None:
        """ """
    def get_hard_state(self) -> HardState_Ref:
        """ """
    def set_hard_state(self, hs: HardState_Ref) -> None:
        """ """

class RaftState_Owner(__RaftState):
    """
    Holds both the hard state (commit index, vote leader, term) and the configuration state
    (Current node IDs)
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> RaftState_Ref: ...
    @staticmethod
    def default() -> RaftState_Owner: ...

class RaftState_Ref(__RaftState):
    """
    Reference type of :class:`RaftState_Owner`.
    """

class __StorageCore:
    def append(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> None:
        """
        Append the new entries to storage.

        # Panics

        Panics if `ents` contains compacted entries, or there's a gap between `ents` and the last
        received entry in the storage.
        """
    def apply_snapshot(self, snapshot: Snapshot_Owner | Snapshot_Ref) -> None:
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
        self, idx: int, cs: Optional[ConfState_Owner] | Optional[ConfState_Ref]
    ) -> None:
        """
        Commit to `idx` and set configuration to the given states. Only used for tests.
        """
    def set_conf_state(self, cs: ConfState_Owner | ConfState_Ref) -> None:
        """
        Saves the current conf state.
        """
    def hard_state(self) -> HardState_Ref:
        """
        Get the hard state.
        """
    def set_hardstate(self, hs: HardState_Owner | HardState_Ref) -> None:
        """
        Saves the current HardState.
        """
    def trigger_snap_unavailable(self) -> None:
        """
        Trigger a SnapshotTemporarilyUnavailable error.
        """

class MemStorageCore_Owner(__StorageCore):
    """
    The Memory Storage Core instance holds the actual state of the storage struct. To access this
    value, use the `rl` and `wl` functions on the main MemStorage implementation.
    """

    def make_ref(self) -> MemStorageCore_Ref: ...
    @staticmethod
    def default() -> MemStorageCore_Owner: ...

class MemStorageCore_Ref(__StorageCore):
    """
    Reference type of :class:`MemStorage_Owner`.
    """

class StorageCore_Owner(__StorageCore):
    """ """

    def make_ref(self) -> StorageCore_Ref: ...
    @staticmethod
    def default() -> StorageCore_Owner: ...

class StorageCore_Ref(__StorageCore):
    """
    Reference type of :class:`StorageCore_Owner`.
    """

class __Storage(__Cloneable):
    def clone(self) -> Any: ...
    def initialize_with_conf_state(
        self, conf_state: ConfState_Owner | ConfState_Ref
    ) -> None:
        """
        Initialize a `MemStorage` with a given `Config`.

        You should use the same input to initialize all nodes.
        """
    def initial_state(self) -> RaftState_Owner:
        """
        Implements the Storage trait.
        """
    def entries(
        self,
        low: int,
        high: int,
        context: GetEntriesContext_Ref,
        max_size: Optional[int],
    ) -> List[Entry_Owner]:
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
    def snapshot(self, request_index: int, to: int) -> Snapshot_Owner:
        """
        Implements the Storage trait.
        """

class MemStorage_Owner(__Storage):
    """
    `MemStorage` is a thread-safe but incomplete implementation of `Storage`, mainly for tests.

    A real `Storage` should save both raft logs and applied data. However `MemStorage` only
    contains raft logs. So you can call `MemStorage::append` to persist new received unstable raft
    logs and then access them with `Storage` APIs. The only exception is `Storage::snapshot`. There
    is no data in `Snapshot` returned by `MemStorage::snapshot` because applied data is not stored
    in `MemStorage`.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> MemStorage_Ref: ...
    def clone(self) -> MemStorage_Owner: ...
    @staticmethod
    def default() -> MemStorage_Owner: ...
    @staticmethod
    def new_with_conf_state(
        conf_state: ConfState_Owner | ConfState_Ref,
    ) -> MemStorage_Owner:
        """
        Create a new `MemStorage` with a given `Config`. The given `Config` will be used to
        initialize the storage.

        You should use the same input to initialize all nodes.
        """
    def wl(self, f: Callable[[MemStorageCore_Ref], None]) -> None:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self, f: Callable[[MemStorageCore_Ref], None]) -> None:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class MemStorage_Ref(__Storage):
    """
    Reference type of :class:`MemStorage_Owner`.
    """

    def clone(self) -> MemStorage_Owner: ...
    def wl(self, f: Callable[[MemStorageCore_Ref], None]) -> None:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self, f: Callable[[MemStorageCore_Ref], None]) -> None:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class Storage_Owner(__Storage):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> Storage_Ref: ...
    def clone(self) -> Storage_Owner: ...
    @staticmethod
    def default() -> Storage_Owner: ...
    @staticmethod
    def new_with_conf_state(
        conf_state: ConfState_Owner | ConfState_Ref,
    ) -> Storage_Owner:
        """ """
    def wl(self, f: Callable[[StorageCore_Ref], None]) -> None:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self, f: Callable[[StorageCore_Ref], None]) -> None:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class Storage_Ref(__Storage):
    """
    Reference type of :class:`Storage_Owner`.
    """

    def clone(self) -> Storage_Owner: ...
    def wl(self, f: Callable[[StorageCore_Ref], None]) -> None:
        """
        Opens up a write lock on the storage and returns guard handle. Use this
        with functions that take a mutable reference to self.
        """
    def rl(self, f: Callable[[StorageCore_Ref], None]) -> None:
        """
        Opens up a read lock on the storage and returns a guard handle. Use this
        with functions that don't require mutation.
        """

class __Ready:
    def hs(self) -> Optional[HardState_Ref]:
        """
        The current state of a Node to be saved to stable storage.
        HardState will be None state if there is no update.
        """
    def ss(self) -> Optional[SoftState_Ref]:
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
    def snapshot(self) -> Snapshot_Ref:
        """
        Snapshot specifies the snapshot to be saved to stable storage.
        """
    def committed_entries(self) -> List[Entry_Ref]:
        """
        CommittedEntries specifies entries to be committed to a
        store/state-machine. These have previously been committed to stable
        store.
        """
    def take_committed_entries(self) -> List[Entry_Owner]:
        """
        Take the CommitEntries.
        """
    def entries(self) -> List[Entry_Ref]:
        """
        Entries specifies entries to be saved to stable storage.
        """
    def take_entries(self) -> List[Entry_Owner]:
        """
        Take the Entries.
        """
    def messages(self) -> List[Message_Ref]:
        """
        Messages specifies outbound messages to be sent.
        If it contains a MsgSnap message, the application MUST report back to raft
        when the snapshot has been received or has failed by calling ReportSnapshot.
        """
    def take_messages(self) -> List[Message_Owner]:
        """
        Take the Messages.
        """
    def persisted_messages(self) -> List[Message_Ref]:
        """
        Persisted Messages specifies outbound messages to be sent AFTER the HardState,
        Entries and Snapshot are persisted to stable storage.
        """
    def take_persisted_messages(self) -> List[Message_Owner]:
        """
        Take the Persisted Messages.
        """
    def read_states(self) -> List[ReadState_Ref]:
        """
        ReadStates specifies the state for read only query.
        """
    def take_read_states(self) -> List[ReadState_Owner]:
        """
        ReadStates specifies the state for read only query.
        """

class Ready_Owner(__Ready):
    """
    Ready encapsulates the entries and messages that are ready to read,
    be saved to stable storage, committed or sent to other peers.
    """

    def make_ref(self) -> Ready_Ref: ...
    @staticmethod
    def default() -> Ready_Owner: ...

class Ready_Ref(__Ready):
    """
    Reference type of :class:`Ready_Owner`.
    """

class __RawNode:
    def advance_apply(self) -> None:
        """
        Advance apply to the index of the last committed entries given before.
        """
    def advance_apply_to(self, applied: int) -> None:
        """
        Advance apply to the passed index.
        """
    def advance(self, rd: Ready_Ref) -> LightReady_Owner:
        """
        Advances the ready after fully processing it.

        Fully processing a ready requires to persist snapshot, entries and hard states, apply all
        committed entries, send all messages.

        Returns the LightReady that contains commit index, committed entries and messages. [`LightReady`]
        contains updates that only valid after persisting last ready. It should also be fully processed.
        Then [`Self::advance_apply`] or [`Self::advance_apply_to`] should be used later to update applying
        progress.
        """
    def advance_append(self, rd: Ready_Ref) -> LightReady_Owner:
        """
        Advances the ready without applying committed entries. [`Self::advance_apply`] or
        [`Self::advance_apply_to`] should be used later to update applying progress.

        Returns the LightReady that contains commit index, committed entries and messages.

        Since Ready must be persisted in order, calling this function implicitly means
        all ready collected before have been persisted.
        """
    def advance_append_async(self, rd: Ready_Ref) -> None:
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
    def report_snapshot(self, id: int, snapshot: SnapshotStatus) -> None:
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
    def snap(self) -> Optional[Snapshot_Ref]:
        """
        Snapshot specifies the snapshot to be saved to stable storage.
        """
    def step(self, msg: Message_Owner | Message_Ref) -> None:
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
    def propose(self, context: bytes | List[int], data: bytes | List[int]) -> None:
        """
        Propose proposes data be appended to the raft log.
        """
    def propose_conf_change(
        self, context: bytes | List[int], cc: ConfChange_Owner | ConfChange_Ref
    ) -> None:
        """
        ProposeConfChange proposes a config change.

        If the node enters joint state with `auto_leave` set to true, it's
        caller's responsibility to propose an empty conf change again to force
        leaving joint state.
        """
    def propose_conf_change_v2(
        self, context: bytes | List[int], cc: ConfChangeV2_Owner | ConfChangeV2_Ref
    ) -> None:
        """
        ProposeConfChange proposes a config change.

        If the node enters joint state with `auto_leave` set to true, it's
        caller's responsibility to propose an empty conf change again to force
        leaving joint state.
        """
    def apply_conf_change(
        self, cc: ConfChange_Owner | ConfChange_Ref
    ) -> ConfState_Owner:
        """
        Applies a config change to the local node. The app must call this when it
        applies a configuration change, except when it decides to reject the
        configuration change, in which case no call must take place.
        """
    def apply_conf_change_v2(
        self, cc: ConfChangeV2_Owner | ConfChangeV2_Ref
    ) -> ConfState_Owner:
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
    def read_index(self, rctx: bytes | List[int]) -> None:
        """
        ReadIndex requests a read state. The read state will be set in ready.
        Read State has a read index. Once the application advances further than the read
        index, any linearizable read requests issued before the read request can be
        processed safely. The read state will have the same rctx attached.
        """
    def ready(self) -> Ready_Owner:
        """
        Returns the outstanding work that the application needs to handle.

        This includes appending and applying entries or a snapshot, updating the HardState,
        and sending messages. The returned `Ready` *MUST* be handled and subsequently
        passed back via `advance` or its families. Before that, *DO NOT* call any function like
        `step`, `propose`, `campaign` to change internal state.

        [`Self::has_ready`] should be called first to check if it's necessary to handle the ready.
        """
    def request_snapshot(self) -> Ready_Owner:
        """
        Request a snapshot from a leader.
        The snapshot's index must be greater or equal to the request_index (last_index) or
        the leader's term must be greater than the request term (last_index's term).
        """

class RawNode__MemStorage_Owner(__RawNode):
    """
    RawNode is a thread-unsafe Node.
    The methods of this struct correspond to the methods of Node and are described
    more fully there.
    """

    def __init__(
        self,
        cfg: Config_Owner | Config_Ref,
        store: MemStorage_Owner | MemStorage_Ref,
        logger: Logger_Owner | Logger_Ref,
    ) -> None: ...
    def make_ref(self) -> RawNode__MemStorage_Ref: ...
    def get_raft(self) -> Raft__MemStorage_Ref:
        """ """
    def store(self) -> MemStorage_Ref:
        """Returns the store as a mutable reference."""
    def status(self) -> Status__Memstorage_Owner:
        """
        Status returns the current status of the given group.
        """

class RawNode__MemStorage_Ref(__RawNode):
    """
    Reference type of :class:`RawNode__MemStorage_Owner`.
    """

    def get_raft(self) -> Raft__MemStorage_Ref:
        """ """
    def store(self) -> MemStorage_Ref:
        """Returns the store as a mutable reference."""
    def status(self) -> Status__Memstorage_Owner:
        """
        Status returns the current status of the given group.
        """

class RawNode_Owner(__RawNode):
    """
    RawNode is a thread-unsafe Node.
    The methods of this struct correspond to the methods of Node and are described
    more fully there.
    """

    def __init__(
        self,
        cfg: Config_Owner | Config_Ref,
        store: Storage_Owner | Storage_Ref,
        logger: Logger_Owner | Logger_Ref,
    ) -> None: ...
    def make_ref(self) -> RawNode_Ref: ...
    def get_raft(self) -> Raft_Ref:
        """ """
    def store(self) -> Storage_Ref:
        """Returns the store as a mutable reference."""
    # def status(self) -> Status__Memstorage_Owner:
    #     """
    #     Status returns the current status of the given group.
    #     """

class RawNode_Ref(__RawNode):
    """
    Reference type of :class:`RawNode_Owner`.
    """

    def get_raft(self) -> Raft_Ref:
        """ """
    def store(self) -> Storage_Ref:
        """Returns the store as a mutable reference."""
    # def status(self) -> Status__Memstorage_Owner:
    #     """
    #     Status returns the current status of the given group.
    #     """

class __Peer:
    def get_id(self) -> int:
        """ """
    def set_id(self, id: int) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes | List[int]) -> None:
        """ """

class Peer_Owner(__Peer):
    """
    Represents a Peer node in the cluster.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> Peer_Ref: ...

class Peer_Ref(__Peer):
    """
    Reference type of :class:`Peer_Owner`.
    """

class __LightReady:
    def commit_index(self) -> Optional[int]:
        """
        The current commit index.
        It will be None state if there is no update.
        It is not required to save it to stable storage.
        """
    def committed_entries(self) -> List[Entry_Ref]:
        """
        CommittedEntries specifies entries to be committed to a
        store/state-machine. These have previously been committed to stable
        store.
        """
    def take_committed_entries(self) -> List[Entry_Owner]:
        """
        Take the CommitEntries.
        """
    def messages(self) -> List[Message_Ref]:
        """
        Messages specifies outbound messages to be sent.
        """
    def take_messages(self) -> List[Message_Owner]:
        """
        Take the Messages.
        """

class LightReady_Owner(__LightReady):
    """
    LightReady encapsulates the commit index, committed entries and
    messages that are ready to be applied or be sent to other peers.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> LightReady_Ref: ...
    @staticmethod
    def default() -> LightReady_Owner: ...

class LightReady_Ref(__LightReady):
    """
    Reference type of :class:`LightReady_Owner`.
    """

class __SnapshotMetadata(__Cloneable):
    def clone(self) -> SnapshotMetadata_Owner: ...
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
    def get_conf_state(self) -> ConfState_Ref:
        """ """
    def set_conf_state(self, conf_state: ConfState_Owner | ConfState_Ref) -> None:
        """ """
    def clear_conf_state(self) -> None:
        """ """
    def has_conf_state(self) -> bool:
        """ """

class SnapshotMetadata_Owner(__SnapshotMetadata):
    """ """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> SnapshotMetadata_Owner: ...
    def make_ref(self) -> SnapshotMetadata_Ref: ...

class SnapshotMetadata_Ref(__SnapshotMetadata):
    """
    Reference type of :class:`SnapshotMetadata_Owner`.
    """

class __Snapshot(__Cloneable):
    def clone(self) -> Snapshot_Owner: ...
    def get_data(self) -> bytes:
        """ """
    def set_data(self, data: bytes) -> None:
        """ """
    def clear_data(self) -> None:
        """ """
    def get_metadata(self) -> SnapshotMetadata_Ref:
        """ """
    def set_metadata(
        self, meta_data: SnapshotMetadata_Owner | SnapshotMetadata_Ref
    ) -> None:
        """ """
    def clear_metadata(self) -> None:
        """ """
    def has_metadata(self) -> bool:
        """ """
    def is_empty(self) -> bool:
        """ """

class Snapshot_Owner(__Snapshot):
    """ """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> Snapshot_Owner: ...
    def make_ref(self) -> Snapshot_Ref: ...

class Snapshot_Ref(__Snapshot):
    """
    Reference type of :class:`Snapshot_Owner`.
    """

class __Message(__Cloneable):
    def clone(self) -> Message_Owner: ...
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
        """ """
    def set_log_term(self, log_index: int) -> None:
        """ """
    def clear_log_term(self) -> None:
        """ """
    def get_priority(self) -> int:
        """ """
    def set_priority(self, priority: int) -> None:
        """ """
    def clear_priority(self) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes | List[int]) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_reject_hint(self) -> int:
        """ """
    def set_reject_hint(self, reject_hint: bool) -> None:
        """ """
    def clear_reject_hint(self) -> None:
        """ """
    def get_entries(self) -> List[Entry_Ref]:
        """ """
    def set_entries(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> None:
        """ """
    def clear_entries(self) -> None:
        """ """
    def get_msg_type(self) -> MessageType:
        """ """
    def set_msg_type(self, typ: MessageType) -> None:
        """ """
    def clear_msg_type(self) -> None:
        """ """
    def get_reject(self) -> bool:
        """ """
    def set_reject(self, reject: bool) -> None:
        """ """
    def clear_reject(self) -> None:
        """ """
    def get_snapshot(self) -> Snapshot_Ref:
        """ """
    def set_snapshot(self, snapshot: Snapshot_Owner | Snapshot_Ref) -> None:
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
        """ """
    def get_cached_size(self) -> int:
        """ """

class Message_Owner(__Message):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> Message_Ref: ...
    @staticmethod
    def default() -> Message_Owner: ...

class Message_Ref(Message):
    """
    Reference type of :class:`Message_Owner`.
    """

class __HardState(__Cloneable):
    def clone(self) -> HardState_Owner: ...
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

class HardState_Owner(__HardState):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> HardState_Ref: ...
    @staticmethod
    def default() -> HardState_Owner: ...

class HardState_Ref(__HardState):
    """
    Reference type of :class:`HardState_Owner`.
    """

class __GetEntriesContext:
    """
    Records the context of the caller who calls entries() of Storage trait.
    """

    def can_async(self) -> bool:
        """ """

class GetEntriesContext_Owner(__GetEntriesContext):
    @staticmethod
    def empty() -> GetEntriesContext_Owner: ...
    def make_ref(self) -> ConfChange_Ref: ...

class GetEntriesContext_Ref(__GetEntriesContext):
    """
    Reference type of :class:`GetEntriesContext_Owner`.
    """

class __Entry(__Cloneable):
    def clone(self) -> Entry_Owner: ...
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes | List[int]) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_data(self) -> bytes:
        """ """
    def set_data(self, data: bytes | List[int]) -> None:
        """ """
    def clear_data(self) -> None:
        """ """
    def get_entry_type(self) -> EntryType:
        """ """
    def set_entry_type(self, typ: EntryType) -> None:
        """ """
    def clear_entry_type(self) -> None:
        """ """
    def get_sync_log(self) -> bool:
        """ """
    def set_sync_log(self, sync_log: bool) -> None:
        """ """
    def clear_sync_log(self) -> None:
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

class Entry_Owner(__Entry):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> Entry_Ref: ...
    @staticmethod
    def default() -> Entry_Owner: ...

class Entry_Ref(__Entry):
    """
    Reference type of :class:`Entry_Owner`.
    """

class __ConfState(__Cloneable):
    def clone(self) -> ConfState_Owner: ...
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

class ConfState_Owner(__ConfState):
    """ """

    def __init__(
        self, voters: Optional[List[int]], learners: Optional[List[int]]
    ) -> None: ...
    def make_ref(self) -> ConfState_Ref: ...
    @staticmethod
    def default() -> ConfState_Owner: ...

class ConfState_Ref(__ConfState):
    """
    Reference type of :class:`ConfState_Owner`.
    """

class __ConfChangeV2(__Cloneable):
    def clone(self) -> ConfChangeV2_Owner: ...
    def get_changes(self) -> bytes:
        """ """
    def set_changes(
        self, changes: List[ConfChangeSingle_Owner] | List[ConfChangeSingle_Ref]
    ) -> None:
        """ """
    def clear_changes(self) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes | List[int]) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def get_transition(self) -> ConfChangeTransition:
        """ """
    def set_transition(self, transition: ConfChangeTransition) -> None:
        """ """
    def clear_transition(self) -> None:
        """ """
    def enter_joint(self) -> Optional[bool]:
        """ """
    def leave_joint(self) -> bool:
        """ """
    def clear_joint(self) -> None:
        """ """
    def write_to_bytes(self) -> bytes:
        """ """
    def as_v1(self) -> Optional[ConfChange_Ref]:
        """
        Converts conf change to `ConfChange`.

        `ConfChangeV2` can't be changed back to `ConfChange`.
        """
    def as_v2(self) -> ConfChangeV2_Owner:
        """
        Gets conf change as `ConfChangeV2`.
        """
    def into_v2(self) -> ConfChangeV2_Owner:
        """
        Converts conf change to `ConfChangeV2`.
        """

class ConfChangeV2_Owner(__ConfChangeV2):
    """ """

    def __init__(self) -> None: ...
    @staticmethod
    def default() -> ConfChangeV2_Owner: ...
    def make_ref(self) -> ConfChangeV2_Ref: ...

class ConfChangeV2_Ref(__ConfChangeV2):
    """
    Reference type of :class:`ConfChangeV2_Owner`.
    """

class __ConfChangeSingle(__Cloneable):
    def clone(self) -> ConfChangeSingle_Owner: ...
    def get_node_id(self) -> int:
        """ """
    def set_node_id(self, node_id: int):
        """ """
    def clear_node_id(self) -> None:
        """ """
    def get_change_type(self) -> ConfChangeType:
        """ """
    def set_change_type(self, typ: ConfChangeType) -> None:
        """ """
    def clear_change_type(self) -> None:
        """ """

class ConfChangeSingle_Owner(__ConfChangeSingle):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> ConfChangeSingle_Ref: ...
    @staticmethod
    def default() -> ConfChangeSingle_Owner: ...

class ConfChangeSingle_Ref(__ConfChangeSingle):
    """
    Reference type of :class:`ConfChangeSingle_Owner`.
    """

class __ConfChange(__Cloneable):
    def clone(self) -> ConfChange_Owner: ...
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
    def get_change_type(self) -> ConfChangeType:
        """ """
    def set_change_type(self, typ: ConfChangeType) -> None:
        """ """
    def clear_change_type(self) -> None:
        """ """
    def get_context(self) -> bytes:
        """ """
    def set_context(self, context: bytes | List[int]) -> None:
        """ """
    def clear_context(self) -> None:
        """ """
    def as_v1(self) -> Optional[ConfChange_Ref]:
        """
        Converts conf change to `ConfChange`.

        `ConfChangeV2` can't be changed back to `ConfChange`.
        """
    def as_v2(self) -> ConfChangeV2_Owner:
        """
        Gets conf change as `ConfChangeV2`.
        """
    def into_v2(self) -> ConfChangeV2_Owner:
        """
        Converts conf change to `ConfChangeV2`.
        """
    def write_to_bytes(self) -> bytes:
        """ """

class ConfChange_Owner(__ConfChange):
    """ """

    def __init__(self) -> None: ...
    def make_ref(self) -> ConfChange_Ref: ...
    @staticmethod
    def default() -> ConfChange_Owner: ...

class ConfChange_Ref(__ConfChange):
    """
    Reference type of :class:`ConfChange_Owner`.
    """

class __Unstable:
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
    def slice(self, lo: int, hi: int) -> List[Entry_Ref]:
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
    def restore(self, snap: Snapshot_Ref) -> None:
        """
        From a given snapshot, restores the snapshot to self, but doesn't unpack.
        """
    def truncate_and_append(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> None:
        """
        Append entries to unstable, truncate local block first if overlapped.

        # Panics

        Panics if truncate logs to the entry before snapshot
        """
    def get_entries_size(self) -> int:
        """ """
    def set_entries_size(self, entries_size: int) -> None:
        """ """
    def get_offset(self) -> int:
        """ """
    def set_offset(self, offset: int) -> None:
        """ """
    def get_entries(self) -> List[Entry_Ref]:
        """ """
    def set_entries(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> None:
        """ """
    def get_logger(self) -> Logger_Ref:
        """ """
    def set_logger(self, logger: Logger_Owner | Logger_Ref) -> None:
        """ """
    def get_snapshot(self) -> Optional[Snapshot_Ref]:
        """ """
    def set_snapshot(self, snapshot: Snapshot_Owner | Snapshot_Ref) -> None:
        """ """

class Unstable_Owner(__Unstable):
    """
    The `unstable.entries[i]` has raft log position `i+unstable.offset`.
    Note that `unstable.offset` may be less than the highest log
    position in storage; this means that the next write to storage
    might need to truncate the log before persisting unstable.entries.
    """

    def __init__(self, offset: int, logger: Logger_Owner | Logger_Ref) -> None: ...
    def make_ref(self) -> Unstable_Ref: ...

class Unstable_Ref(__Unstable):
    """
    Reference type of :class:`Unstable_Owner`.
    """

class __Status:
    def get_applied(self) -> int:
        """ """
    def set_applied(self, applied: int) -> None:
        """ """
    def get_id(self) -> int:
        """ """
    def set_id(self, id: int) -> None:
        """ """
    def get_hs(self) -> HardState_Ref:
        """ """
    def set_hs(self, hs: HardState_Ref) -> None:
        """ """
    def get_ss(self) -> SoftState_Ref:
        """ """
    def set_ss(self, ss: SoftState_Ref) -> None:
        """ """
    def get_progress(self) -> Optional[ProgressTracker_Ref]:
        """ """
    def set_progress(
        self, tracker: Optional[ProgressTracker_Owner] | Optional[ProgressTracker_Ref]
    ) -> None:
        """ """

class Status__Memstorage_Owner(__Status):
    """
    Represents the current status of the raft
    """

    def __init__(self, raft: Raft__MemStorage_Owner) -> None: ...
    def make_ref(self) -> Status__Memstorage_Ref: ...

class Status__Memstorage_Ref(__Status):
    """
    Reference type of :class:`Status__Memstorage_Owner`.
    """

class __SoftState:
    def get_leader_id(self) -> int:
        """ """
    def set_leader_id(self, leader_id: int) -> None:
        """ """
    def get_raft_state(self) -> StateRole:
        """ """
    def set_raft_state(self, role: StateRole) -> None:
        """ """

class SoftState_Owner(__SoftState):
    """
    SoftState provides state that is useful for logging and debugging.
    The state is volatile and does not need to be persisted to the WAL.
    """

    def make_ref(self) -> SoftState_Ref: ...
    @staticmethod
    def default() -> SoftState_Owner: ...

class SoftState_Ref(__SoftState):
    """
    Reference type of :class:`SoftState_Owner`.
    """

class __ReadState(__Cloneable):
    def clone(self) -> ReadState_Owner: ...
    def get_index(self) -> int:
        """ """
    def set_index(self, idx: int) -> None:
        """ """
    def get_request_ctx(self) -> bytes:
        """ """
    def set_request_ctx(self, request_ctx: bytes | List[int]) -> None:
        """ """

class ReadState_Owner(__ReadState):
    """
    ReadState provides state for read only query.
    It's caller's responsibility to send MsgReadIndex first before getting
    this state from ready. It's also caller's duty to differentiate if this
    state is what it requests through request_ctx, e.g. given a unique id as
    request_ctx.
    """

    def __init__(self) -> None: ...
    def make_ref(self) -> ReadState_Ref: ...

class ReadState_Ref(__ReadState):
    """
    Reference type of :class:`ReadState_Owner`.
    """

class __RaftLog:
    def entries(
        self, idx: int, context: GetEntriesContext_Ref, max_size: Optional[int]
    ) -> List[Entry_Owner]:
        """
        Returns entries starting from a particular index and not exceeding a bytesize.
        """
    def all_entries(self) -> List[Entry_Owner]:
        """
        Returns all the entries. Only used by tests.
        """
    def append(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> int:
        """
        Appends a set of entries to the unstable list.
        """
    def applied(self) -> int:
        """
        Returns the last applied index.
        """
    def find_conflict(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> int:
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
    def store(self) -> MemStorage_Ref:
        """ """
    def next_entries(self, max_size: Optional[int]) -> Optional[List[Entry_Owner]]:
        """
        Returns all the available entries for execution.
        If applied is smaller than the index of snapshot, it returns all committed
        entries after the index of snapshot.
        """
    def next_entries_since(
        self, since_idx: int, max_size: Optional[int]
    ) -> List[Entry_Owner]:
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
        ents: List[Entry_Owner] | List[Entry_Ref],
    ) -> Optional[Tuple[int, int]]:
        """
        Returns None if the entries cannot be appended. Otherwise,
        it returns Some((conflict_index, last_index)).

        # Panics

        Panics if it finds a conflicting index less than committed index.
        """
    def snapshot(self, request_index: int, to: int) -> Snapshot_Ref:
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
    def unstable(self) -> Unstable_Ref:
        """
        Returns a reference to the unstable log.
        """
    def unstable_entries(self) -> List[Entry_Ref]:
        """
        Returns slice of entries that are not persisted.
        """
    def unstable_snapshot(self) -> Optional[Snapshot_Ref]:
        """
        Returns the snapshot that are not persisted.
        """
    def get_applied(self) -> int:
        """ """
    def set_applied(self, applied: int) -> None:
        """ """
    def get_committed(self) -> int:
        """ """
    def set_committed(self, committed: int) -> None:
        """ """
    def get_persisted(self) -> int:
        """ """
    def set_persisted(self, persisted: int) -> None:
        """ """

class RaftLog__MemStorage_Owner(__RaftLog):
    """
    Raft log implementation
    """

    def __init__(
        self, store: MemStorage_Ref, logger: Logger_Owner | Logger_Ref
    ) -> None: ...
    def make_ref(self) -> RaftLog__MemStorage_Ref: ...
    def get_store(self) -> MemStorage_Ref:
        """
        Grab a read-only reference to the underlying storage.
        """

class RaftLog__MemStorage_Ref(__RaftLog):
    """
    Reference type of :class:`RaftLog__MemStorage_Owner`.
    """

    def get_store(self) -> MemStorage_Ref:
        """
        Grab a read-only reference to the underlying storage.
        """

class RaftLog_Owner(__RaftLog):
    """ """

    def __init__(
        self, store: Storage_Ref, logger: Logger_Owner | Logger_Ref
    ) -> None: ...
    def make_ref(self) -> RaftLog_Ref: ...
    def get_store(self) -> Storage_Ref:
        """
        Grab a read-only reference to the underlying storage.
        """

class RaftLog_Ref(__RaftLog):
    """
    Reference type of :class:`RaftLog_Owner`.
    """

    def get_store(self) -> Storage_Ref:
        """
        Grab a read-only reference to the underlying storage.
        """

class __Raft:
    def append_entry(self, ents: List[Entry_Owner] | List[Entry_Ref]) -> bool:
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
        self, ents: List[Entry_Owner] | List[Entry_Ref]
    ) -> bool:
        """
        Increase size of 'ents' to uncommitted size. Return true when size limit
        is satisfied. Otherwise return false and uncommitted size remains unchanged.
        For raft with no limit(or non-leader raft), it always return true.
        """
    def reduce_uncommitted_size(
        self, ents: List[Entry_Owner] | List[Entry_Ref]
    ) -> None:
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
    def load_state(self, hs: HardState_Owner | HardState_Ref) -> None:
        """
        For a given hardstate, load the state into self.
        """
    def soft_state(self) -> SoftState_Ref:
        """
        Returns a value representing the softstate at the time of calling.
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
    def step(self, msg: Message_Owner | Message_Ref) -> None:
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
    def post_conf_change(self) -> ConfState_Ref:
        """
        Updates the in-memory state and, when necessary, carries out additional actions
        such as reacting to the removal of nodes or changed quorum requirements.
        """
    def in_lease(self) -> bool:
        """
        Returns whether the current raft is in lease.
        """
    def handle_heartbeat(self, msg: Message_Owner | Message_Ref) -> None:
        """ """
    def handle_append_entries(self, msg: Message_Owner | Message_Ref) -> None:
        """ """
    def request_snapshot(self) -> None:
        """
        Request a snapshot from a leader.
        """
    def prs(self) -> ProgressTracker_Ref:
        """
        Returns a read-only reference to the progress set.
        """
    def reset(self, term: int) -> None:
        """
        Resets the current node to a given term.
        """
    def restore(self, snapshot: Snapshot_Owner | Snapshot_Ref) -> bool:
        """
        Recovers the state machine from a snapshot. It restores the log and the
        configuration of state machine.
        """
    def snap(self) -> Snapshot_Ref:
        """
        Grabs a reference to the snapshot
        """
    def store(self) -> MemStorage_Ref:
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
    def get_lead_transferee(self) -> Optional[int]:
        """ """
    def set_lead_transferee(self, lead_transferee: int) -> None:
        """ """
    def get_term(self) -> int:
        """ """
    def set_term(self, term: int) -> None:
        """ """
    def get_vote(self) -> int:
        """ """
    def set_vote(self, vote: int) -> None:
        """ """
    def get_priority(self) -> int:
        """ """
    def set_priority(self, priority: int) -> None:
        """ """
    def get_leader_id(self) -> int:
        """ """
    def set_leader_id(self, leader_id: int) -> None:
        """ """
    def get_max_msg_size(self) -> int:
        """ """
    def set_max_msg_size(self, max_msg_size: int) -> None:
        """ """
    def get_pending_conf_index(self) -> int:
        """ """
    def set_pending_conf_index(self, pending_conf_index: int) -> None:
        """ """
    def get_pending_request_snapshot(self) -> int:
        """ """
    def set_pending_request_snapshot(self, pending_request_snapshot: int) -> None:
        """ """
    def get_id(self) -> int:
        """ """
    def set_id(self, id: int) -> None:
        """ """
    def get_msgs(self) -> List[Message_Ref]:
        """ """
    def take_msgs(self) -> List[Message_Owner]:
        """ """
    def set_msgs(self, msgs: List[Message_Owner | Message_Ref]) -> None:
        """ """
    def get_max_inflight(self) -> int:
        """ """
    def set_max_inflight(self, max_inflight: int) -> None:
        """ """
    def get_state(self) -> StateRole:
        """ """
    def set_state(self, state_role: StateRole) -> None:
        """ """
    def get_raft_log(self) -> RaftLog__MemStorage_Ref:
        """ """
    def get_election_elapsed(self) -> int:
        """ """
    def set_election_elapsed(self, election_elapsed: int) -> None:
        """ """
    def get_check_quorum(self) -> bool:
        """ """
    def set_check_quorum(self, check_quorum: bool) -> None:
        """ """
    def get_pre_vote(self) -> bool:
        """"""
    def set_pre_vote(self, pre_vote: bool) -> None:
        """"""
    def apply_conf_change(self, conf_change: ConfChangeV2_Ref) -> ConfChange_Ref:
        """ """
    def set_batch_append(self, batch_append: bool) -> None:
        """Set whether batch append msg at runtime."""
    def get_readonly_read_index_queue(self) -> List[List[int]]:
        """ """
    def get_readstates(self) -> List[ReadState_Owner]:
        """ """
    def set_max_committed_size_per_ready(
        self, max_committed_size_per_ready: int
    ) -> None:
        """ """
    def get_read_states(self) -> List[ReadState_Owner]:
        """ """
    def set_read_states(
        self, read_states: List[ReadState_Owner] | List[ReadState_Ref]
    ) -> None:
        """ """
    def get_read_only_option(self) -> ReadOnlyOption:
        """ """
    def set_read_only_option(self, option: ReadOnlyOption) -> None:
        """ """

class Raft__MemStorage_Owner(__Raft):
    """
    A struct that represents the raft consensus itself. Stores details concerning the current
    and possible state the system can take.
    """

    def __init__(
        self,
        cfg: Config_Owner | Config_Ref,
        store: MemStorage_Owner | MemStorage_Ref,
        logger: Logger_Owner | Logger_Ref,
    ) -> None: ...
    def make_ref(self) -> Raft__MemStorage_Ref: ...

class Raft__MemStorage_Ref(__Raft):
    """
    Reference type of :class:`Raft__MemStorage_Owner`.
    """

class Raft_Owner(__Raft):
    """
    A struct that represents the raft consensus itself. Stores details concerning the current
    and possible state the system can take.
    """

    def __init__(
        self,
        cfg: Config_Owner | Config_Ref,
        store: Storage_Owner | Storage_Ref,
        logger: Logger_Owner | Logger_Ref,
    ) -> None: ...
    def make_ref(self) -> Raft_Ref: ...

class Raft_Ref(__Raft):
    """
    Reference type of :class:`Raft_Owner`.
    """

class __ProgressTracker(__Cloneable):
    def clone(self) -> ProgressTracker_Owner: ...
    def get(self, id: int) -> Optional[Progress_Ref]:
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
    def conf_voters(self) -> JointConfig_Ref:
        """ """
    def conf_learners(self) -> Set[int]:
        """ """

class ProgressTracker_Owner(__ProgressTracker):
    """
    `ProgressTracker` contains several `Progress`es,
    which could be `Leader`, `Follower` and `Learner`.
    """

    def __init__(self, max_inflight: int) -> None: ...
    def make_ref(self) -> ProgressTracker_Ref: ...

class ProgressTracker_Ref(__ProgressTracker):
    """
    Reference type of :class:`ProgressTracker_Owner`.
    """

class __Progress(__Cloneable):
    def clone(self) -> Progress_Owner: ...
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
    def is_paused(self) -> bool:
        """
        Determine whether progress is paused.
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
        update committed_index.
        """
    def optimistic_update(self, n: int) -> None:
        """
        Optimistically advance the index
        """
    def get_ins(self) -> Inflights_Ref:
        """"""
    def set_ins(self, inflights: Inflights_Owner | Inflights_Ref) -> None:
        """"""
    def get_commit_group_id(self) -> int:
        """"""
    def set_commit_group_id(self, commit_group_id: int) -> None:
        """"""
    def get_committed_index(self) -> int:
        """"""
    def set_committed_index(self, committed_index: int) -> None:
        """"""
    def get_matched(self) -> int:
        """"""
    def set_matched(self, matched: int) -> None:
        """"""
    def get_next_idx(self) -> int:
        """"""
    def set_next_idx(self, next_idx: int) -> None:
        """"""
    def get_pending_snapshot(self) -> int:
        """"""
    def set_pending_snapshot(self, pending_snapshot: int) -> None:
        """"""
    def get_pending_request_snapshot(self) -> int:
        """"""
    def set_pending_request_snapshot(self, pending_request_snapshot: int) -> None:
        """"""
    def get_recent_active(self) -> bool:
        """"""
    def set_recent_active(self, recent_active: bool) -> None:
        """"""
    def get_paused(self) -> bool:
        """"""
    def set_paused(self, paused: bool) -> None:
        """"""
    def get_state(self) -> ProgressState:
        """"""
    def set_state(self, state: ProgressState) -> None:
        """"""

class Progress_Owner(__Progress):
    """
    The progress of catching up from a restart.
    """

    def __init__(self, next_idx: int, ins_size: int) -> None: ...
    def make_ref(self) -> Progress_Ref: ...

class Progress_Ref(__Progress):
    """
    Reference type of :class:`Progress_Owner`.
    """

class __JointConfig(__Cloneable):
    def clone(self) -> JointConfig_Owner: ...
    def clear(self) -> None:
        """Clears all IDs."""
    def contains(self, id: int) -> bool:
        """Check if an id is a voter."""
    def ids() -> Set[int]:
        """ """
    def is_singleton(self) -> bool:
        """
        Returns true if (and only if) there is only one voting member
        (i.e. the leader) in the current configuration.
        """

class JointConfig_Owner(__JointConfig):
    """
    A configuration of two groups of (possibly overlapping) majority configurations.
    Decisions require the support of both majorities.
    """

    def __init__(self, voters: Set[int]) -> None: ...
    def make_ref(self) -> JointConfig_Ref: ...

class JointConfig_Ref(__JointConfig):
    """
    Reference type of :class:`JointConfig_Owner`.
    """

class __MajorityConfig(__Cloneable):
    def clone(self) -> MajorityConfig_Owner: ...
    def capacity(self) -> int:
        """"""
    def is_empty(self) -> bool:
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
    def raw_slice(self) -> List[int]:
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

class MajorityConfig_Owner(__MajorityConfig):
    """
    A set of IDs that uses majority quorums to make decisions.
    """

    def __init__(self, voters: Set[int]) -> None: ...
    def make_ref(self) -> MajorityConfig_Ref: ...

class MajorityConfig_Ref(__MajorityConfig):
    """
    Reference type of :class:`MajorityConfig_Owner`.
    """

class __Inflights(__Cloneable):
    def clone(self) -> Inflights_Owner: ...
    def add(self, inflight: int) -> None:
        """Adds an inflight into inflights"""
    def set_cap(self, incoming_cap: int) -> None:
        """ """
    def full(self) -> bool:
        """Returns true if the inflights is full."""
    def reset(self) -> None:
        """Frees all inflights."""
    def free_to(self, to: int) -> None:
        """Frees the inflights smaller or equal to the given `to` flight."""
    def free_first_one(self) -> None:
        """Frees the first buffer entry."""

class Inflights_Owner(__Inflights):
    """
    A buffer of inflight messages.
    """

    def __init__(self, cap: int) -> None: ...
    def make_ref(self) -> Inflights_Ref: ...

class Inflights_Ref(__Inflights):
    """
    Reference type of :class:`Inflights_Ref`.
    """

class __Config(__Cloneable):
    def clone(self) -> Config_Owner: ...
    def min_election_tick(self) -> int:
        """The minimum number of ticks before an election."""
    def set_min_election_tick(self, min_election_tick: int) -> None:
        """ """
    def max_election_tick(self) -> int:
        """The maximum number of ticks before an election."""
    def set_max_election_tick(self, max_election_tick: int) -> None:
        """ """
    def validate(self) -> None:
        """Runs validations against the config."""
    def get_read_only_option(self) -> ReadOnlyOption:
        """"""
    def set_read_only_option(self, read_only_option: ReadOnlyOption) -> None:
        """"""
    def get_id(self) -> int:
        """"""
    def set_id(self, id: int) -> None:
        """"""
    def get_election_tick(self) -> int:
        """"""
    def set_election_tick(self, election_tick: int) -> None:
        """"""
    def get_heartbeat_tick(self) -> int:
        """"""
    def set_heartbeat_tick(self, heartbeat_tick: int) -> None:
        """"""
    def get_max_size_per_msg(self) -> int:
        """"""
    def set_max_size_per_msg(self, max_size_per_msg: int) -> None:
        """"""
    def get_max_inflight_msgs(self) -> int:
        """"""
    def set_max_inflight_msgs(self, max_inflight_msgs: int) -> None:
        """"""
    def get_applied(self) -> int:
        """"""
    def set_applied(self, applied: int) -> None:
        """"""
    def get_check_quorum(self) -> bool:
        """"""
    def set_check_quorum(self, check_quorum: bool) -> None:
        """"""
    def get_pre_vote(self) -> bool:
        """"""
    def set_pre_vote(self, pre_vote: bool) -> None:
        """"""
    def get_batch_append(self) -> bool:
        """"""
    def set_batch_append(self, batch_append: bool) -> None:
        """"""
    def get_skip_bcast_commit(self) -> bool:
        """"""
    def set_skip_bcast_commit(self, skip_bcast_commit: bool) -> None:
        """"""
    def get_priority(self) -> int:
        """"""
    def set_priority(self, priority: int) -> None:
        """"""
    def get_max_uncommitted_size(self) -> int:
        """"""
    def set_max_uncommitted_size(self, max_uncommitted_size: int) -> None:
        """"""

class Config_Owner(__Config):
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
        read_only_option: Optional[ReadOnlyOption] = None,
        skip_bcast_commit: Optional[bool] = None,
        batch_append: Optional[bool] = None,
        priority: Optional[int] = None,
        max_uncommitted_size: Optional[int] = None,
        max_committed_size_per_ready: Optional[int] = None,
    ) -> None:
        """
        :param id: The identity of the local raft. It cannot be 0, and must be unique in the group.

        :param election_tick: The identity of the local raft. It cannot be 0, and must be unique in the group.

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
    def make_ref(self) -> Config_Ref: ...
    @staticmethod
    def default() -> Config_Owner: ...

class Config_Ref(__Config):
    """
    Config contains the parameters to start a raft.
    """
