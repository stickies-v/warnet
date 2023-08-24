"""
  Tanks are containerized bitcoind nodes
"""

import logging
from copy import deepcopy
from templates import TEMPLATES
from warnet.bitcoin_conf import (
    dump_bitcoin_conf
)
from warnet.utils import (
    get_architecture
)
from warnet.addr import (
    generate_ipv4_addr
)

CONTAINER_PREFIX_BITCOIND = "tank"
CONTAINER_PREFIX_PROMETHEUS = "prometheus_exporter"

class Tank:
    def __init__(self):
        self.warnet = None
        self.index = None
        self.version = "25.0"
        self.conf = ""
        self.conf_file = None
        self.netem = ""
        self.rpc_port = 18443
        self.rpc_user = "warnet_user"
        self.rpc_password = "2themoon"
        self._suffix = None
        self._ipv4 = None

    @classmethod
    def from_graph_node(cls, index, warnet):
        assert index is not None

        self = cls()
        self.warnet = warnet
        self.index = index
        node = warnet.graph.nodes[index]
        if hasattr(node, "version"):
            self.version = node["version"]
        if hasattr(node, "bitcoin_config"):
            self.conf = node["bitcoin_config"]
        if hasattr(node, "tc_netem"):
            self.netem = node["tc_netem"]
        return self

    def get_suffix(self):
        if self._suffix:
            return self._suffix
        else:
            self._suffix = f"{self.index:06}"
            return self._suffix

    def get_ipv4(self):
        if self._ipv4:
            return self._ipv4
        else:
            self._ipv4 = generate_ipv4_addr(self.warnet.subnet)
            return self._ipv4

    def write_bitcoin_conf(self, base_bitcoin_conf):
        conf = deepcopy(base_bitcoin_conf)
        options = self.conf.split(",")
        for option in options:
            option = option.strip()
            if option:
                if "=" in option:
                    key, value = option.split("=")
                else:
                    key, value = option, "1"
                conf[self.warnet.network].append((key, value))
        conf_file = dump_bitcoin_conf(conf)
        path = self.warnet.tmpdir / f"bitcoin.conf.{self.get_suffix()}"
        logging.debug(f"Wrote file {path}")
        with open(path, 'w') as file:
            file.write(conf_file)
        self.conf_file = path

    def add_services(self, services):
        assert self.index is not None
        assert self.conf_file is not None

        # Setup bitcoind, either release binary or build from source
        if "/" and "#" in self.version:
            # it's a git branch, building step is necessary
            repo, branch = self.version.split("#")
            build = {
                "context": ".",
                "dockerfile": str(TEMPLATES / "Dockerfile"),
                "args": {
                    "REPO": repo,
                    "BRANCH": branch,
                }
            }
        else:
            # assume it's a release version, get the binary
            arch = get_architecture()
            build = {
                "context": ".",
                "dockerfile": str(TEMPLATES / "Dockerfile"),
                "args": {
                    "ARCH": arch,
                    "BITCOIN_VERSION": self.version,
                    "BITCOIN_URL": f"https://bitcoincore.org/bin/bitcoin-core-{self.version}/bitcoin-{self.version}-{arch}-linux-gnu.tar.gz"
                }
            }

        # Add the bitcoind service
        suf = self.get_suffix()
        bitcoind_name = f"{CONTAINER_PREFIX_BITCOIND}_{suf}"
        services[bitcoind_name] = {
            "container_name": bitcoind_name,

            "build": build,
            "volumes": [
                f"{self.conf_file}:/root/.bitcoin/bitcoin.conf"
            ],
            "networks": {
                "warnet": {
                    "ipv4_address": f"{self.get_ipv4()}",
                }
            },
            "privileged": True,
        }

        # Add the prometheus data exporter in a neighboring container
        exporter_name = f"{CONTAINER_PREFIX_PROMETHEUS}_{suf}"
        services[exporter_name] = {
            "image": "jvstein/bitcoin-prometheus-exporter",
            "container_name": exporter_name,
            "environment": {
                "BITCOIN_RPC_HOST": bitcoind_name,
                "BITCOIN_RPC_PORT": self.rpc_port,
                "BITCOIN_RPC_USER": self.rpc_password,
                "BITCOIN_RPC_PASSWORD": self.rpc_password,
            },
            "ports": [f"{8335 + self.index}:9332"],
            "networks": [
                "warnet"
            ]
        }

    def add_scrapers(self, scrapers):
        suf = self.get_suffix()
        bitcoind_name = f"{CONTAINER_PREFIX_BITCOIND}_{suf}"
        exporter_name = f"{CONTAINER_PREFIX_PROMETHEUS}_{suf}"
        scrapers.append({
            "job_name": bitcoind_name,
            "scrape_interval": "5s",
            "static_configs": [
                {"targets": [f"{exporter_name}:9332"]}
            ]
        })

