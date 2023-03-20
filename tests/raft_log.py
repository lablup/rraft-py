from typing import List, Optional

from rraft import (
    Entry_Owner,
    MemStorage_Owner,
    RaftLog__MemStorage_Owner,
    Snapshot_Owner,
    SnapshotMetadata_Owner,
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


def test_find_conflict():
    l = default_logger()
    previous_ents = [
        new_entry(1, 1),
        new_entry(2, 2),
        new_entry(3, 3),
    ]

    class Test:
        def __init__(self, ents: List[Entry_Owner], wconflict: int) -> None:
            self.ents = ents
            self.wconflict = wconflict

    tests = [
        # no conflict, empty ent
        Test([], 0),
        Test([], 0),
        # no conflict
        Test([new_entry(1, 1), new_entry(2, 2), new_entry(3, 3)], 0),
        Test([new_entry(2, 2), new_entry(3, 3)], 0),
        Test([new_entry(3, 3)], 0),
        # no conflict, but has new entries
        Test(
            [
                new_entry(1, 1),
                new_entry(2, 2),
                new_entry(3, 3),
                new_entry(4, 4),
                new_entry(5, 4),
            ],
            4,
        ),
        Test([new_entry(2, 2), new_entry(3, 3), new_entry(4, 4), new_entry(5, 4)], 4),
        Test([new_entry(3, 3), new_entry(4, 4), new_entry(5, 4)], 4),
        Test([new_entry(4, 4), new_entry(5, 4)], 4),
        # conflicts with existing entries
        Test([new_entry(1, 4), new_entry(2, 4)], 1),
        Test([new_entry(2, 1), new_entry(3, 4), new_entry(4, 4)], 2),
        Test([new_entry(3, 1), new_entry(4, 2), new_entry(5, 4), new_entry(6, 4)], 3),
    ]

    for i, v in enumerate(tests):
        ents, wconflict = v.ents, v.wconflict
        store = MemStorage_Owner()
        raft_log = RaftLog__MemStorage_Owner(store, l)
        raft_log.append(previous_ents)
        gconflict = raft_log.find_conflict(ents)

        assert gconflict == wconflict, f"#{i}: conflict = {gconflict}, want {wconflict}"


def test_is_up_to_date():
    previous_ents = [
        new_entry(1, 1),
        new_entry(2, 2),
        new_entry(3, 3),
    ]
    store = MemStorage_Owner()
    l = default_logger()
    raft_log = RaftLog__MemStorage_Owner(store, l)
    raft_log.append(previous_ents)

    class Test:
        def __init__(self, last_index: int, term: int, up_to_date: bool) -> None:
            self.last_index = last_index
            self.term = term
            self.up_to_date = up_to_date

    tests = [
        # greater term, ignore lastIndex
        Test(raft_log.last_index() - 1, 4, True),
        Test(raft_log.last_index(), 4, True),
        Test(raft_log.last_index() + 1, 4, True),
        # smaller term, ignore lastIndex
        Test(raft_log.last_index() - 1, 2, False),
        Test(raft_log.last_index(), 2, False),
        Test(raft_log.last_index() + 1, 2, False),
        # equal term, lager lastIndex wins
        Test(raft_log.last_index() - 1, 3, False),
        Test(raft_log.last_index(), 3, True),
        Test(raft_log.last_index() + 1, 3, True),
    ]

    for i, v in enumerate(tests):
        last_index, term, up_to_date = v.last_index, v.term, v.up_to_date
        g_up_to_date = raft_log.is_up_to_date(last_index, term)
        assert (
            g_up_to_date == up_to_date
        ), f"#{i}: up_to_date = {g_up_to_date}, want {up_to_date}"


def test_append():
    l = default_logger()

    class Test:
        def __init__(
            self,
            ents: List[Entry_Owner],
            windex: int,
            wents: List[Entry_Owner],
            wunstable: int,
        ) -> None:
            self.ents = ents
            self.windex = windex
            self.wents = wents
            self.wunstable = wunstable

    previous_ents = [
        new_entry(1, 1),
        new_entry(2, 2),
    ]

    tests = [
        # Test([], 2, [new_entry(1, 1), new_entry(2, 2)], 3),
        Test(
            [new_entry(3, 2)], 3, [new_entry(1, 1), new_entry(2, 2), new_entry(3, 2)], 3
        ),
        # conflicts with index 1
        Test([new_entry(1, 2)], 1, [new_entry(1, 2)], 1),
        # conflicts with index 2
        Test(
            [new_entry(2, 3), new_entry(3, 3)],
            3,
            [new_entry(1, 1), new_entry(2, 3), new_entry(3, 3)],
            2,
        ),
    ]

    for i, v in enumerate(tests):
        ents, windex, wents, wunstable = v.ents, v.windex, v.wents, v.wunstable
        store = MemStorage_Owner()
        store.wl(lambda core: core.append(previous_ents))
        raft_log = RaftLog__MemStorage_Owner(store, l)
        index = raft_log.append(ents)
        assert index == windex, f"#{i}: index = {index}, want {windex}"

        g = raft_log.entries(1, None)
        wents = list(map(lambda x: x, wents))
        # TODO: Handle errors properly here.
        assert g == wents, f"#{i}: logEnts = {g}, want {wents}"


def test_compaction_side_effects():
    last_index = 1000
    unstable_index = 750
    last_term = last_index
    storage = MemStorage_Owner()

    for i in range(1, unstable_index + 1):
        storage.wl(lambda core: core.append([new_entry(i, i)]))

    l = default_logger()
    raft_log = RaftLog__MemStorage_Owner(storage, l)

    for i in range(unstable_index, last_index):
        raft_log.append([new_entry(i + 1, i + 1)])

    assert raft_log.maybe_commit(
        last_index, last_term
    ), "maybe_commit return false"

    offset = 500
    raft_log.get_store().wl(lambda core: core.compact(offset))

    assert last_index == raft_log.last_index()

    for j in range(offset, raft_log.last_index() + 1):
        assert j == raft_log.term(j)
        assert raft_log.match_term(
            j, j
        ), f"match_term({j}) = false, want true"

    unstable_ents = raft_log.unstable_entries()
    assert last_index - unstable_index == len(unstable_ents)
    assert unstable_index + 1 == unstable_ents[0].get_index()

    prev = raft_log.last_index()
    raft_log.append([new_entry(prev + 1, prev + 1)])
    assert unstable_index + 1 == unstable_ents[0].get_index()

    prev = raft_log.last_index()
    ents = raft_log.entries(prev, None)
    assert len(ents) == 1


def test_term_with_unstable_snapshot():
    pass


def test_term():
    pass


def test_log_restore():
    pass


def test_maybe_persist_with_snap():
    pass


def test_unstable_ents():
    pass


def test_has_next_ents_and_next_ents():
    pass


def test_slice():
    pass


def test_log_maybe_append():
    pass


def test_commit_to():
    pass


def test_compaction():
    pass


def test_is_outofbounds():
    pass


def test_restore_snap():
    pass
