from enum import Enum
import random
import copy
from rpy2 import robjects as ro
from rpy2.robjects.packages import importr

networkD3 = importr("networkD3")


def bernoulli(prob):
    return random.uniform(0, 1) < prob


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

    def __str__(self):
        return f"cycle:{self.cycle} loc:{self.location} health:{self.health}"


class Person:
    # TODO: fix not relateing to home, maybe remove home and use only locations?
    def __init__(self, id, home, locations, globalState):
        self.id = id
        self.history = [PersonState(globalState.cycle, home, HealthStatus.HEALTHY)]
        self.locations = copy.deepcopy(locations)
        self.locations.append(home)
        self.globalState = globalState

    def __str__(self):
        return f"person:{self.id} last state:({self.history[-1]})"

    # TODO: change name?
    def live_one_cycle(self):
        for location in self.locations:
            if bernoulli(location.visit_prob):
                location.visit(self)

    def update_health(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        if my_state.health is HealthStatus.INFECTED:
            if bernoulli(GlobalParams.RECOVERY_PROB):
                my_state.health = HealthStatus.RECOVERED
            elif bernoulli(GlobalParams.DEATH_PROB):
                my_state.health = HealthStatus.DEAD

    def infect(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        my_state.health = HealthStatus.INFECTED

    def make_new_history_record(self):
        my_state = self.history[-1]
        assert self.globalState.cycle > my_state.cycle
        new_state = copy.copy(my_state)
        new_state.cycle = self.globalState.cycle
        self.history.append(new_state)

    def get_health(self):
        return self.history[-1].health


class Location:
    def __init__(self, name, loc_id, visit_prob):
        self.visitors = set()
        self.name = name
        self.id = loc_id
        self.visit_prob = visit_prob

    # TODO: rethink if needed
    def health_summary(self):
        health_dict = {status: 0 for status in HealthStatus}
        for person in self.visitors:
            health_dict[person.get_health()] += 1
        return health_dict

    # TODO: rethink if needed
    def __str__(self):
        visitors_map = self.health_summary()
        health_summary = ", ".join(
            [f"{status.name}:{visitors_map[status]}" for status in HealthStatus]
        )
        return f"location: {self.name} ({self.id}) visitors: {len(self.visitors)} {health_summary}"

    def visit(self, person):
        self.visitors.add(person)

    def update_visitors_health(self):
        # print(f"after:  dead:{len(dead_population)} pop:{len(self.population)} morgue:{len(self.country.morgue)}")
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
    def __init__(self, name, loc_id, visit_prob):
        super().__init__(name, loc_id, visit_prob)


class WorkPlace(Location):
    def __init__(self, name, loc_id):
        super().__init__(name, loc_id, GlobalParams.WP_VISIT_PROB)


class Country:
    def __init__(self):
        self.locations = []
        self.population = set()
        self.morgue = set()
        self.globalState = GlobalState()

    def health_summary(self):
        health_dict = {status: 0 for status in HealthStatus}
        for person in self.population:
            health_dict[person.get_health()] += 1
        health_dict[HealthStatus.DEAD] = len(self.morgue)
        return health_dict

    def __str__(self):
        return "\n".join([f"cycle: {self.globalState.cycle}", self.health_summary()])

    # TODO: check loging
    def run_simulation(self):
        self.show_summary()
        status = self.health_summary()
        while (
            status[HealthStatus.INFECTED] > 0
            and self.globalState.cycle < GlobalParams.MAX_CYCLES
        ):
            # Health update
            print(status)
            self.globalState.update()

            for person in self.population:
                person.live_one_cycle()
            for location in self.locations:
                location.update_visitors_health()
                location.clear_visitors()
            for person in self.population:
                person.update_health()
                person.make_new_history_record()
            dead_population = [
                p for p in self.population if p.get_health() is HealthStatus.DEAD
            ]
            self.morgue.add(dead_population)
            self.population.difference_update(dead_population)

            status = self.health_summary()
        print("Final State")
        self.show_summary()

    def get_graph_connections(self):
        connections = []
        for p in self.population:
            for loc in p.locations:
                connections.append((f"p ({p.id})", f"{loc.name} ({loc.id})"))
        return connections

    def show_graph(self):
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
            linkDistance=60,  # distance between node. Increase this value to have more space between nodes
            charge=-20,  # numeric value indicating either the strength of the node repulsion (negative value) or attraction (positive value)
            fontSize=10,  # size of the node names
            fontFamily="serif",  # font og node names
            linkColour="#666",  # colour of edges, MUST be a common colour for the whole graph
            nodeColour="#69b3a2",  # colour of nodes, MUST be a common colour for the whole graph
            opacity=0.9,  # opacity of nodes. 0=transparent. 1=no transparency
            zoom=True,  # Can you zoom on the figure?
        )

        print(graph)


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
        while pop_count < population_size:
            # Create random household (HH)
            house = HouseHold("HH", self._get_new_id())
            num_CCs = random.randint(
                int(GlobalParams.AVG_HOUSEHOLD_CCs / 2),
                int(GlobalParams.AVG_HOUSEHOLD_CCs * 1.5),
            )
            # Choose random community centers (CC)
            # NOTE: random.choices can choose the same element couple of times
            house_CCs = random.choices(CCs, k=min(num_CCs, len(CCs)))
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
        infected = random.choices(self.country.population, k=infected_count)
        for p in infected:
            p.infect()

    def get_country(self):
        return self.country

    def _get_new_id(self):
        self.loc_unique_id += 1
        return self.loc_unique_id


def create_random_country():
    cg = CountryGenerator()
    n_work = random.randint(2, 8)
    print(f" {n_work} works")
    cg.generateWorkPlaces(n_work)
    n_comm = random.randint(3, 10)
    print(f" {n_comm} communities")
    for i in range(n_comm):
        pop_size = random.randint(100, 300)
        n_CCs = random.randint(3, 7)
        print(f" Community {i + 1}, population: {pop_size}, community centers: {n_CCs}")
        cg.generateCommunity(pop_size, n_CCs)

    cg.infect(GlobalParams.INIT_INFECTED)
    country = cg.get_country()
    return country


c = create_random_country()
c.show_graph()
#print("press enter to exit")
#input()
