#pragma once

#include <map>
#include <string>
#include <vector>

#include "GlobalParams.hpp"

class Person;
enum class HealthStatus;

typedef std::map<HealthStatus, unsigned int> HealthDict;

class Location {
  private:
    std::vector<Person*> m_visitors = {};
    std::string m_name;
    int m_id;
    float m_visitProb;

  public:
    Location(std::string name, int id, float visitProb);
    virtual ~Location() { /* Empty */ }

    float getVisitProb() const { return m_visitProb; }

    HealthDict getHealthSummery() const;
    void visit(Person* person);
    void udpateVisitorsHealth();
    void clearVisitors();
};

class HouseHold : public Location {
  public:
    HouseHold(std::string name, int id) : Location(name, id, 1.f) {}
};

class CommunityCenter : public Location {
  public:
    CommunityCenter(std::string name, int id, float visitProb)
        : Location(name, id, visitProb) {}
};

class PublicTransportation : public Location {
  public:
    PublicTransportation(std::string name, int id, float visitProb)
        : Location(name, id, visitProb) {}
};

class WorkPlace : public Location {
  public:
    WorkPlace(std::string name, int id)
        : Location(name, id, GlobalParams::WP_VISIT_PROB){};
};