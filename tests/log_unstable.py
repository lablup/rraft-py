from typing import List, Optional
from rraft import (
    Entry_Owner,
    Entry_Ref,
    Snapshot_Owner,
    Snapshot_Ref,
    SnapshotMetadata_Owner,
    Unstable_Owner,
    default_logger,
)


def new_entry(index: int, term: int) -> Entry_Owner:
    e = Entry_Owner()
    e.set_term(term)
    e.set_index(index)
    return e


def new_snapshot(index: int, term: int) -> Snapshot_Owner:
    snap = Snapshot_Owner()
    meta = SnapshotMetadata_Owner()
    meta.set_term(term)
    meta.set_index(index)
    snap.set_metadata(meta)
    return snap


def entry_approximate_size(e: Entry_Owner | Entry_Ref) -> int:
    return len(e.get_data()) + len(e.get_context()) + 12


def test_maybe_first_index():
    class Test:
        def __init__(
            self,
            e: Optional[Entry_Owner | Entry_Ref],
            offset: int,
            snapshot: Optional[Snapshot_Owner | Snapshot_Ref],
            wok: bool,
            windex: int,
        ):
            self.e = e
            self.offset = offset
            self.snapshot = snapshot
            self.wok = wok
            self.windex = windex

    tests = [
        Test(new_entry(5, 1), 5, None, False, 0),
        Test(None, 0, None, False, 0),
        Test(new_entry(5, 1), 5, new_snapshot(4, 1), True, 5),
        Test(None, 5, new_snapshot(4, 1), True, 5),
    ]

    for test in tests:
        e, offset, snapshot, wok, windex = (
            test.e,
            test.offset,
            test.snapshot,
            test.wok,
            test.windex,
        )

        entries_size = 0
        entries = []

        if e:
            entries_size = entry_approximate_size(e)
            entries = [e]

        logger = default_logger()

        u = Unstable_Owner(offset, logger)
        u.set_entries(entries)
        u.set_entries_size(entries_size)
        u.set_snapshot(snapshot)
        # u.set_logger(logger)

        index = u.maybe_first_index()

        if index is None:
            assert wok is False
        else:
            assert index == windex


def test_maybe_term():
    class Test:
        def __init__(
            self,
            e: Optional[Entry_Owner | Entry_Ref],
            offset: int,
            snapshot: Optional[Snapshot_Owner | Snapshot_Ref],
            index: int,
            wok: int,
            wterm: int,
        ):
            self.e = e
            self.offset = offset
            self.snapshot = snapshot
            self.index = index
            self.wok = wok
            self.wterm = wterm

    tests = [
        Test(new_entry(5, 1), 5, None, 5, True, 1),
        Test(new_entry(5, 1), 5, None, 6, False, 0),
        Test(new_entry(5, 1), 5, None, 4, False, 0),
        Test(new_entry(5, 1), 5, new_snapshot(4, 1), 5, True, 1),
        Test(new_entry(5, 1), 5, new_snapshot(4, 1), 6, False, 0),
        # term from snapshot
        Test(new_entry(5, 1), 5, new_snapshot(4, 1), 4, True, 1),
        Test(new_entry(5, 1), 5, new_snapshot(4, 1), 3, False, 0),
        Test(None, 5, new_snapshot(4, 1), 5, False, 0),
        Test(None, 5, new_snapshot(4, 1), 4, True, 1),
        Test(None, 0, None, 5, False, 0),
    ]

    for test in tests:
        e, offset, snapshot, index, wok, wterm = (
            test.e,
            test.offset,
            test.snapshot,
            test.index,
            test.wok,
            test.wterm,
        )

        entries_size = 0
        entries = []

        if e:
            entries_size = entry_approximate_size(e)
            entries = [e]

        logger = default_logger()

        u = Unstable_Owner(offset, logger)
        u.set_entries(entries)
        u.set_entries_size(entries_size)
        u.set_snapshot(snapshot)
        # u.set_logger(logger)
        term = u.maybe_term(index)

        if term is None:
            assert wok is False
        else:
            assert term == wterm


def test_restore():
    logger = default_logger()
    u = Unstable_Owner(5, logger)

    s = new_snapshot(6, 2)
    u.restore(s)

    assert u.get_offset() == s.get_metadata().get_index() + 1
    assert not u.get_entries()
    assert u.get_entries_size() == 0
    assert u.get_snapshot() == s


def test_stable_snapshot_and_entries():
    ents = [new_entry(5, 1), new_entry(5, 2), new_entry(6, 3)]
    entries_size = sum(map(lambda x: entry_approximate_size(x), ents))

    logger = default_logger()
    u = Unstable_Owner(5, logger)
    u.set_entries(ents)
    u.set_entries_size(entries_size)
    u.set_snapshot(new_snapshot(4, 1))
    # u.set_logger(logger)

    assert ents == u.get_entries()
    u.stable_snap(4)
    u.stable_entries(6, 3)
    assert not u.get_entries()
    assert u.get_entries_size() == 0
    assert u.get_offset() == 7


def test_truncate_and_append():
    class Test:
        def __init__(
            self,
            entries: List[Entry_Owner | Entry_Ref],
            offset: int,
            snap: Optional[Snapshot_Owner | Snapshot_Ref],
            to_append: List[Entry_Owner | Entry_Ref],
            woffset: int,
            wentries: List[Entry_Owner | Entry_Ref],
        ):
            self.entries = entries
            self.offset = offset
            self.snap = snap
            self.to_append = to_append
            self.woffset = woffset
            self.wentries = wentries

    tests = [
        # replace to the end
        Test(
            [new_entry(5, 1)],
            5,
            None,
            [new_entry(6, 1), new_entry(7, 1)],
            5,
            [new_entry(5, 1), new_entry(6, 1), new_entry(7, 1)],
        ),
        # replace to unstable entries
        Test(
            [new_entry(5, 1)],
            5,
            None,
            [new_entry(5, 2), new_entry(6, 2)],
            5,
            [new_entry(5, 2), new_entry(6, 2)],
        ),
        Test(
            [new_entry(5, 1)],
            5,
            None,
            [new_entry(4, 2), new_entry(5, 2), new_entry(6, 2)],
            4,
            [new_entry(4, 2), new_entry(5, 2), new_entry(6, 2)],
        ),
        # truncate existing entries and append
        Test(
            [new_entry(5, 1), new_entry(6, 1), new_entry(7, 1)],
            5,
            None,
            [new_entry(6, 2)],
            5,
            [new_entry(5, 1), new_entry(6, 2)],
        ),
        Test(
            [new_entry(5, 1), new_entry(6, 1), new_entry(7, 1)],
            5,
            None,
            [new_entry(7, 2), new_entry(8, 2)],
            5,
            [new_entry(5, 1), new_entry(6, 1), new_entry(7, 2), new_entry(8, 2)],
        ),
    ]

    for test in tests:
        entries, offset, snap, to_append, woffset, wentries = (
            test.entries,
            test.offset,
            test.snap,
            test.to_append,
            test.woffset,
            test.wentries,
        )

        entries_size = sum(map(lambda x: entry_approximate_size(x), entries))

        logger = default_logger()
        u = Unstable_Owner(offset, logger)
        u.set_entries(entries)
        u.set_entries_size(entries_size)
        u.set_offset(offset)
        u.set_snapshot(snap)
        # u.set_logger(logger)

        u.truncate_and_append(list(map(lambda x: x, to_append)))
        assert u.get_offset() == woffset
        assert u.get_entries() == wentries
        entries_size = sum(
            map(
                lambda x: entry_approximate_size(x),
                wentries,
            )
        )
        assert u.get_entries_size() == entries_size
