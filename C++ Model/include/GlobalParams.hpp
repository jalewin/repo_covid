#pragma once

#include <math.h>

namespace GlobalParams {

    namespace Privates {
        const float DEATH_RATE = 0.05f;
        const float DISEASE_DURATION = 20.f;
    } // namespace Privates

    const float INFECTION_PROB = 0.3f;
    const float RECOVERY_PROB = 1.f / Privates::DISEASE_DURATION;
    const float DEATH_PROB =
        1.f - powf(1 - Privates::DEATH_RATE, 1 / Privates::DISEASE_DURATION);
    const unsigned int MAX_CYCLES = 365;
    const unsigned int NUM_LOCATIONS = 100;
    const unsigned int AVG_POPULATION = 50;
    const unsigned int AVG_NEIGHBORS = 3;
    const unsigned int INIT_INFECTED = 10;
    const unsigned int AVG_HOUSEHOLD_SIZE = 6;
    const unsigned int AVG_HOUSEHOLD_CCs = 2;
    const float AVG_HOUSEHOLD_WORKING_PEOPLE = 1.7f;
    const unsigned int POPULATION_SIZE = 1000;
    const float WP_VISIT_PROB = 5.f / 7.f;
    const float CC_VISIT_PROB = 1.f / 10.f;

} // namespace GlobalParams
