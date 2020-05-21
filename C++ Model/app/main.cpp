#include <iostream>

#include "Country.hpp"
#include "CountryGenerator.hpp"
#include "Location.hpp"
#include "Person.hpp"
#include "randomUtils.hpp"

void populateCountryRandomly(Country* country, float factor, bool log) {
	CountryGenerator cg(country);
	unsigned int nWPs = RandomUtils::randInt(2 * factor, 8 * factor);
	if (log) {
		std::cout << " " << nWPs << " works" << std::endl;
	}
	cg.generateWPs(nWPs);
	unsigned int nComm = RandomUtils::randInt(3 * factor, 10 * factor);
	if (log) {
		std::cout << " " << nComm << " communities" << std::endl;
	}
	for (size_t i = 0; i < nComm; i++) {
		unsigned int popSize = RandomUtils::randInt(100 * factor, 300 * factor);
		unsigned int nCCs = RandomUtils::randInt(3 * factor, 7 * factor);
		if (log) {
			std::cout << " Community " << i + 1 << ", population: " << popSize
				<< ", CCs: " << nCCs << std::endl;
		}
		cg.generateCommunity(popSize, nCCs);
	}
	cg.initInfected(GlobalParams::INIT_INFECTED);
}

int main() {

	Country c;
	populateCountryRandomly(&c, 10, true);
	std::cout << " Country population: " << c.populationSize()
		<< ", locations count: " << c.locationsCount() << std::endl;
	c.runSimulation(true);
}