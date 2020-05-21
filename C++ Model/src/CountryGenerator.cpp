#include "CountryGenerator.hpp"

#include "randomUtils.hpp"

void CountryGenerator::generateWPs(unsigned int count) {
    for (size_t i = 0; i < count; i++) {
        WorkPlace* wp = new WorkPlace("WP", getUniqueID());
        m_WPs.push_back(wp);
        m_country->m_locations.push_back(wp);
    }
}

void CountryGenerator::generateCommunity(unsigned int populationSize,
                                         unsigned int numCCs) {

    std::vector<Location*> communityCCs;
    communityCCs.reserve(numCCs);
    for (size_t i = 0; i < numCCs; i++) {
        communityCCs.push_back(new CommunityCenter(
            "CC", getUniqueID(), GlobalParams::CC_VISIT_PROB));
        m_country->m_locations.push_back(communityCCs[i]);
    }
    unsigned int popCount = 0;
    // Create random households (HH)
    while (popCount < populationSize) {
        // Create house
        Location* house = new HouseHold("HH", getUniqueID());
        // Decide how many CCs the house will have
        unsigned int houseCCsCount =
            RandomUtils::randInt(GlobalParams::AVG_HOUSEHOLD_CCs / 2,
                                 GlobalParams::AVG_HOUSEHOLD_CCs * 1.5);
        std::vector<Location*> houseCCs;
        houseCCs.reserve(houseCCsCount);
        for (size_t i = 0; i < houseCCsCount; i++) {
            // Choose random CC
            houseCCs.push_back(
                communityCCs[RandomUtils::randInt(0, communityCCs.size() - 1)]);
        }
        // Decide the size of the house
        unsigned int houseSize =
            std::min(static_cast<unsigned int>(RandomUtils::randInt(
                         GlobalParams::AVG_HOUSEHOLD_SIZE / 2,
                         GlobalParams::AVG_HOUSEHOLD_SIZE * 1.5)),
                     populationSize - popCount);
        std::vector<Person> houseResidents;
        houseResidents.reserve(houseSize);
        for (size_t i = 0; i < houseSize; i++) {
            // Add person to the house with CCs
            houseResidents.emplace_back(getUniqueID(), house, houseCCs,
                                        m_country->m_globalState);
        }
        // Choose random work for some people from the household
        if (m_WPs.size() > 0) {
            unsigned int workingResidentsCount = RandomUtils::randInt(
                GlobalParams::AVG_HOUSEHOLD_WORKING_PEOPLE / 2,
                GlobalParams::AVG_HOUSEHOLD_WORKING_PEOPLE * 1.5);

            for (size_t i = 0; i < workingResidentsCount; i++) {
                Person& randomPerson = houseResidents[RandomUtils::randInt(
                    0, houseResidents.size() - 1)];
                Location* randomWP =
                    m_WPs[RandomUtils::randInt(0, m_WPs.size() - 1)];
                randomPerson.m_locations.push_back(randomWP);
            }
        }

        // Add hosehold to country
        m_country->m_locations.push_back(house);
        // Add household population to country
        m_country->m_population.insert(m_country->m_population.end(),
                                      houseResidents.begin(),
                                      houseResidents.end());

        popCount += houseResidents.size();
    }
}

void CountryGenerator::initInfected(unsigned int count) {
    auto begin = m_country->m_population.begin();
    auto end = m_country->m_population.end();
    size_t left = std::distance(begin, end);
    while (count--) {
        auto r = begin;
        std::advance(r, RandomUtils::randInt(0, left));
        std::swap(*begin, *r);
        begin++;
        left--;
    }
    for (auto it = m_country->m_population.begin(); it != begin; it++) {
        it->infect();
    }
}
