#TODO make initial solution random

from __future__ import annotations

from typing import List
from tools.data_loader import ProblemData


def build_trivial_initial_solution(data: ProblemData) -> list[str]:
    customer_ids = data.customers["Customer ID"].tolist()
    return ["DEPOT", *customer_ids, "DEPOT"]


def build_nearest_neighbor_solution(data: ProblemData) -> list[str]:
    distance_matrix = data.distance_matrix
    unvisited = set(data.customers["Customer ID"].tolist())

    current = "DEPOT"
    route = ["DEPOT"]

    while unvisited:
        next_customer = min(
            unvisited,
            key=lambda customer: distance_matrix.loc[current, customer]
        )
        route.append(next_customer)
        unvisited.remove(next_customer)
        current = next_customer

    route.append("DEPOT")
    return route