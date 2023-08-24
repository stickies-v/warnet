import logging
from templates import TEMPLATES
from .warnet import Warnet

BITCOIN_GRAPH_FILE = TEMPLATES / "example.graphml"

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

def main():
    wn = Warnet.from_graph_file(BITCOIN_GRAPH_FILE)
    wn.write_bitcoin_confs()
    wn.write_docker_compose()
    wn.write_prometheus_config()
    wn.docker_compose_up()
    # wn.apply_network_conditions
    # wn.connect_edges()
    exit()

if __name__ == "__main__":
    main()
