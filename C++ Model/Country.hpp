#pragma once

#include <string>
#include <vector>

#include "GlobalState.hpp"
#include "Location.hpp"
#include "Person.hpp"

class Country {
    friend class CountryGenerator;

  private:
    std::vector<Location*> m_locations = {};
    std::vector<Person> m_population = {};
    std::vector<Person> m_morgue = {};
    GlobalState m_globalState = {};
    std::vector<HealthDict> m_history = {};

    HealthDict getHealthSummery() const;
    std::string getStringSummery() const;

  public:
    Country() {}
    ~Country();

    void runSimulation(bool log);

    int populationSize() const { return m_population.size(); }
    int locationsCount() const { return m_locations.size(); }
};