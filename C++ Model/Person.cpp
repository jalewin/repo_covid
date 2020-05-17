#include "Person.hpp"

#include <cassert>
#include <stdexcept>

#include "GlobalParams.hpp"
#include "Location.hpp"
#include "randomUtils.hpp"

std::ostream& operator<<(std::ostream& os, const HealthStatus& status) {
    switch (status) {
    case HealthStatus::DEAD:
        os << "DEAD";
        break;
    case HealthStatus::HEALTHY:
        os << "HEALTHY";
        break;
    case HealthStatus::INFECTED:
        os << "INFECTED";
        break;
    case HealthStatus::RECOVERED:
        os << "RECOVERED";
        break;
    default:
        throw std::invalid_argument("Unexpected HealthStatus");
    }
    return os;
}

Person::Person(int id, Location* home, std::vector<Location*> locations,
               GlobalState& globalState)
    : m_id(id), m_locations(locations), m_globalState(globalState) {
    m_history.emplace_back(globalState.getCycle(), home, HealthStatus::HEALTHY);
    m_locations.push_back(home);
}

Person::Person(const Person& other)
    : m_id(other.m_id), m_history(other.m_history),
      m_isFlagedInfected(other.m_isFlagedInfected),
      m_locations(other.m_locations), m_globalState(other.m_globalState) {}

Person& Person::operator=(const Person& other) {
    if (&other == this) {
        return *this;
    }

    m_id = other.m_id;
    m_history = std::vector<PersonState>(other.m_history);
    m_isFlagedInfected = other.m_isFlagedInfected;
    m_locations = std::vector<Location*>(other.m_locations);
    m_globalState = other.m_globalState;
    return *this;
}

void Person::visitLocations() {
    for (Location* location : m_locations) {
        if (RandomUtils::bernoulli(location->getVisitProb())) {
            location->visit(this);
        }
    }
}

void Person::updateHealth() {
    PersonState& myState = m_history.back();
    assert(myState.cycle == m_globalState.getCycle());
    // if true might override changes when applied
    // TODO: maybe change applyInfection() to be private and call it from here?
    assert(!m_isFlagedInfected);
    if (myState.health == HealthStatus::INFECTED) {
        if (RandomUtils::bernoulli(GlobalParams::RECOVERY_PROB)) {
            myState.health = HealthStatus::RECOVERED;
        } else if (RandomUtils::bernoulli(GlobalParams::DEATH_PROB)) {
            myState.health = HealthStatus::DEAD;
        }
    }
}

void Person::infect() {
    PersonState& myState = m_history.back();
    assert(myState.cycle == m_globalState.getCycle());
    myState.health = HealthStatus::INFECTED;
}

void Person::flagInfection() {
    PersonState& myState = m_history.back();
    assert(myState.cycle == m_globalState.getCycle());
    m_isFlagedInfected = true;
}

void Person::applyInfection() {
    PersonState& myState = m_history.back();
    assert(myState.cycle == m_globalState.getCycle());
    if (m_isFlagedInfected) {
        myState.health = HealthStatus::INFECTED;
        m_isFlagedInfected = false;
    }
}

void Person::makeNewHistoryRecord() {
    PersonState& myState = m_history.back();
    assert(myState.cycle < m_globalState.getCycle());
    PersonState newState = PersonState(m_history.back());
    newState.cycle = m_globalState.getCycle();
    m_history.push_back(newState);
}

const HealthStatus& Person::getHealth() const {
    const PersonState& myState = m_history.back();
    return myState.health;
}
