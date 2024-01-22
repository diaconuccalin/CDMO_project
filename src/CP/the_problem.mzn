include "gecode.mzn";
include "globals.mzn";


% ~~~~~~~~~~~~~~~~~~~~~~~~ Instance parameters ~~~~~~~~~~~~~~~~~~~~~~~~
% Number of couriers
int: m;

% Number of items
int: n;

% Assert for number of items >= number of couriers - from problem requirements
constraint assert(n >= m, "Invalid data - less items than couriers.");

% Sets to use for iterations
set of int: ITEMS = 1..n;
set of int: COURIERS = 1..m;
set of int: LOCATIONS = 1..n+1;

% Maximum load for each courier
array[COURIERS] of int: l;

% Size of each item
array[ITEMS] of int: s;

% Assert for couriers to have the capacity to carry all items
constraint assert(sum(l) >= sum(s), "Unsolvable - total size of items is larger than total capacity of couriers.");

% Distances
array[LOCATIONS, LOCATIONS] of int: D;


% ~~~~~~~~~~~~~~~~~~~~~~~~ Decision variables ~~~~~~~~~~~~~~~~~~~~~~~~
% Courier assignment
array[ITEMS] of var COURIERS: courier_assignment;

% Variable to store item carried by each courier
array[COURIERS, ITEMS] of var bool: item_assignment;

% Precedence variable (for item ordering)
% pre[i] = j means that item i gets delivered immediately after item j
% or that the precedent of item i is j (the direction of the courier is j -> i)
array[ITEMS] of var LOCATIONS: pre;

% Precedence table (marked with 1 if pre(i) = j, 0 otherwise)
array[ITEMS, ITEMS] of var bool: pre_table;

% Varaible for distances in the precedence array
array[ITEMS] of var {dist | dist in D where dist != 0}: pre_dist;


% Count the number of steps (not the distance) made by courier from origin to deliver the item
array[ITEMS] of var ITEMS: steps_from_origin;

% Array to store the total distances covered by each courier
% Used to set tighter limits for these values
array[COURIERS] of var 0..sum([max(row(D, i)) | i in ITEMS]) + (max(row(D, n+1))): covered_distances;

% Store the maximum value in the previous array (objective function)
var 0..sum([max(row(D, i)) | i in ITEMS]) + (max(row(D, n+1))): max_dist;


% ~~~~~~~~~~~~~~~~~~~~~~~~ Constraints ~~~~~~~~~~~~~~~~~~~~~~~~
% Mark distances in the corresponding array
constraint forall(it in ITEMS) (
  pre_dist[it] = D[pre[it], it]
);

% Make sure the capacity of couriers is enforced
constraint bin_packing_capa(l, courier_assignment, s);

% Item assignment channeling
% Mark with 1 items carried by courier in item_assignment matrix
constraint forall(co in COURIERS, it in ITEMS) (
  item_assignment[co, it] <-> (co = courier_assignment[it])
);

% Complete precedence table
% Mark with 1 item and its precedent
constraint forall(it in ITEMS where pre[it] <= n) (
  pre_table[pre[it], it] = 1
);

% Mark with 1 on the main diagonal the first object of each courier
constraint forall(it in ITEMS where pre[it] > n) (
  pre_table[it, it] = 1
);

% Mark with 0 everything else
constraint forall(it in ITEMS) (
  sum(col(pre_table, it)) = 1
);

% Since only one item is delivered at a time, there are no 2 items delivered immediately after another one
% So no 2 items should have the same precedent item, unless coming from origin
constraint alldifferent_except(pre, {n + 1});

% Precedence can only happen between items carried by same courier
constraint forall(it in ITEMS, co in COURIERS where pre[it] != (n + 1)) (
  courier_assignment[it] = courier_assignment[pre[it]]
);

% Remove cycles
constraint forall(it in ITEMS where pre[it] = (n + 1)) (steps_from_origin[it] = 1);
constraint forall(it in ITEMS where pre[it] <= n)(
  steps_from_origin[it] = steps_from_origin[pre[it]] + 1
);

% Count that base appears as many times as the number of used couriers in the precedence array (each courier must leave from origin)
constraint count(pre, (n + 1), sum([1 | co in COURIERS where sum(row(item_assignment, co)) > 0]));


% Implied constraint: make sure that each item is carried by a single courier
constraint redundant_constraint(forall(it in ITEMS)(
    sum(co in COURIERS)(item_assignment[co, it]) == 1
));

% Implied constraint: item cannot be precedent of itself (already solved by cycle breaking)
constraint redundant_constraint(forall(it in ITEMS)(pre[it] != it));

% Implied constraint: make sure that for all items in courier, the number of steps is different
constraint redundant_constraint(forall(co in COURIERS)(
    alldifferent([steps_from_origin[it] | it in ITEMS where courier_assignment[it] == co])
));

% Implied constraint: check that for each item x, at most one other item has x as previous item
constraint redundant_constraint(global_cardinality_low_up(pre, ITEMS, [0 | i in ITEMS], [1 | i in ITEMS]));

% Break symmetry for max load
constraint symmetry_breaking_constraint(forall(c1, c2 in COURIERS where (c1 < c2 /\ l[c1] == l[c2])) (
  lex_less(row(item_assignment, c1), row(item_assignment, c2))
));

% Break symmetry for forward/reversed equal distances between locations (good for last 10 tests)
constraint symmetry_breaking_constraint(lex_lesseq(array1d(pre_table), [pre_table[j,i] | i,j in ITEMS]));

% Objective value
constraint forall(co in COURIERS) (
  covered_distances[co] = (sum(it in ITEMS where courier_assignment[it] == co) (D[pre[it], it]) + sum(it in ITEMS where count(pre, it, 0) /\ courier_assignment[it] == co) (D[it, (n + 1)]))
);
constraint max_dist = max(covered_distances);

solve ::  int_search(pre_dist, smallest, indomain_split)
      ::  restart_luby(250)
      ::  relax_and_reconstruct(pre_dist, 50)
          minimize max_dist;
