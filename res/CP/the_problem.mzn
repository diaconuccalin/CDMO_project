include "gecode.mzn";
include "globals.mzn";

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
set of int: ITEMS1 = 1..n+1;
array[ITEMS] of int: s;

% Assert for couriers to have the capacity to carry all items
constraint assert(sum(l) >= sum(s), "Unsolvable - total size of items is larger than total capacity of couriers.");

% Distances
set of int: LOCATIONS = 1..n+1;
array[LOCATIONS, LOCATIONS] of int: D;


% --------------------------------------------------------------------------------------------------------------
% Decision variables
% Courier assignment
array[ITEMS] of var COURIERS: courier_assignment;

% Precedence variable (for item ordering)
% pre[i] = j means that item i gets delivered immediately after item j
% or that the precedent of item i is j (j -> i)
array[ITEMS] of var ITEMS1: pre;

% Variable to store item carried by each courier
array[COURIERS, ITEMS] of var bool: item_assignment;

% Varaible for distances in the pre array
%array[ITEMS] of var min(D)..max(D): pre_dist;
array[ITEMS] of var {dist | dist in D where dist != 0}: pre_dist;

% Precedence table (marked with 1 if pre(i) = j, 0 otherwise)
% Slows everything down
array[ITEMS1, ITEMS1] of var bool: pre_table;

array[ITEMS] of var ITEMS: steps_from_origin;

array[COURIERS] of var 0..sum([max(row(D, i)) | i in ITEMS]) + (m * max(row(D, n+1))): covered_distances;

var 0..sum([max(row(D, i)) | i in ITEMS]) + (m * max(row(D, n+1))): max_dist;

% --------------------------------------------------------------------------------------------------------------

% Constraints
constraint forall(it in ITEMS) (
  pre_dist[it] = D[pre[it], it]
);

% Another way to respect capacity
constraint bin_packing_capa(l, courier_assignment, s);


% Item assignment channeling
% Mark with 1 items carried by courier in item_assignment matrix
constraint forall(co in COURIERS, it in ITEMS) (
  item_assignment[co, it] <-> (co = courier_assignment[it])
);

% Mark with 1 in precedence table
constraint forall(it in ITEMS where pre[it] <= n) (
  pre_table[pre[it], it] = 1
);

% Mark with 1 on the main diagonal the first object of each courier
constraint forall(it in ITEMS where pre[it] > n) (
  pre_table[it, it] = 1
);

% Mark with 0 everything else
constraint forall(it in ITEMS) (
  sum(col(pre_table, it)) == 1
);

% Since only one item is delivered at a time, there are no 2 items delivered immediately after another one
% So no 2 items should have the same precedent item, unless coming from origin
% No time difference for these 2
constraint alldifferent_except(pre, {n + 1});

% Tighter constraint for alldifferent in same courier
constraint forall(co in COURIERS)(
  alldifferent([pre[it] | it in ITEMS where courier_assignment[it] == co])
);

% Precedence can only happen between items carried by same courier
constraint forall(it in ITEMS, co in COURIERS where pre[it] != (n + 1)) (
  courier_assignment[it] == courier_assignment[pre[it]]
);

% Precedence can not happen with itself (courier can not remain in the same place)
constraint forall(it in ITEMS) (
  pre[it] != it
);

% Remove cycles
constraint forall(it in ITEMS where pre[it] = (n + 1)) (steps_from_origin[it] = 1);
constraint forall(it in ITEMS where pre[it] <= n)(
  steps_from_origin[it] = steps_from_origin[pre[it]] + 1
);

% Make sure the number of steps is different for each courier
constraint forall(co in COURIERS)(
  alldifferent([steps_from_origin[it] | it in ITEMS where courier_assignment[it] == co])
);

% Precedence - count that base appears as many times as the number of used couriers in the precedence array
constraint count(pre, (n + 1), sum([1 | co in COURIERS where sum(row(item_assignment, co)) > 0]));

% At most 1 of each item in pre (0 when last item, so it would be precedent of source location)
% Yields lower values in some cases (11, 12)
array[ITEMS] of int: l_bound = [0 | i in ITEMS];
array[ITEMS] of int: r_bound = [1 | i in ITEMS];

constraint global_cardinality_low_up(pre, ITEMS, l_bound, r_bound);

% Break symmetry for max load
constraint forall(c1, c2 in COURIERS where (c1 < c2 /\ l[c1] == l[c2])) (
  lex_less(row(item_assignment, c1), row(item_assignment, c2))
);

% Break symmetry for forward/reversed equal distances between locations (good for last 10 tests)
constraint lex_lesseq(array1d(pre_table), [ pre_table[j,i] | i,j in ITEMS]);

% Objective value
constraint forall(co in COURIERS) (
  covered_distances[co] = (sum(it in ITEMS where courier_assignment[it] == co) (D[pre[it], it]) + sum(it in ITEMS where count(pre, it, 0) /\ courier_assignment[it] == co) (D[it, (n + 1)]))
);
constraint max_dist = max(covered_distances);

solve ::  int_search(pre_dist, smallest, indomain_split)
      ::  restart_luby(250)
      ::  relax_and_reconstruct(pre_dist, 50)
          minimize max_dist;
