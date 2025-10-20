```Approach```:
The approach I took for this problem was to first create dataclasses to represent the core concepts of 
Battery and Market, along with their associated methods for operations like charging, discharging, and checking viability of dispatching.
I used TDD to ensure expected behaviour of these methods. I did similarly for the main dispatching logic, starting 
with a simple algorithm based on average prices and then refining it to look ahead a few intervals to make better decisions.
The algorithm assumes knowledge of future prices, and looks ahead a variable (set at the outset) number of hours to 
determine local minima and maxima for charging and discharging respectively. If we are at a local minimum, 
we charge the battery, and vice-versa. Some simplifications were made, such as ignoring efficiency and only allowing
one market commitment at a time, to keep the problem manageable within the time constraints. Initial implementation
with the average price algorithm yielded a profit of around £66k, while the lookahead algorithm improved this to over £200k 
(not taking into account diminishing factors such as battery wear and efficiency). Full results are shown at the bottom for the latest version of the algorithm.

```Instructions for running the code```:
- Clone the repository
- `python3 -m venv venv` to create a virtual environment
- `source venv/bin/activate` to activate the virtual environment
- `cd` into `aurora_technical_test`
- `pip install -e .` to install dependencies
- (Optional) `pip install -r requirements-dev.txt` to install dev dependencies (to run e.g. pytest)
- Run main execution script with `python -m battery_dispatch.core`
- I haven't set up any command line arguments, so to change parameters you will need to edit the script directly in `src/battery_dispatch/core.py`


```NOTES MADE DURING DEVELOPMENT```:
Plan (update as I go):

- Create initial dataclasses for core modelling concepts (with fields based on given data):
  - Battery
  - Market
  - Commitment of energy for market (link between the two above)

- Implement methods on these dataclasses for basic operations

Rough idea for first pass is:
- Choose the smallest time interval and evaluate best choice at each interval
- Implement a simple algorithm to check whether to charge or discharge based on market prices
- To start with, assume we know all market prices in advance (here we can do this but probably a big assumption in reality)
- To mostly simply guess where the best profit lies, get the average price across both markets - if current price is above average, discharge, if below, charge
- Since there are two markets, we can do this independently for each market and see which gives better effective profit
- Ignore efficiency for now - will be easier to add in later

This gives some operations we will need to implement on the dataclasses:
  - Battery: 
    - charge
    - discharge
    - get state of charge/capacity
    - check if can charge/discharge
    - I think we should separate adding and clearing commitments to markets since they have differing intervals, and we need to make sure we track ongoing commitments
  
  - Market:
    - check if we are on the correct interval
    - average price

- Write tests for dataclass methods
- Write a simple version of this with dummy functions to see what we might need to add
- Write an integration test to check overall functionality
- Fill in remainder of algorithm details and edge cases (e.g. what happens if battery is full/empty)
- Fix any issues found in testing

Things to get to later (if time permits):
- More sophisticated algorithm for deciding when to charge/discharge (e.g. look ahead a few intervals rather than overall average)
- Consider efficiency
- Consider using an optimisation package for even better results (e.g. pyomo, scipy.optimize), although I have never used these so it will mostly be exploratory


Decisions made during:
- Should we allow partial charging/discharging?
  - Ideally yes, as it will be a better model, but may make logic trickier. I will try to implement as we go as this might be trickier to squeeze in later. If it gets too complex, I may revert to all-or-nothing charging/discharging.
- Thinking about how we can handle multiple markets, I can see some complexity in tracking multiple commitments in one go, as we'll need a second state to track potential/ongoing commitments
  - This seems like it could get a bit messy, so I'm potentially thinking about creating a fake battery to test whether we can safely commit energy before actually committing it.
  - This will be less efficient but should be simpler to implement and reason about
- When writing integration tests, I realise that dispatching to two markets at once doesn't really make sense in the same time interval with the assumptions we have, since we would always prefer the higher price market
  - So I will assume we can only commit to one market at a time, which simplifies things a bit
  - In reality this may not be the case, as maybe there are ways that we can split energy between markets more efficiently
- I don't think this is necessarily the best way, but here I am going to track cost and revenue on the battery itself, since it is within the battery logic that we are making decisions about what to commit.
  - Maybe we should have had a service like a `BatteryManager` to handle this, but it would take too long to refactor now
  - This is mainly because the cost and revenue are dependent on the final amount of change dispatched, which I only evaluate at the point of committing to a market
  - This is maybe a weakness in this approach
- Although I built this to handle multiple concurrent commitments, on reflection I decided to change to only allowing one at a time
  - This is because we assume any current commitments are using the maximum power available, and we have committed to them already so we cannot take on more commitments
  - This would simplify the logic a bit in places, but leaving as it is for now as it offers better flexibility if we want to change this assumption later

- Now trying a quick run at a better algorithm of looking ahead a few intervals rather than just using the average price
  - This will also add a bit of complexity to the code, but I think it's worth it for better performance
  - Baseline profit is £66.3k `Total Revenue: 308363.22 GBP, Total Cost: 242089.62 GBP, Total Profit: 66273.59 GBP, Final State of Charge: 0.00 MWh`
  - Initially getting worse results since I am buying and selling whenever there is a better price in future, meaning I a getting a loss
  - Instead checking that I'm at a local minimum or maximum fixes this and gives much better results
  - A quick test with varying the number of hours to look ahead:
  
1: `Total Revenue: 751813.03 GBP, Total Cost: 527411.24 GBP, Total Profit: 224401.79 GBP, Final State of Charge: 2.00 MWh`

2: `Total Revenue: 578675.99 GBP, Total Cost: 365779.04 GBP, Total Profit: 212896.94 GBP, Final State of Charge: 2.00 MWh`

3: `Total Revenue: 503920.46 GBP, Total Cost: 299147.13 GBP, Total Profit: 204773.34 GBP, Final State of Charge: 2.00 MWh`

4: `Total Revenue: 456785.43 GBP, Total Cost: 259832.82 GBP, Total Profit: 196952.61 GBP, Final State of Charge: 2.00 MWh`

5: `Total Revenue: 419631.25 GBP, Total Cost: 229647.02 GBP, Total Profit: 189984.23 GBP, Final State of Charge: 2.00 MWh`

6: `Total Revenue: 388349.88 GBP, Total Cost: 205180.90 GBP, Total Profit: 183168.98 GBP, Final State of Charge: 2.00 MWh`

7: `Total Revenue: 356682.32 GBP, Total Cost: 181473.64 GBP, Total Profit: 175208.68 GBP, Final State of Charge: 2.00 MWh`

8: `Total Revenue: 324131.68 GBP, Total Cost: 158289.82 GBP, Total Profit: 165841.86 GBP, Final State of Charge: 2.00 MWh`

9: `Total Revenue: 298280.70 GBP, Total Cost: 140735.93 GBP, Total Profit: 157544.77 GBP, Final State of Charge: 2.00 MWh`

10: `Total Revenue: 278939.15 GBP, Total Cost: 127922.17 GBP, Total Profit: 151016.98 GBP, Final State of Charge: 2.00 MWh`
  - The sweet spot here is kind of difficult to tell without taking considerations about battery wear etc. into account, but I think 2-4 hours seems to be a good balance between complexity and performance


- I'm over 4 hours in now, so I will stop here and submit what I have, next to look at would be adding efficiency and other battery constraints which are not taken into account at all in this model and possibly refining the algorithm further
- To better consider constraints I should track and log more info about number of charges etc.