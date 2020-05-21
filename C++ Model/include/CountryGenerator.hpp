#pragma once

#include "Country.hpp"
#include "Location.hpp"
#include <vector>

class CountryGenerator final {
  private:
    int m_uniqueID = 0;
    Country* m_country = nullptr;
    std::vector<Location*> m_WPs = {};

    int getUniqueID() { return m_uniqueID++; }

  public:
    CountryGenerator(Country* country) : m_country(country) {}
    ~CountryGenerator() {}

    void generateWPs(unsigned int count);
    void generateCommunity(unsigned int populationSize, unsigned int numCCs);
    void initInfected(unsigned int count);
};