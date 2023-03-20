from typing import Any, Dict, List, Optional
from interface import Interface
from rraft import (
    Config_Owner,
    ConfState_Owner,
    Logger_Owner,
    Logger_Ref,
    MemStorage_Owner,
    Message_Owner,
    MessageType,
    NO_LIMIT,
    Raft__MemStorage_Owner,
)
import random


# A connection from one node to another.
#
# Used in by `Network` for determining drop rates on messages.
class Connection:
    def __hash__(self) -> int:
        return hash((self.from_, self.to))

    def __eq__(self, other) -> bool:
        return self.from_ == other.from_ and self.to == other.to

    def __init__(self, from_: int, to: int) -> None:
        self.from_ = from_
        self.to = to


# A simulated network for testing.
#
# You can use this to create a test network of Raft nodes.
#
# *Please note:* no actual network calls are made.
class Network:
    def __init__(
        self,
        peers: Dict[int, Interface],
        storage: Dict[int, MemStorage_Owner],
        dropm: Dict[Connection, float],
        ignorem: Dict[MessageType, bool],
    ) -> None:
        self.peers = peers
        self.storage = storage
        self.dropm = dropm
        self.ignorem = ignorem

    # Get a base config. Calling `Network::new` will initialize peers with this config.
    @staticmethod
    def default_config() -> Config_Owner:
        cfg = Config_Owner()
        cfg.set_election_tick(10)
        cfg.set_heartbeat_tick(1)
        cfg.set_max_size_per_msg(NO_LIMIT)
        cfg.set_max_inflight_msgs(256)
        return cfg

    # Initializes a network from `peers`.
    #
    # Nodes will receive their ID based on their index in the vector, starting with 1.
    #
    # A `None` node will be replaced with a new Raft node, and its configuration will
    # be `peers`.
    @staticmethod
    def new(peers: List[Optional[Interface]], l: Logger_Owner | Logger_Ref) -> Any:
        cfg = Network.default_config()
        return Network.new_with_config(peers, cfg, l)

    # Initialize a network from `peers` with explicitly specified `config`.
    @staticmethod
    def new_with_config(
        peers: List[Optional[Interface]],
        config: Config_Owner,
        l: Logger_Owner | Logger_Ref,
    ) -> Any:
        nstorage = {}
        npeers = {}
        peer_addrs = list(range(1, len(peers) + 1))

        for p, id in zip(peers, peer_addrs):
            if p is None:
                cs_owner = ConfState_Owner(peer_addrs, [])
                store_owner = MemStorage_Owner.new_with_conf_state(cs_owner.make_ref())
                nstorage[id] = store_owner.clone()
                cfg = config.clone()
                cfg.set_id(id)

                raft_owner = Raft__MemStorage_Owner(
                    cfg, store_owner.make_ref(), l
                )
                r = Interface(raft_owner)
                npeers[id] = r
            else:
                if p.raft:
                    if raft := p.raft.make_ref():
                        assert (
                            raft.get_id() == id
                        ), f"peer {p.raft.make_ref().get_id()} in peers has a wrong position"

                        store = raft.get_raft_log().get_store().clone()
                        nstorage[id] = store

                npeers[id] = p

        return Network(npeers, nstorage, {}, {})

    # Ignore a given `MessageType`.
    def ignore(self, t: MessageType) -> None:
        self.ignorem[t] = True

    # Filter out messages that should be dropped according to rules set by `ignore` or `drop`.
    def filter_(self, msgs: List[Message_Owner]) -> List[Message_Owner]:
        def should_be_filtered(m: Message_Owner):
            if self.ignorem.get(m.make_ref().get_msg_type()):
                return False

            # hups never go over the network, so don't drop them but panic
            assert (
                m.make_ref().get_msg_type() != MessageType.MsgHup
            ), "unexpected msgHup"

            perc = self.dropm.get(
                Connection(m.make_ref().get_from(), m.make_ref().get_to()), 0.0
            )

            return random.random() >= perc

        return list(filter(should_be_filtered, msgs))

    # Read out all messages generated by peers in the `Network`.
    #
    # Note: messages are not filtered by any configured filters.
    def read_messages(self) -> List[Message_Owner]:
        msgs = []
        for _id, p in self.peers.items():
            msgs.extend(p.read_messages())
        return msgs

    # Instruct the cluster to `step` through the given messages.
    #
    # NOTE: the given `msgs` won't be filtered by its filters.
    def send(self, msgs: List[Message_Owner]) -> None:
        while msgs:
            new_msgs: List[Message_Owner] = []

            for m in msgs:
                p = self.peers.get(m.make_ref().get_to())
                p.step(m.make_ref())
                # The unstable data should be persisted before sending msg.
                p.persist()
                resp = p.read_messages()
                new_msgs.extend(self.filter_(resp))

            msgs = []
            msgs.extend(new_msgs)

    # Filter `msgs` and then instruct the cluster to `step` through the given messages.
    def filter_and_send(self, msgs: List[Message_Owner]) -> None:
        self.send(self.filter_(msgs))

    # Dispatches the given messages to the appropriate peers.
    #
    # Unlike `send` this does not gather and send any responses. It also does not ignore errors.
    def dispatch(self, messages: List[Message_Owner]) -> None:
        for message in self.filter_(messages):
            to = message.make_ref().get_to()
            peer = self.peers[to]
            peer.step(message)

    # Ignore messages from `from` to `to` at `perc` percent chance.
    #
    # `perc` set to `1f64` is a 100% chance, `0f64` is a 0% chance.
    def drop(self, from_: int, to: int, perc: float) -> None:
        self.dropm[Connection(from_, to)] = perc

    # Cut the communication between the two given nodes.
    def cut(self, one: int, other: int) -> None:
        self.drop(one, other, 1.0)
        self.drop(other, one, 1.0)

    # Isolate the given raft to and from all other raft in the cluster.
    def isolate(self, id: int) -> None:
        for i in range(0, len(self.peers)):
            nid = i + 1

            if nid != id:
                self.drop(id, nid, 1.0)
                self.drop(nid, id, 1.0)

    # Recover the cluster conditions applied with `drop` and `ignore`.
    def recover(self) -> None:
        self.dropm = {}
        self.ignorem = {}
