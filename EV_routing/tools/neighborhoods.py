#TODO improve for better local search

from __future__ import annotations

import random


def swap_customers(route: list[str]) -> list[str]:
    new_route = route[:]

    customer_positions = list(range(1, len(route) - 1))
    i, j = random.sample(customer_positions, 2)

    new_route[i], new_route[j] = new_route[j], new_route[i]
    return new_route



def relocate_customer(route: list[str]) -> list[str]:
    new_route = route[:]

    customer_positions = list(range(1, len(route) - 1))
    i, j = random.sample(customer_positions, 2)

    node = new_route.pop(i)
    new_route.insert(j, node)
    return new_route



def two_opt(route: list[str]) -> list[str]:
    new_route = route[:]

    i, j = sorted(random.sample(range(1, len(route) - 1), 2))
    new_route[i:j+1] = reversed(new_route[i:j+1])

    return new_route



def generate_neighbor(route: list[str]) -> list[str]:
    move = random.choice([swap_customers, relocate_customer, two_opt])
    return move(route)