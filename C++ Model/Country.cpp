#include "Country.hpp"

#include <algorithm>
#include <iomanip>
#include <iostream>
#include <sstream>

Country::~Country() {
    for (Location* location : m_locations) {
        delete location;
    }
}

std::string Country::getStringSummery() const {
    HealthDict healthDict = getHealthSummery();
    std::ostringstream stringStream;
    for (auto& [status, count] : healthDict) {
        stringStream << std::setw(10) << status;
        stringStream << " : " << std::setw(7) << count << std::endl;
    }
    return stringStream.str();
}

HealthDict Country::getHealthSummery() const {
    HealthDict rv;
    for (HealthStatus status : ALL_HEALTH_STATUSES) {
        rv[status] = 0;
    }
    for (const Person person : m_population) {
        rv[person.getHealth()]++;
    }
    rv[HealthStatus::DEAD] = static_cast<unsigned int>(m_morgue.size());
    return rv;
}

void Country::runSimulation(bool log) {

    // TODO: Add time measurement

    HealthDict status = getHealthSummery();
    m_history.push_back(status);

    if (log) {
        std::cout << " Cycle: " << m_globalState.getCycle() << std::endl
                  << getStringSummery() << std::endl;
    }

    while (status[HealthStatus::INFECTED] > 0 &&
           m_globalState.getCycle() < GlobalParams::MAX_CYCLES) {

        // Health update
        for (Person& person : m_population) {
            person.visitLocations();
        }
        for (Location* location : m_locations) {
            location->udpateVisitorsHealth();
        }
        for (Person& person : m_population) {
            person.applyInfection();
            person.updateHealth();
        }

        m_globalState.update();

        // Finish cycle
        for (Person& person : m_population) {
            person.makeNewHistoryRecord();
        }
        for (Location* location : m_locations) {
            location->clearVisitors();
        }

        // Move dead people to the morgue
        // First copy them
        std::copy_if(m_population.begin(), m_population.end(),
                     std::back_inserter(m_morgue), [](const Person& p) {
                         return p.getHealth() == HealthStatus::DEAD;
                     });
        // Now delete them
        m_population.erase(
            std::remove_if(m_population.begin(), m_population.end(),
                           [](const Person& p) {
                               return p.getHealth() == HealthStatus::DEAD;
                           }),
            m_population.end());

        status = getHealthSummery();
        m_history.push_back(status);
        if (log) {
            std::cout << " Cycle: " << m_globalState.getCycle() << std::endl
                      << getStringSummery() << std::endl;
        }
    }

    std::cout << "\n --- Final State --- \n"
              << " Cycle: " << m_globalState.getCycle() << std::endl
              << getStringSummery() << std::endl;
}