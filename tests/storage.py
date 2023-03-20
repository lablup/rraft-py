from typing import Optional

from rraft import Entry_Owner, MemStorage_Owner, Message_Ref, Snapshot_Owner, SnapshotMetadata_Owner, RaftError, StorageError


def new_entry(index: int, term: int) -> Entry_Owner:
    e = Entry_Owner()
    e.set_term(term)
    e.set_index(index)
    return e


def size_of(m: Message_Ref):
    m.compute_size()


def new_snapshot(index: int, term: int) -> Snapshot_Owner:
    snap = Snapshot_Owner()
    meta = SnapshotMetadata_Owner()
    meta.set_term(term)
    meta.set_index(index)
    snap.set_metadata(meta)
    return snap


def test_storage_term():
    class Test:
        def __init__(self, idx: int, wterm: int) -> None:
            self.idx = idx
            self.wterm = wterm

    ents = [new_entry(3, 3), new_entry(4, 4), new_entry(5, 5)]

    tests = [
        Test(2, RaftError.Store(StorageError.Compacted)),
        Test(3, 3),
        Test(4, 4),
        Test(5, 5),
        Test(6, RaftError.Store(StorageError.Unavailable)),
    ]

    for i, v in enumerate(tests):
        idx, wterm = v.idx, v.wterm
        storage = MemStorage_Owner()
        # TODO: Resolve private fields issue.
        # storage.


def test_storage_entries():
    pass


def test_storage_last_index():
    pass


def test_storage_first_index():
    pass


def test_storage_compact():
    pass


def test_storage_create_snapshot():
    pass


def test_storage_append():
    pass


def test_storage_apply_snapshot():
    pass
