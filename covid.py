from enum import Enum
import random
import copy
from rpy2 import robjects as ro
from rpy2.robjects.packages import importr
import matplotlib.pyplot as plt
import numpy as np

from timeit import default_timer as timer


networkD3 = importr("networkD3")


class RandomGenerator:
    def __init__(self, batch_size: int):
        self._batch_size = batch_size
        self._generate_batch()
        self._prev_idx = -1

    def next(self) -> float:
        """Return random floats in the half-open interval [0.0, 1.0)."""
        self._prev_idx += 1
        if self._prev_idx >= self._batch_size:
            self._generate_batch()
            self._prev_idx = 0
        return self._randoms[self._prev_idx]

    def bernoulli(self, prob: float) -> bool:
        return self.next() < prob

    def _generate_batch(self):
        self._randoms = np.random.random(size=self._batch_size)


def bernoulli(prob):
    return random.uniform(0, 1) < prob


fast_random = RandomGenerator(10 ** 7)
bernoulli = fast_random.bernoulli


class GlobalParams:
    INFECTION_PROB = 1
    TRANSITION_PROB = 0.01
    _disease_duration = 20
    RECOVERY_PROB = 1.0 / _disease_duration
    _death_rate = 0.05
    DEATH_PROB = 1 - (1 - _death_rate) ** (1 / _disease_duration)
    MAX_CYCLES = 10000

    NUM_LOCATIONS = 100
    AVG_POPULATION = 50
    AVG_NEIGHBORS = 3
    INIT_INFECTED = 10

    AVG_HOUSEHOLD_SIZE = 6
    AVG_HOUSEHOLD_CCs = 2
    AVS_HOUSEHOLD_WORKING_PEOPLE = 1.7
    POPULATION_SIZE = 1000
    WP_VISIT_PROB = 5 / 7
    CC_VISIT_PROB = 1 / 10


class GlobalState:
    def __init__(self):
        self.cycle = 0

    def update(self):
        self.cycle += 1


class HealthStatus(Enum):
    HEALTHY = 0
    INFECTED = 1
    RECOVERED = 2
    DEAD = 3


class PersonState:
    def __init__(self, cycle, location, health):
        self.cycle = cycle
        self.location = location
        self.health = health

    def __copy__(self):
        return PersonState(self.cycle, self.location, self.health)

    def __str__(self):
        return f"cycle:{self.cycle} loc:{self.location} health:{self.health}"

    def __repr__(self):
        return f"({self.cycle}, {self.location}, {self.health})"


class Person:
    def __init__(self, id, home, locations, globalState):
        self.id = id
        self.history = [PersonState(globalState.cycle, home, HealthStatus.HEALTHY)]
        self.next_health = self.history[-1].health
        # NOTE: performance issue
        self.locations = copy.copy(locations)
        self.locations.append(home)
        self.globalState = globalState

    def __str__(self):
        return f"person:{self.id} last state:({self.history[-1]})"

    # TODO: change name?
    def visit_locations(self):
        for location in self.locations:
            if bernoulli(location.visit_prob):
                location.visit(self)

    def update_current_health(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        if my_state.health is HealthStatus.INFECTED:
            if bernoulli(GlobalParams.RECOVERY_PROB):
                my_state.health = HealthStatus.RECOVERED
            elif bernoulli(GlobalParams.DEATH_PROB):
                my_state.health = HealthStatus.DEAD

    # changes will apply only after calling advance_state()
    def infect(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        self.next_health = HealthStatus.INFECTED

    # apply health changes
    def advance_health_state(self):
        my_state = self.history[-1]
        assert self.globalState.cycle == my_state.cycle
        if self.next_health is not None:
            my_state.health = self.next_health
            self.next_health = None

    def make_new_history_record(self):
        my_state = self.history[-1]
        assert self.globalState.cycle > my_state.cycle
        new_state = copy.copy(my_state)
        new_state.cycle = self.globalState.cycle
        self.history.append(new_state)

    def get_health(self):
        my_state = self.history[-1]
        return my_state.health

    # changes will apply immediately
    def set_health(self, status):
        my_state = self.history[-1]
        self.next_health = my_state.health = status


class Location:
    def __init__(self, name, loc_id, visit_prob):
        self.visitors = set()
        self.name = name
        self.id = loc_id
        self.visit_prob = visit_prob

    def health_summary(self):
        health_dict = {status: 0 for status in HealthStatus}
        for person in self.visitors:
            health_dict[person.get_health()] += 1
        return health_dict

    def __str__(self):
        visitors_map = self.health_summary()
        health_summary = ", ".join(
            [f"{status.name}:{visitors_map[status]}" for status in HealthStatus]
        )
        return f"location: {self.name} ({self.id}) visitors: {len(self.visitors)} {health_summary}"

    def visit(self, person):
        self.visitors.add(person)

    def update_visitors_health(self):
        infected_count = sum(
            [p.get_health() is HealthStatus.INFECTED for p in self.visitors]
        )
        if infected_count == 0 or infected_count == len(self.visitors):
            return
        infection_prob = (
            infected_count / (len(self.visitors) - 1) * GlobalParams.INFECTION_PROB
        )
        for person in self.visitors:
            if person.get_health() is HealthStatus.HEALTHY:
                if bernoulli(infection_prob):
                    person.infect()

    # TODO: better name
    def clear_visitors(self):
        self.visitors.clear()


class HouseHold(Location):
    def __init__(self, name, loc_id):
        super().__init__(name, loc_id, 1)


class CommunityCenter(Location):
    pass


class PublicTransportation(Location):
    pass


class WorkPlace(Location):
    def __init__(self, name, loc_id):
        super().__init__(name, loc_id, GlobalParams.WP_VISIT_PROB)


class Country:
    def __init__(self):
        self.locations = []
        self.population = set()
        self.morgue = set()
        self.globalState = GlobalState()
        self.history = []

    def health_summary(self):
        health_dict = {status: 0 for status in HealthStatus}
        for person in self.population:
            health_dict[person.get_health()] += 1
        health_dict[HealthStatus.DEAD] = len(self.morgue)
        return health_dict

    def __str__(self):
        health_dict = self.health_summary()
        readable_dict = [f"{s.name:<10}: {health_dict[s]:<10}" for s in HealthStatus]
        return "\n".join([f"Cycle: {self.globalState.cycle}"] + readable_dict)

    def run_simulation(self, log=False):
        begin_time = timer()
        status = self.health_summary()
        self.history.append(status)
        if log:
            print(self)
        while (
            status[HealthStatus.INFECTED] > 0
            and self.globalState.cycle < GlobalParams.MAX_CYCLES
        ):
            # Health update
            for person in self.population:
                person.visit_locations()
            for location in self.locations:
                location.update_visitors_health()
            for person in self.population:
                person.advance_health_state()
                person.update_current_health()

            self.globalState.update()

            # Finish cycle
            for person in self.population:
                person.make_new_history_record()
            for location in self.locations:
                location.clear_visitors()

            dead_population = [
                p for p in self.population if p.get_health() is HealthStatus.DEAD
            ]
            self.morgue.update(dead_population)
            self.population.difference_update(dead_population)
            status = self.health_summary()
            self.history.append(status)
            if log:
                print(self)

        elapsed_time = timer() - begin_time
        print(f" Total time: {elapsed_time:.4}s")
        print(f"{self.globalState.cycle / elapsed_time:.4} Cycles per second")
        print(
            f"{self.globalState.cycle / elapsed_time * (len(self.population) + len(self.morgue)):.4} Peoples per second"
        )
        print("\n--- Final State ---")
        print(self)

    def get_graph_connections(self):
        connections = []
        for p in self.population:
            for loc in p.locations:
                connections.append((f"p ({p.id})", f"{loc.name} ({loc.id})"))
        return connections

    def show_community_graph(self):
        connections = self.get_graph_connections()
        source = [conn[0] for conn in connections]
        target = [conn[1] for conn in connections]
        graph_data_frame = ro.DataFrame(
            {"source": ro.StrVector(source), "target": ro.StrVector(target),}
        )
        graph = networkD3.simpleNetwork(
            graph_data_frame,
            Source=1,  # column number of source
            Target=2,  # column number of target
            height=880,  # height of frame area in pixels
            width=1980,
            linkDistance=30,  # distance between node. Increase this value to have more space between nodes
            charge=-60,  # numeric value indicating either the strength of the node repulsion (negative value) or attraction (positive value)
            fontSize=10,  # size of the node names
            fontFamily="serif",  # font og node names
            linkColour="#666",  # colour of edges, MUST be a common colour for the whole graph
            nodeColour="#69b3a2",  # colour of nodes, MUST be a common colour for the whole graph
            opacity=0.9,  # opacity of nodes. 0=transparent. 1=no transparency
            zoom=True,  # Can you zoom on the figure?
        )

        print(graph)

    def show_status_graph(self):
        time = list(range(self.globalState.cycle + 1))
        healthy = [record[HealthStatus.HEALTHY] for record in self.history]
        infected = [record[HealthStatus.INFECTED] for record in self.history]
        recovered = [record[HealthStatus.RECOVERED] for record in self.history]
        dead = [record[HealthStatus.DEAD] for record in self.history]
        plt.plot(time, healthy, label="Healthy")
        plt.plot(time, infected, label="Infected")
        plt.plot(time, recovered, label="Recovered")
        plt.plot(time, dead, label="Dead")

        plt.xlabel("Days (cycles)")
        plt.ylabel("Population")
        plt.title("COVID-19 simulation")
        plt.legend()

        plt.show()


# TODO: add public transportation
class CountryGenerator:
    def __init__(self):
        self.loc_unique_id = 0
        self.country = Country()
        self.WPs = []

    def generateWorkPlaces(self, count):
        for _ in range(count):
            working_place = WorkPlace("WP", self._get_new_id())
            self.WPs.append(working_place)
            self.country.locations.append(working_place)

    # TODO: seprate the creation of communities from the creation of all of the social connections
    # TODO: think on better random distributions for all random variables
    def generateCommunity(self, population_size, community_center_count):

        CCs = []

        for _ in range(community_center_count):
            community_center = CommunityCenter(
                "CC", self._get_new_id(), GlobalParams.CC_VISIT_PROB
            )
            CCs.append(community_center)
            self.country.locations.append(community_center)

        pop_count = 0
        # Create random households (HH)
        while pop_count < population_size:
            house = HouseHold("HH", self._get_new_id())
            num_CCs = random.randint(
                int(GlobalParams.AVG_HOUSEHOLD_CCs / 2),
                int(GlobalParams.AVG_HOUSEHOLD_CCs * 1.5),
            )
            # Choose random community centers (CC)
            # NOTE: random.choices can choose the same element couple of times
            house_CCs = random.choices(CCs, k=num_CCs)
            house_size = min(
                random.randint(
                    int(GlobalParams.AVG_HOUSEHOLD_SIZE / 2),
                    int(GlobalParams.AVG_HOUSEHOLD_SIZE * 1.5),
                ),
                population_size - pop_count,
            )
            house_residents = []
            for _ in range(house_size):
                house_residents.append(
                    Person(
                        self._get_new_id(), house, house_CCs, self.country.globalState
                    )
                )

            if len(self.WPs) > 0:
                # Choose random work for some people from the household
                working_people_count = random.randint(
                    int(GlobalParams.AVS_HOUSEHOLD_WORKING_PEOPLE / 2),
                    int(GlobalParams.AVS_HOUSEHOLD_WORKING_PEOPLE * 1.5),
                )
                working_people = random.choices(
                    house_residents, k=min(working_people_count, len(house_residents))
                )
                for p in working_people:
                    p.locations.append(random.choice(self.WPs))

            self.country.locations.append(house)
            self.country.population.update(house_residents)

            pop_count += len(house_residents)

    def infect(self, infected_count):
        # random.choices does not supports sets
        infected = random.choices(tuple(self.country.population), k=infected_count)
        for p in infected:
            p.set_health(HealthStatus.INFECTED)

    def get_country(self):
        return self.country

    def _get_new_id(self):
        self.loc_unique_id += 1
        return self.loc_unique_id


def create_random_country(factor=1):
    cg = CountryGenerator()
    n_work = random.randint(2 * factor, 8 * factor)
    print(f" {n_work} works")
    cg.generateWorkPlaces(n_work)
    n_comm = random.randint(3 * factor, 10 * factor)
    print(f" {n_comm} communities")
    for i in range(n_comm):
        pop_size = random.randint(100 * factor, 300 * factor)
        n_CCs = random.randint(3 * factor, 7 * factor)
        print(f" Community {i + 1}, population: {pop_size}, community centers: {n_CCs}")
        cg.generateCommunity(pop_size, n_CCs)

    cg.infect(GlobalParams.INIT_INFECTED)
    country = cg.get_country()
    return country


def get_country():
    cg = CountryGenerator()
    cg.generateWorkPlaces(3)
    for _ in range(10):
        cg.generateCommunity(500, 3)
    cg.infect(10)
    return cg.get_country()


c = create_random_country(5)
# c.show_community_graph()
c.run_simulation()
c.show_status_graph()
# print("press enter to exit")
# input()

# TODO: Check performance of:
#   20.53   * visit_locations (111)
#   17.86   * make_new_history_record (139)
#   13.50   * bernoulli (29)
#   07.98   * __copy__ (87)
#   07.85   * health_summery (224)
#   06.93   * update_visitors_health(179)