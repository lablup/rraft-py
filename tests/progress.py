from typing import Optional

from rraft import Progress_Owner, ProgressState, INVALID_INDEX


def new_progress(
    state: ProgressState,
    matched: int,
    next_idx: int,
    pending_snapshot: int,
    ins_size: int,
) -> Progress_Owner:
    p = Progress_Owner(next_idx, ins_size)
    p.make_ref().set_state(state)
    p.make_ref().set_matched(matched)
    p.make_ref().set_pending_snapshot(pending_snapshot)
    return p


def test_progress_is_paused():
    class Test:
        def __init__(self, state: ProgressState, paused: bool, w: bool):
            self.state = state
            self.paused = paused
            self.w = w

    tests = [
        Test(ProgressState.Probe, False, False),
        Test(ProgressState.Probe, True, True),
        Test(ProgressState.Replicate, False, False),
        Test(ProgressState.Replicate, True, False),
        Test(ProgressState.Snapshot, False, True),
        Test(ProgressState.Snapshot, True, True),
    ]

    for i, v in enumerate(tests):
        state, paused, w = v.state, v.paused, v.w
        p = new_progress(state, 0, 0, 0, 256)
        p.make_ref().set_paused(paused)
        if p.make_ref().is_paused() != w:
            assert False, f"#{i}: shouldwait = {p.make_ref().is_paused()}, want {w}"


def test_progress_resume():
    p = Progress_Owner(2, 256)
    p.make_ref().set_paused(True)
    p.make_ref().maybe_decr_to(1, 1, INVALID_INDEX)
    assert not p.make_ref().get_paused(), "paused= true, want false"
    p.make_ref().set_paused(True)
    p.make_ref().maybe_update(2)
    assert not p.make_ref().get_paused(), "paused= true, want false"


def test_progress_become_probe():
    matched = 1

    class Test:
        def __init__(self, p: Progress_Owner, wnext: int) -> None:
            self.p = p
            self.wnext = wnext

    tests = [
        Test(new_progress(ProgressState.Replicate, matched, 5, 0, 256), 2),
        # snapshot finish
        Test(new_progress(ProgressState.Snapshot, matched, 5, 10, 256), 11),
        # snapshot failure
        Test(
            new_progress(ProgressState.Probe, matched, 5, 0, 256),
            2,
        ),
    ]

    for i, v in enumerate(tests):
        p, wnext = v.p, v.wnext
        p.make_ref().become_probe()

        if p.make_ref().get_state() != ProgressState.Probe:
            assert (
                False
            ), f"#{i}: state = {p.make_ref().get_state()}, want {ProgressState.Probe}"

        if p.make_ref().get_matched() != matched:
            assert False, f"#{i}: match = {p.make_ref().get_matched()}, want {matched}"

        if p.make_ref().get_next_idx() != wnext:
            assert False, f"#{i}: next = {p.make_ref().get_next_idx()}, want {wnext}"


def test_progress_become_replicate():
    p = new_progress(ProgressState.Probe, 1, 5, 0, 256)
    p.make_ref().become_replicate()

    assert p.make_ref().get_state() == ProgressState.Replicate
    assert p.make_ref().get_matched() == 1
    assert p.make_ref().get_matched() + 1 == p.make_ref().get_next_idx()


def test_progress_become_snapshot():
    p = new_progress(ProgressState.Probe, 1, 5, 0, 256)
    p.make_ref().become_snapshot(10)

    assert p.make_ref().get_state() == ProgressState.Snapshot
    assert p.make_ref().get_matched() == 1
    assert p.make_ref().get_pending_snapshot() == 10


def test_progress_update():
    class Test:
        def __init__(self, update: int, wm: int, wn: int, wok: bool) -> None:
            self.update = update
            self.wm = wm
            self.wn = wn
            self.wok = wok

    prev_m, prev_n = 3, 5

    tests = [
        Test(prev_m - 1, prev_m, prev_n, False),
        Test(prev_m, prev_m, prev_n, False),
        Test(prev_m + 1, prev_m + 1, prev_n, True),
        Test(prev_m + 2, prev_m + 2, prev_n + 1, True),
    ]

    for i, v in enumerate(tests):
        update, wm, wn, wok = v.update, v.wm, v.wn, v.wok
        p = Progress_Owner(prev_n, 256)
        p.make_ref().set_matched(prev_m)
        ok = p.make_ref().maybe_update(update)

        assert ok == wok, f"#{i}: ok = {ok}, want {wok}"
        assert (
            p.make_ref().get_matched() == wm
        ), f"#{i}: match = {p.make_ref().get_matched()}, want {wm}"
        assert (
            p.make_ref().get_next_idx() == wn
        ), f"#{i}: next = {p.make_ref().get_next_idx()}, want {wn}"


def test_progress_maybe_decr():
    class Test:
        def __init__(
            self,
            state: ProgressState,
            m: int,
            n: int,
            rejected: int,
            last: int,
            w: bool,
            wn: int,
        ) -> None:
            self.state = state
            self.m = m
            self.n = n
            self.rejected = rejected
            self.last = last
            self.w = w
            self.wn = wn

    tests = [
        Test(ProgressState.Replicate, 5, 10, 5, 5, False, 10),
        Test(ProgressState.Replicate, 5, 10, 4, 4, False, 10),
        Test(ProgressState.Replicate, 5, 10, 9, 9, True, 6),
        Test(ProgressState.Probe, 0, 0, 0, 0, False, 0),
        Test(ProgressState.Probe, 0, 10, 5, 5, False, 10),
        Test(ProgressState.Probe, 0, 10, 9, 9, True, 9),
        Test(ProgressState.Probe, 0, 2, 1, 1, True, 1),
        Test(ProgressState.Probe, 0, 1, 0, 0, True, 1),
        Test(ProgressState.Probe, 0, 10, 9, 2, True, 3),
        Test(ProgressState.Probe, 0, 10, 9, 0, True, 1),
    ]

    for i, v in enumerate(tests):
        state, m, n, rejected, last, w, wn = (
            v.state,
            v.m,
            v.n,
            v.rejected,
            v.last,
            v.w,
            v.wn,
        )

        p = new_progress(state, m, n, 0, 0)
        if p.make_ref().maybe_decr_to(rejected, last, 0) != w:
            assert False, f"#{i}: maybeDecrTo = {not w}, want {w}"
        if p.make_ref().get_matched() != m:
            assert False, f"#{i}: match = {p.make_ref().get_matched()}, want {m}"
        if p.make_ref().get_next_idx() != wn:
            assert False, f"#{i}: next = {p.make_ref().get_next_idx()}, want {wn}"
