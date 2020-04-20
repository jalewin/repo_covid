from enum import Enum
import random
import copy


def bernoulli(prob):
    return random.uniform(0, 1) < prob


class GlobalParams:
    INFECTION_PROB = 1
    TRANSITION_PROB = 0.01
    _disease_duration = 20
    RECOVERY_PROB = 1.0 / _disease_duration
    _death_rate = 0.05
    DEATH_PROB = 1 - (1 - _death_rate)**(1 / _disease_duration)
    MAX_CYCLES = 10000

    NUM_LOCATIONS = 100
    AVG_POPULATION = 50
    AVG_NEIGHBORS = 3
    INIT_INFECTED = 10

    AVG_FAMILY_SIZE = 6
    POPULATION_SIZE = 1000


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
        self.history = [
            PersonState(globalState.cycle, home, HealthStatus.HEALTHY)
        ]
        self.locations = locations
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
        health_summary = ", ".join([
            f"{status.name}:{visitors_map[status]}" for status in HealthStatus
        ])
        return f"location: {self.name} ({self.id}) visitors: {len(self.visitors)} {health_summary}"

    def visit(self, person):
        self.visitors.add(person)

    def update_visitors_health(self):
        #print(f"after:  dead:{len(dead_population)} pop:{len(self.population)} morgue:{len(self.country.morgue)}")
        infected_count = sum(
            [p.get_health() is HealthStatus.INFECTED for p in self.visitors])
        if infected_count == 0 or infected_count == len(self.visitors):
            return
        infection_prob = infected_count / (len(self.visitors) -
                                           1) * GlobalParams.INFECTION_PROB
        for person in self.visitors:
            if person.get_health() is HealthStatus.HEALTHY:
                if bernoulli(infection_prob):
                    person.infect()

    # TODO: better name
    def finish_cycle(self):
        self.visitors.clear()


class Country:
    def __init__(self):
        self.locations = []
        self.population = set()
        self.morgue = set()
        self.globalState = GlobalState()
        create_random_country()

    def health_summary(self):
        health_dict = {status: 0 for status in HealthStatus}
        for person in self.population:
            health_dict[person.get_health()] += 1
        health_dict[HealthStatus.DEAD] = len(self.morgue)
        return health_dict

    def __str__(self):
        hh = self.health_summary()
        h_summary = ", ".join([f"{s.name}:{hh[s]}" for s in HealthStatus])
        #return "\n".join([f"cycle:{self.globalState.cycle}", h_summary])
        return "\n".join([f"cycle:{self.globalState.cycle}", h_summary])

    # TODO: delete
    def connect_locations(self, loc_a, loc_b):
        loc_a.neighbors.append(loc_b)
        loc_b.neighbors.append(loc_a)

    # TODO: rewrite
    def create_random_country(self):
        id = 0
        while len(self.population) < GlobalParams.POPULATION_SIZE:
            home = Location('home', id, 1)
            id += 1
            family_size = round(
                random.gammavariate(2, 1 / 2) * GlobalParams.AVG_FAMILY_SIZE)
            for _ in range(family_size):
                pass
                # random person
                # random locations

        n_loc = 0

        ## generat locations and populations
        for ii in range(GlobalParams.NUM_LOCATIONS):
            new_location = Location(ii, self)
            pop = round(
                random.gammavariate(2, 1 / 2) * GlobalParams.AVG_POPULATION)
            for jj in range(pop):
                new_person = Person(jj, ii, self.globalState)
                new_location.visit(new_person)
            self.locations.append(new_location)
        ## connect locations
        prob_connected = GlobalParams.AVG_NEIGHBORS / (
            GlobalParams.NUM_LOCATIONS - 1)
        for ii in range(len(self.locations)):
            for jj in range(ii):
                if bernoulli(prob_connected):
                    self.connect_locations(self.locations[ii],
                                           self.locations[jj])
        ## infect someone in the population
        for _ in range(GlobalParams.INIT_INFECTED):
            ii = random.randrange(0, len(self.locations))
            while len(self.locations[ii].population) == 0:
                ii = random.randrange(0, len(self.locations))
            chosen_person = random.choice(list(self.locations[ii].population))
            chosen_person.history[-1].health = HealthStatus.INFECTED

    # TODO: check loging
    def run_simulation(self):
        self.show_summary()
        status = self.health_summary()

        while status[
                'INFECTED'] > 0 and self.globalState.cycle < GlobalParams.MAX_CYCLES:
            # Health update
            print(status)
            self.globalState.update()

            for person in self.population:
                person.live_one_cycle()
            for location in self.locations:
                location.update_visitors_health()
                location.finish_cycle()
            for person in self.population:
                person.update_health()
                person.make_new_history_record()
            dead_population = [
                p for p in self.population
                if p.get_health() is HealthStatus.DEAD
            ]
            self.morgue.add(dead_population)
            self.population.difference_update(dead_population)

            if self.globalState.cycle % 100 == 0:
                self.show_summary()

            status = self.health_summary()
        print("Final State")
        self.show_summary()

    def show_summary(self):
        print(self)


israel = Country()
israel.run_simulation()