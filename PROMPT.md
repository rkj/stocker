 initialize this project, figure out architecture, etc. What we want to do is build stock trading simulator with some easily
  describable strategies that will run over historical data and tell us how would that strategy perform.

  one strategy that must be possible to execute is S&P 500 index with daily rebalancing. There must be inputs like trading cost or
  something. You should work until you get realistic market returns from the historical data (matching published research). Data
  should be taken from arguments, currently it's located at /mnt/nfs-lithium-public/rkj/all_stock_data.csv

  another strategy we will want to compare is equal owned (buy same $ amount of evry stock and rebalance from there)

  yet another is the variants of above with less often rebalancing (so maybe make an option to above with that) - rebalance once a
  year or never

  yet another combination of both above is additional investment - buying new stock (with accurate balancing) daily, monthly,
  yearly.

  Another strategy is to pick N number of stock, either specific or randomly or most valued or least valued, etc.

  Feel free to come with some other popular strategies.

  Then we should be able to run them all specifying date of entering the market, how much and then how much we invest, and then at
  the end of simulation we should see how all the strategies fare (as simulation runs it should capture daily data so we can draw
  chart, but then we should hae some table at the end with just strategies and returns every year or something). Could be either
  simple webpage with something running on the backend or fully TUI app.

  Pick an efficient language. If python works fast enough that's fine, but go or rust should be also consider. Start with writing
  docs with all of the above (product requirements in docs/spec/), then for every engineering decision (stack, language, algorithms,
  strategy representation, etc write ADR in docs/adr) - start with overview/high level, then break it down into more and more
  details.

  After all of the above is done you can start coding. You can use beads for tracking tasks so you won't forget (bd prime for
  instructions).

  The code produced should be of high quality, SOLID & DRY. Strict TDD with everything - extract some sample test data from the
  whole datafile and use that for testing. Commit often with good descriptions. Start with writing AGENTS.md, then create beads for
  major tasks (product requirement, adrs, code), then break each beads into smaller and smaller task (and use beads later when you
  start new task and have better idea about area to break things further). Then run in a loop - consume single bead, fix it, take
  next one, etc.
