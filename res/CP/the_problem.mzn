include "alldifferent.mzn";
include "alldifferent_except.mzn";
include "count_fn.mzn";

% Instance parameters
% Number of couriers
int: m;

% Number of items
int: n;

% Assert for number of items >= number of couriers - from problem requirements
constraint assert(n >= m, "Invalid data - less items than couriers.");

% Maximum load for each courier
set of int: COURIERS = 1..m;
array[COURIERS] of int: l;

% Size of each item
set of int: ITEMS = 1..n;
array[ITEMS] of int: s;

% Assert for couriers to have the capacity to carry all items
constraint assert(sum(l) >= sum(s), "Unsolvable - total size of items is larger than total capacity of couriers.");

% Distances
set of int: LOCATIONS = 1..n+1;
array[LOCATIONS, LOCATIONS] of int: D;


% --------------------------------------------------------------------------------------------------------------
% Decision variables
% Courier assignment
array[ITEMS] of var 1..m: courier_assignment;

% Actual load for each courier
array[COURIERS] of var 0..max(l): actual_load;

% Precedence variable (for item ordering)
% pre[i] = j means that item i gets delivered immediately after item j
% or that the precedent of item i is j
array[ITEMS] of var 1..n+1: pre;

% Variable to store item carried by each courier
array[COURIERS, ITEMS] of var 0..1: item_assignment;

% Variable to store total distance
var 0..sum(D): total_dist;
% --------------------------------------------------------------------------------------------------------------


% Constraints

% Item assignment
% Mark with 1 items carried by courier in item_assignment matrix
constraint forall(it in ITEMS) (
  item_assignment[courier_assignment[it], it] == 1
);

% Mark with 0 all other values
constraint forall(it in ITEMS) (
  sum(co in COURIERS)(item_assignment[co, it]) == 1
);

% Maximum capacity of each courier
% Get sum of items carried by each in actual_load
constraint forall(co in COURIERS) (
  actual_load[co] = sum(it in ITEMS)((courier_assignment[it] == co) * s[it])
);

% Constrain to maximum load of each
constraint forall(co in COURIERS) (
  actual_load[co] <= l[co]
);

% Since only one item is delivered at a time, there are no 2 items delivered immediately after another one
% So no 2 items should have the same precedent item, unless coming from origin
constraint alldifferent_except(pre, {n + 1});

% Tighter constraint for alldifferent in same courier
constraint forall(co in COURIERS)(
  alldifferent([pre[it] | it in ITEMS where item_assignment[co, it] == 1])
);

% Precedence can only happen between items carried by same courier
constraint forall(it in ITEMS, co in COURIERS where pre[it] != (n + 1)) (
  item_assignment[co, it] == item_assignment[co, pre[it]]
);

% Precedence can not happen with itself (courier can not remain in the same place)
constraint forall(it in ITEMS) (
  pre[it] != it
);

% Precedence - avoid cycles
constraint forall(it in ITEMS where pre[it] < (n + 1)) (
  pre[pre[it]] != it
);

% Precedence - count that base appears as many times as the number of couriers
% (since alldifferent, it will be included exactly once for each of them)
constraint count(pre, (n + 1), m);

% Compute total distance
constraint total_dist = (sum(it in ITEMS) (D[pre[it], it]) + sum(it in ITEMS where count(pre, it, 0)) (D[it, (n + 1)]));

solve minimize total_dist;
