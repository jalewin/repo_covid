from enum import Enum
import random
import copy


def bernoulli(prob):
    return random.uniform(0,1) < prob

class GlobalParams:
    INFECTION_PROB = 1
    TRANSITION_PROB = 0.01
    _disease_duration = 20
    RECOVERY_PROB = 1.0 / _disease_duration
    _death_rate = 0.5
    DEATH_PROB = 1 - (1 - _death_rate)**(1 / _disease_duration)
    MAX_CYCLES = 100

    NUM_LOCATIONS = 100
    AVG_POPULATION = 50
    AVG_NEIGHBORS = 3
    INIT_INFECTED = 10



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
    def __init__(self, cycle, locationID, health):
        self.cycle = cycle
        self.locationID = locationID
        self.health = health

    def __str__(self):
        return f"cycle:{self.cycle} loc:{self.locationID} health:{self.health}"


class Person:
    def __init__(self, id, locationID, globalState):
        self.id = id
        self.history = [
            PersonState(globalState.cycle, locationID, HealthStatus.HEALTHY)
        ]
        self.globalState = globalState

    def __str__(self):
        return f"person:{self.id} last state:({self.history[-1]})"

    def update_internal_health(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        if my_state.health == HealthStatus.INFECTED:
            if bernoulli(GlobalParams.RECOVERY_PROB):
                my_state.health = HealthStatus.RECOVERED
            elif bernoulli(GlobalParams.DEATH_PROB):
                my_state.health = HealthStatus.DEAD

    def update_infected(self):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        my_state.health = HealthStatus.INFECTED

    def update_location(self, locationID):
        my_state = self.history[-1]
        assert my_state.cycle == self.globalState.cycle
        my_state.locationID = locationID

    def make_new_history_record(self):
        my_state = self.history[-1]
        assert self.globalState.cycle > my_state.cycle
        new_state = copy.copy(my_state)
        new_state.cycle = self.globalState.cycle
        self.history.append(new_state)

    def current_health(self):
        return self.history[-1].health


class Location:
    def __init__(self, id, country):
        self.population = set()
        self.neighbors = []
        self.id = id
        self.country = country

    def health_summary(self):
        health_dict = {e.name:0 for e in HealthStatus}
        for p in self.population:
            health_dict[p.current_health().name]+=1
        return health_dict

    def __str__(self):
        pop_map = self.health_summary()
        health_summary = ", ".join([f"{e.name}:{pop_map[e.name]}" for e in HealthStatus])
        neighbors_summary = ", ".join([str(l.id) for l in self.neighbors])
        return f"location:{self.id} population:{len(self.population)} {health_summary} neighbors: {neighbors_summary}"

    def add_person(self, person):
        self.population.add(person)

    def update_population_health(self):
        for person in self.population:
            person.update_internal_health()
        dead_population = set([p for p in self.population if p.current_health() == HealthStatus.DEAD])
        #print(self.health_summary())
        #print(f"before:  dead:{len(dead_population)} pop:{len(self.population)}")
        self.population.difference_update(dead_population)
        self.country.morgue.update(dead_population)
        #print(f"after:  dead:{len(dead_population)} pop:{len(self.population)} morgue:{len(self.country.morgue)}")


        infected_count = sum([p.current_health() == HealthStatus.INFECTED for p in self.population])
        if infected_count == 0 or infected_count ==len(self.population):
            return
        infection_prob = infected_count / (len(self.population) - 1) * GlobalParams.INFECTION_PROB
        for person in self.population:
            if person.current_health() == HealthStatus.HEALTHY:
                if bernoulli(infection_prob):
                    person.update_infected()

    def calc_transitions(self):
        self.preparing_to_move = []
        for person in self.population:
            if len(self.neighbors)>0 and bernoulli(GlobalParams.TRANSITION_PROB):
                destination = self.neighbors[random.randrange(0, len(self.neighbors))]
                self.preparing_to_move.append((person, destination))

    def do_transitions(self):
        for person, destination in self.preparing_to_move:
            destination.add_person(person)
            self.population.remove(person)
            person.update_location(destination)

    def make_new_history_record(self):
        for person in self.population:
            person.make_new_history_record()

class Country:
    def __init__(self):
        self.locations = []
        self.morgue = set()
        self.globalState = GlobalState()
        self.create_random_country()
    
    def health_summary(self):
        health_dict = {e.name:0 for e in HealthStatus}
        for loc in self.locations:
            m = loc.health_summary()
            for key in health_dict.keys():
                health_dict[key] += m[key]
        health_dict['DEAD'] = len(self.morgue)
        return health_dict
    
    def __str__(self):
        hh = self.health_summary()
        h_summary = ", ".join([f"{e.name}:{hh[e.name]}" for e in HealthStatus])
        #return "\n".join([f"cycle:{self.globalState.cycle}", h_summary])
        return "\n".join([f"cycle:{self.globalState.cycle}", h_summary]+[loc.__str__() for loc in self.locations])
    
    def connect_locations(self, loc_a, loc_b):
        loc_a.neighbors.append(loc_b)
        loc_b.neighbors.append(loc_a)

    def create_random_country(self):
        n_loc = 0
        ## generat locations and populations
        for ii in range(GlobalParams.NUM_LOCATIONS):
            new_location = Location(ii ,self)
            pop = round(random.gammavariate(2,1/2) * GlobalParams.AVG_POPULATION)
            for jj in range(pop):
                new_person = Person(jj, ii, self.globalState)
                new_location.add_person(new_person)
            self.locations.append(new_location)
        ## connect locations
        prob_connected = GlobalParams.AVG_NEIGHBORS / (GlobalParams.NUM_LOCATIONS - 1)
        for ii in range(len(self.locations)):
            for jj in range(ii):
                if bernoulli(prob_connected):
                    self.connect_locations(self.locations[ii], self.locations[jj])
        ## infect someone in the population
        for _ in range(GlobalParams.INIT_INFECTED):
            ii = random.randrange(0, len(self.locations))
            while len(self.locations[ii].population)==0:
                ii = random.randrange(0, len(self.locations))
            chosen_person = random.choice(list(self.locations[ii].population))
            chosen_person.history[-1].health = HealthStatus.INFECTED            



    def run_simulation(self):
        self.show_summary()
        while self.globalState.cycle < GlobalParams.MAX_CYCLES:
            # Health update
            self.globalState.update()
            for location in self.locations:
                location.make_new_history_record()
                location.update_population_health()
            self.show_summary()

            # Transition update
            self.globalState.update()
            for location in self.locations:
                location.make_new_history_record()
                location.calc_transitions()
            for location in self.locations:
                location.do_transitions()
            self.show_summary()

    def show_summary(self):
        print(self)



israel = Country()
israel.run_simulation()
