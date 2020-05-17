#pragma once

#include <ostream>
#include <vector>

#include "GlobalState.hpp"

class Location;

// NOTE: If adding HealthStatus remember to add it also to ALL_HEALTH_STATUSES!
enum class HealthStatus { HEALTHY, INFECTED, RECOVERED, DEAD };
const std::vector<HealthStatus> ALL_HEALTH_STATUSES{
    HealthStatus::HEALTHY, HealthStatus::INFECTED, HealthStatus::RECOVERED,
    HealthStatus::DEAD};
std::ostream& operator<<(std::ostream& os, const HealthStatus& status);

struct PersonState {
    unsigned int cycle;
    Location* location;
    HealthStatus health;
    PersonState(unsigned int cycle, Location* location, HealthStatus health)
        : cycle(cycle), location(location), health(health) {}
    PersonState(const PersonState& other)
        : cycle(other.cycle), location(other.location), health(other.health) {}
};

class Person {
    friend class CountryGenerator;
  private:
    int m_id;
    std::vector<PersonState> m_history = {};
    bool m_isFlagedInfected = false;
    std::vector<Location*> m_locations;
    GlobalState& m_globalState;

  public:
    Person(int id, Location* home, std::vector<Location*> locations,
           GlobalState& globalState);
    Person(const Person& other);
    ~Person() {}

    Person& operator=(const Person& other);

    void visitLocations();
    void updateHealth();
    void infect();
    void flagInfection();
    void applyInfection();
    void makeNewHistoryRecord();

    const HealthStatus& getHealth() const;
};
