#include <random>

namespace RandomUtils {

    inline bool bernoulli(float prob) {
        static std::random_device device;
        static unsigned int seed = device();
        static std::mt19937 randomEngine(seed);
        static std::uniform_real_distribution<float> distribution(0, 1);

        return distribution(randomEngine) < prob;
    }

    inline int randInt(int min, int max) {
        static std::random_device device;
        static unsigned int seed = device();
        static std::mt19937 randomEngine(seed);
        std::uniform_int_distribution<int> distribution(min, max);
        return distribution(randomEngine);
    }
} // namespace RandomUtils