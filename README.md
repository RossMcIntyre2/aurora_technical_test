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