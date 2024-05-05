import random
from copy import deepcopy
from typing import Union
import numpy as np
import networkx as nx
from gufe import LigandNetwork, SmallMoleculeComponent

from .. import network_tools as tools


def get_is_connected(ligand_network: LigandNetwork) -> bool:
    """
    Check if the Ligand Network graph is connected.

    Parameters
    ----------
    ligand_network: LigandNetwork

    Returns
    -------
    bool
        if the Ligand Network graph is connected
    """
    return nx.is_connected(ligand_network.graph.to_undirected())


def get_graph_score(ligand_network: LigandNetwork) -> float:
    """
    Calculate the graph score based on summation of the edge weights.

    Parameters
    ----------
    ligand_network: LigandNetwork
        ligand network, that should return the graph score.

    Returns
    -------
    float
        sum of all edges the graph score
    """
    score = sum([e.annotations["score"] for e in ligand_network.edges])
    return score


def get_number_of_graph_cycles(ligand_network: LigandNetwork, higher_bound: int = 4) -> int:
    """
    Calculate the graph cycles, upt to the upper bound.

    Parameters
    ----------
    ligand_network: LigandNetwork
    higher_bound: int
        largest number of nodes in cycle.

    Returns
    -------
    int
        number of counted cycles.
    """
    graph = nx.DiGraph(ligand_network.graph).to_undirected()
    raw_cycles = [str(sorted(c)) for c in nx.simple_cycles(graph, length_bound=higher_bound)]
    return len(raw_cycles)


def get_node_connectivities(ligand_network: LigandNetwork, normalize: bool = False) -> dict[SmallMoleculeComponent, Union[float, int]]:
    """
    Calculate the connectivities for all nodes in the graph.

    Parameters
    ----------
    ligand_network: LigandNetwork

    Returns
    -------
    dict[int, int]
        node id and corresponding connectivity
    """
    if normalize:
        n_edges = ligand_network.graph.number_of_edges()
        return {n: sum([n in e for e in ligand_network.edges]) / n_edges for n in ligand_network.nodes}
    else:
        return {n: sum([n in e for e in ligand_network.edges]) for n in ligand_network.nodes}


def get_node_scores(ligand_network: LigandNetwork, normalize:bool = True) -> dict[SmallMoleculeComponent, float]:
    """
    Calculate the score of a node, as the sum of the edge scores.
    Parameters
    ----------
    ligand_network: LigandNetwork
    normalize: bool, optional


    Returns
    -------
    dict[int, float]
        node index with value as node score.
    """
    if normalize:
        n_edges = ligand_network.graph.number_of_edges()
        return {n: sum([e.annotations["score"] for e in ligand_network.edges if n in e]) / n_edges for n
                in ligand_network.nodes}
    else:
        return {n: sum([e.annotations["score"] for e in ligand_network.edges if n in e]) for n
                in ligand_network.nodes}


def get_node_number_cycles(ligand_network: LigandNetwork, higher_bound: int = 4) -> dict[int,
int]:
    """
    Get for each node the number of cycles, the node is contained in.

    Parameters
    ----------
    ligand_network: LigandNetwork
    higher_bound:int, optional
        largest number of nodes contained in one searched cycle.

    Returns
    -------
    dict[int, int]
        node index with number of cycles.
    """
    graph = nx.DiGraph(ligand_network.graph).to_undirected()
    # Todo: check if there is a possibility in nx to omit cycles going back over already chosen nodes (1-2-3-2-1)
    # Todo: if possible remove the corresponding code
    raw_cycles = [n for c in nx.simple_cycles(graph, length_bound=higher_bound) for n in c if len(set(c)) == len(c)]
    uni, cou = np.unique(raw_cycles, return_counts=True)

    #Add 0 nodes
    res =  dict(zip(uni, cou))
    for n in graph.nodes:
        if n not in res:
            res[n] = 0
    return res


def get_edge_failure_robustness(ligand_network: LigandNetwork,
                                failure_rate: float = 0.05,
                                nrepeats: int = 100) -> float:
    """
    Estimate the robustness of a LigandNetwork, by removing n edges,
    corresponding to the percentage given by the failure_rate.
    This process is randomly repeated nrepeat times.
    The result is the average of the repeats, between 0 (was always disconnected) and 1 (never was disconnected).


    Parameters
    ----------
    ligand_network: LigandNetwork
    failure_rate: float
        number of failing edges.
    nrepeats: int
        how often shall the process be sampled.

    Returns
    -------
    float
        returns a value between 0 (was always disconnected) and 1 (never was disconnected), as indicator how often a network was disconnected after removing the edges.
    """

    edges = list(ligand_network.edges)
    npics = int(np.round(len(ligand_network.edges) * failure_rate)) if (
            np.round(len(ligand_network.edges) * failure_rate) > 1) else 1

    connected = []
    for _ in range(nrepeats):
        nn = ligand_network
        tedges = deepcopy(edges)
        for _ in range(npics):
            i = random.randrange(0, len(tedges), 1)
            nn = tools.delete_transformation(nn, tedges[i])

            # Remove edge, os it can not be repicked
            tedges.remove(tedges[i])
            if len(tedges) == 0:
                break

        connected.append(get_is_connected(nn))

    r = np.mean(list(map(float, connected)))
    return r
