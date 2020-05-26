#include "Location.hpp"

#include <algorithm>

#include "Person.hpp"
#include "randomUtils.hpp"

Location::Location(std::string name, int id, float visitProb)
    : m_name(name), m_id(id), m_visitProb(visitProb) {}

HealthDict Location::getHealthSummery() const {
    HealthDict rv;
    for (HealthStatus status : ALL_HEALTH_STATUSES) {
        rv[status] = 0;
    }
    for (const Person* person : m_visitors) {
        rv[person->getHealth()]++;
    }
    return rv;
}

void Location::visit(Person* person) { m_visitors.push_back(person); }

void Location::udpateVisitorsHealth() {

    if (m_visitors.size() == 0) {
        return;
    }

    auto infectedCount = std::count_if(
        m_visitors.begin(), m_visitors.end(), [&](const Person* p) {
            return p->getHealth() == HealthStatus::INFECTED;
        });
    if (infectedCount == 0 || infectedCount == m_visitors.size()) {
        return;
    }
    float infectionProb = static_cast<float>(infectedCount) / m_visitors.size() * GlobalParams::INFECTION_PROB;

    for (Person* person : m_visitors) {
        if (person->getHealth() == HealthStatus::HEALTHY) {
            if (RandomUtils::bernoulli(infectionProb)) {
                person->flagInfection();
            }
        }
    }
}

void Location::clearVisitors() { m_visitors.clear(); }