#include "Country.hpp"

#include <algorithm>
#include <chrono>
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
    for (const Person& person : m_population) {
        rv[person.getHealth()]++;
    }
    return rv;
}

// Static
std::string Country::toStringSummery(const HealthDict& healthDict) {
    std::ostringstream stringStream;
    for (auto& [status, count] : healthDict) {
        stringStream << std::setw(10) << status;
        stringStream << " : " << std::setw(7) << count << std::endl;
    }
    return stringStream.str();
}

void Country::runSimulation(bool log) {

    // TODO: Add time measurement

    auto beginTime = std::chrono::steady_clock::now();

    HealthDict status = getHealthSummery();
    m_history.push_back(status);

    if (log) {
        std::cout << " Cycle: " << m_globalState.getCycle() << std::endl
                  << toStringSummery(status) << std::endl;
    }

    while (status[HealthStatus::INFECTED] > 0 &&
           m_globalState.getCycle() < GlobalParams::MAX_CYCLES) {

        // Health update
        for (Person& person : m_population) {
            if (person.getHealth() != HealthStatus::DEAD) {
                person.visitLocations();
            }
        }
        for (Location* location : m_locations) {
            location->udpateVisitorsHealth();
        }
        for (Person& person : m_population) {
            if (person.getHealth() != HealthStatus::DEAD) {
                person.applyInfection();
                person.updateHealth();
            }
        }

        m_globalState.update();

        // Finish cycle
        for (Person& person : m_population) {
            if (person.getHealth() != HealthStatus::DEAD) {
                person.makeNewHistoryRecord();
            }
        }
        for (Location* location : m_locations) {
            location->clearVisitors();
        }

        status = getHealthSummery();
        m_history.push_back(status);
        if (log) {
            std::cout << " Cycle: " << m_globalState.getCycle() << std::endl
                      << toStringSummery(status) << std::endl;
        }
    }

    auto endTime = std::chrono::steady_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
                        endTime - beginTime)
                        .count() /
                    1000.f;
    std::cout << " Total time: " << duration << "s" << std::endl;
    std::cout << " " << m_globalState.getCycle() / duration
              << " Cycles per second" << std::endl;
    std::cout << " "
              << m_globalState.getCycle() / duration * m_population.size()
              << " People per second" << std::endl;

    std::cout << "\n --- Final State --- \n"
              << " Cycle: " << m_globalState.getCycle() << std::endl
              << toStringSummery(status) << std::endl;
}