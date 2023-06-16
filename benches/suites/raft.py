import pytest
from rraft import (
    ConfState,
    Logger_Ref,
    MemStorage,
    Config,
    InMemoryRaft,
    default_logger,
)


def new_storage(voters: int, learners: int) -> MemStorage:
    cc = ConfState.default()
    for i in range(1, voters + 1):
        cc.set_voters([*cc.get_voters(), i])
    for i in range(1, learners + 1):
        cc.set_learners([*cc.get_learners(), voters + i])

    return MemStorage.new_with_conf_state(cc)


def quick_raft(storage: MemStorage, logger: Logger_Ref):
    id = 1
    config = Config(id)
    return InMemoryRaft(config, storage, logger)


@pytest.mark.benchmark(group="raft-creation", warmup=True)
def test_raft_creation_0_0(benchmark):
    logger = default_logger()
    storage = new_storage(0, 0)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="raft-creation", warmup=True)
def test_raft_creation_3_1(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="raft-creation", warmup=True)
def test_raft_creation_5_2(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)
    benchmark(quick_raft, storage, logger)


@pytest.mark.benchmark(group="raft-creation", warmup=True)
def test_raft_creation_7_3(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)
    benchmark(quick_raft, storage, logger)


# ---


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__3_1_CampaignPreElection(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__3_1_CampaignElection(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__3_1_CampaignTransfer(benchmark):
    logger = default_logger()
    storage = new_storage(3, 1)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__5_2_CampaignPreElection(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__5_2_CampaignElection(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__5_2_CampaignTransfer(benchmark):
    logger = default_logger()
    storage = new_storage(5, 2)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__7_3_CampaignPreElection(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignPreElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__7_3_CampaignElection(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignElection")

    benchmark(bench, storage, logger)


@pytest.mark.benchmark(group="raft-campaign", warmup=True)
def test_raft_campaign__7_3_CampaignTransfer(benchmark):
    logger = default_logger()
    storage = new_storage(7, 3)

    def bench(storage, logger):
        raft = quick_raft(storage, logger)
        raft.campaign("CampaignTransfer")

    benchmark(bench, storage, logger)
