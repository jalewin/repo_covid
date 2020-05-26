#include <iostream>

#include "Country.hpp"
#include "CountryGenerator.hpp"
#include "Location.hpp"
#include "Person.hpp"
#include "randomUtils.hpp"

void populateCountryRandomly(Country* country, float factor, bool log) {
	CountryGenerator cg(country);
	unsigned int nWPs = RandomUtils::randInt(20 * factor, 30 * factor);
	if (log) {
		std::cout << " " << nWPs << " works" << std::endl;
	}
	cg.generateWPs(nWPs);
	unsigned int nComm = RandomUtils::randInt(40 * factor, 50 * factor);
	if (log) {
		std::cout << " " << nComm << " communities" << std::endl;
	}
	for (size_t i = 0; i < nComm; i++) {
		unsigned int popSize = RandomUtils::randInt(1000 * factor, 3000 * factor);
		unsigned int nCCs = RandomUtils::randInt(5 * factor, 10 * factor);
		if (log) {
			std::cout << " Community " << i + 1 << ", population: " << popSize
				<< ", CCs: " << nCCs << std::endl;
		}
		cg.generateCommunity(popSize, nCCs);
	}
	cg.initInfected(GlobalParams::INIT_INFECTED);
}

void populateCountry(Country* country) {
	CountryGenerator cg(country);
	cg.generateWPs(3);
	for (size_t i = 0; i < 50; i++) {
		cg.generateCommunity(1000, 3);
	}
	cg.initInfected(10);
}

int main() {
	std::cout << "Hello World\n";
	Country c;
	populateCountryRandomly(&c, 0.5, false);
	std::cout << " Country population: " << c.populationSize()
		<< ", locations count: " << c.locationsCount() << std::endl;
	c.runSimulation(false);
}