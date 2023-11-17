include "alldifferent.mzn";
include "alldifferent_except_0.mzn";
include "count_fn.mzn";

% Constants
% # of couriers
int: m;

% # of items
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
constraint assert(sum(l) >= sum(s), "Unsolvable - total weight of items is larger than total capacity of couriers.");

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
array[ITEMS] of var 1..n+1: pre;

% Variable to store item carried by each courier
array[COURIERS, ITEMS] of var 0..1: item_assignment;

% Variable to store distance needed to deliver item, based on precedence
array[ITEMS] of var 0..max(D): item_d;

% Variable to store all items that precede another item
array[ITEMS] of var 0..1: has_next;

% Variable to store leftover distance (from last item of all couriers to origin)
var 0..sum(D): leftover_dist;

% Variable to store total distance
var 0..sum(D): total_dist;
% --------------------------------------------------------------------------------------------------------------


% Constraints
% Constraint to mark with 1 items carried by courier in item_assignment matrix
constraint forall(it in ITEMS) (
  item_assignment[courier_assignment[it], it] == 1
);

% Constraint for all other values to be 0 in the item_assignment matrix s.t. assigned to exactly one courier
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
% So no 2 items should have the same precedent item (unless 0, which means it's the first item being taken
%   and previous point was the origin
% Maybe not needed anymore because below plus origin is not 0, but last i
% constraint alldifferent_except_0(pre);

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

% Precedence for each courier to include base once
%constraint forall(co in COURIERS) ( 
% );

%add column for base
%make it always 1
%make it such that precedence can not be itself

% Compute distances for each item
constraint forall(it in ITEMS) (
  item_d[it] = D[pre[it], it]
);

% Mark with 1 all items that have a predecesor
constraint forall(it in ITEMS where pre[it] < (n + 1)) (
  has_next[pre[it]] = 1
);

% Make sure that all other are 0
constraint count(has_next, 1, (n - m));

% Compute distances from last drop point to origin
constraint sum(it in ITEMS where has_next[it] == 0) (D[it, (n + 1)]) == leftover_dist;

% Compute total distance
constraint (sum(it in ITEMS) (item_d[it]) + leftover_dist) == total_dist;

solve minimize total_dist;
