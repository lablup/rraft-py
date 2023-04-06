import pytest
from rraft import (
    ConfState_Owner,
    Logger_Ref,
    MemStorage_Owner,
    Config_Owner,
    Raft__MemStorage_Owner,
    default_logger,
)


def new_storage(voters: int, learners: int) -> MemStorage_Owner:
    cc = ConfState_Owner.default()
    for i in range(1, voters + 1):
        cc.set_voters([*cc.get_voters(), i])
    for i in range(1, learners + 1):
        cc.set_learners([*cc.get_learners(), voters + i])

    return MemStorage_Owner.new_with_conf_state(cc)


def quick_raft(storage: MemStorage_Owner, logger: Logger_Ref):
    id = 1
    config = Config_Owner(id)
    return Raft__MemStorage_Owner(config, storage, logger)


@pytest.mark.benchmark(group="Raft", warmup=True)
def test_raft_creation1(benchmark):
    logger = default_logger()
    storage = new_storage(0, 0)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="Raft", warmup=True)
def test_raft_creation2(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="Raft", warmup=True)
def test_raft_creation3(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="Raft", warmup=True)
def test_raft_creation4(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign1_1(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign1_2(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign1_3(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign2_1(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign2_2(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign2_3(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign3_1(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign3_2(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="Raft")
def test_raft_campaign3_3(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)
