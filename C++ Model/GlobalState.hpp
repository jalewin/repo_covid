#pragma once

class GlobalState
{
private:
    unsigned int m_currCycle = 0;

public:
    GlobalState() {}
    ~GlobalState() {}

    void update() { m_currCycle++; }
    unsigned int getCycle() const { return m_currCycle; }
};