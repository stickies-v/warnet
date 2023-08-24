"""
  Warnet is the top-level class for a simulated network.
"""

import docker
import logging
import networkx
import subprocess
import yaml
from pathlib import Path
from tempfile import mkdtemp
from templates import TEMPLATES
from warnet.tank import Tank
from warnet.addr import (
    DEFAULT_SUBNET
)
from warnet.bitcoin_conf import (
    parse_bitcoin_conf
)

TMPDIR_PREFIX = "warnet_tmp_"

class Warnet:
    def __init__(self):
        self.tmpdir = Path(mkdtemp(prefix=TMPDIR_PREFIX))
        self.docker = docker.from_env()
        self.network = "regtest"
        self.subnet = DEFAULT_SUBNET
        self.graph = None
        self.tanks = []
        logging.info(f"Created Warnet with temp directory {self.tmpdir}")

    @classmethod
    def from_graph_file(cls, graph_file: str):
        self = cls()
        self.graph = networkx.read_graphml(graph_file, node_type=int)
        self.tanks_from_graph()
        return self

    @classmethod
    def from_graph(cls, graph):
        self = cls()
        self.graph = graph
        self.tanks_from_graph()
        return self

    def tanks_from_graph(self):
        for node_id in self.graph.nodes():
            self.tanks.append(Tank.from_graph_node(node_id, self))
        logging.info(f"Imported {len(self.tanks)} tanks from graph")

    def write_bitcoin_confs(self):
        with open(TEMPLATES / "bitcoin.conf", 'r') as file:
            text = file.read()
        base_bitcoin_conf = parse_bitcoin_conf(text)
        for tank in self.tanks:
            tank.write_bitcoin_conf(base_bitcoin_conf)

    def docker_compose_up(self):
        command = ["docker-compose", "-p", "warnet", "up", "-d", "--build"]
        try:
            subprocess.run(command, cwd=self.tmpdir)
        except Exception as e:
            logging.error(f"An error occurred while executing `{command.join(' ')}` in {self.tmpdir}: {e}")

    def write_docker_compose(self):
        compose = {
            "version": "3.8",
            "networks": {
                "warnet": {
                    "name": "warnet",
                    "ipam": {
                        "config": [
                            {"subnet": self.subnet}
                        ]
                    }
                }
            },
            "volumes": {
                "grafana-storage": None
            },
            "services": {}
        }

        # Pass services object to each tank so they can add whatever they need.
        for tank in self.tanks:
            tank.add_services(compose["services"])

        # Add global services
        compose["services"]["prometheus"] = {
            "image": "prom/prometheus:latest",
            "container_name": "prometheus",
            "ports": ["9090:9090"],
            "volumes": [f"{self.tmpdir / 'prometheus.yml'}:/etc/prometheus/prometheus.yml"],
            "command": ["--config.file=/etc/prometheus/prometheus.yml"],
            "networks": [
                "warnet"
            ]
        }
        compose["services"]["node-exporter"] = {
            "image": "prom/node-exporter:latest",
            "container_name": "node-exporter",
            "volumes": [
                "/proc:/host/proc:ro",
                "/sys:/host/sys:ro",
                "/:/rootfs:ro"
            ],
            "command": ["--path.procfs=/host/proc", "--path.sysfs=/host/sys"],
            "networks": [
                "warnet"
            ]
        }
        compose["services"]["grafana"] = {
            "image": "grafana/grafana:latest",
            "container_name": "grafana",
            "ports": ["3000:3000"],
            "volumes": ["grafana-storage:/var/lib/grafana"],
            "networks": [
                "warnet"
            ]
        }

        docker_compose_path = self.tmpdir / "docker-compose.yml"
        try:
            with open(docker_compose_path, "w") as file:
                yaml.dump(compose, file)
            logging.info(f"Wrote file: {docker_compose_path}")
        except Exception as e:
            logging.error(f"An error occurred while writing to {docker_compose_path}: {e}")

    def write_prometheus_config(self):
        config = {
            "global": {
                "scrape_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "scrape_interval": "5s",
                    "static_configs": [{"targets": ["localhost:9090"]}]
                },
                {
                    "job_name": "node-exporter",
                    "scrape_interval": "5s",
                    "static_configs": [{"targets": ["node-exporter:9100"]}]
                },
                {
                    "job_name": "cadvisor",
                    "scrape_interval": "5s",
                    "static_configs": [{"targets": ["cadvisor:8080"]}]
                }
            ]
        }

        for tank in self.tanks:
            tank.add_scrapers(config["scrape_configs"])

        prometheus_path = self.tmpdir / "prometheus.yml"
        try:
            with open(prometheus_path, "w") as file:
                yaml.dump(config, file)
            logging.info(f"Wrote file: {prometheus_path}")
        except Exception as e:
            logging.error(f"An error occurred while writing to {prometheus_path}: {e}")












