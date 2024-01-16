include "alldifferent.mzn";
include "alldifferent_except.mzn";
include "count_fn.mzn";
include "gecode.mzn";
include "global_cardinality_low_up.mzn";
include "bin_packing_capa.mzn";

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

% Actual load for each courier
% array[COURIERS] of var 0..max(l): actual_load;

% Precedence variable (for item ordering)
% pre[i] = j means that item i gets delivered immediately after item j
% or that the precedent of item i is j (j -> i)
array[ITEMS] of var ITEMS1: pre;

% Subservience variable
% sub[i] = j => i -> j => sub[i] = j iff pre[j] = i
% array[ITEMS] of var 1..n+1: sub;

% Variable to store item carried by each courier
array[COURIERS, ITEMS] of var bool: item_assignment;

% Varaible for distances in the pre array
array[ITEMS] of var min(D)..max(D): pre_dist;

% Precedence table (marked with 1 if pre(i) = j, 0 otherwise)
% Slows everything down
%array[ITEMS1, ITEMS1] of var bool: pre_table;

% Variable to store total distance
% var 0..ceil(sum(D) / 2): total_dist;
% n for each item, m to go to base
%var (n + m) * min(D)..(n + m) * max(D): total_dist;
var sum([min(row(D, i)) | i in 1..n]) + (m * min(row(D, n+1)))..sum([max(row(D, i)) | i in 1..n]) + (m * max(row(D, n+1))): total_dist;

% --------------------------------------------------------------------------------------------------------------


% Constraints

constraint forall(it in ITEMS) (
  pre_dist[it] = D[pre[it], it]
);


% Another way to respect capacity
constraint bin_packing_capa(l, courier_assignment, s);


% Item assignment
% Mark with 1 items carried by courier in item_assignment matrix
constraint forall(it in ITEMS) (
  item_assignment[courier_assignment[it], it] == 1
);

% Mark with 0 all other values
constraint forall(it in ITEMS) (
  sum(co in COURIERS)(item_assignment[co, it]) == 1
);

% Also on vertical - no time improvement
constraint forall(co in COURIERS) (
  sum(it in ITEMS) (item_assignment[co, it]) == count(courier_assignment, co)
);


% Mark with 1 in precedence table
%constraint forall(it in ITEMS where pre[it] <= n) (
%  pre_table[pre[it], it] = 1
%);

% Mark with 1 on the main diagonal the first object of each courier
%constraint forall(it in ITEMS where pre[it] > n) (
%  pre_table[it, it] = 1
%);

% Mark with 0 everything else
%constraint forall(it in ITEMS) (
%  sum(col(pre_table, it)) == 1
%);

% Maximum capacity of each courier
% Get sum of items carried by each in actual_load
%constraint forall(co in COURIERS) (
%  actual_load[co] = sum(it in ITEMS)((courier_assignment[it] == co) * s[it])
%);

% Constrain to maximum load of each
%constraint forall(co in COURIERS) (
%  sum(it in ITEMS)((courier_assignment[it] == co) * s[it]) <= l[co]
%);

% Connect pre and sub
% sub[i] = j iff pre[j] = i => pre[sub[i]] == i && sub[pre[j]] == j
%constraint forall(it in ITEMS where sub[it] < (n + 1)) (pre[sub[it]] == it);
%constraint forall(it in ITEMS where pre[it] < (n + 1)) (sub[pre[it]] == it);

% Since only one item is delivered at a time, there are no 2 items delivered immediately after another one
% So no 2 items should have the same precedent item, unless coming from origin
% No time difference for these 2
constraint alldifferent_except(pre, {n + 1});

% Same for sub
%constraint alldifferent_except(sub, {n + 1});

% Tighter constraint for alldifferent in same courier
constraint forall(co in COURIERS)(
  alldifferent([pre[it] | it in ITEMS where courier_assignment[it] == co])
);

% Same for sub
%constraint forall(co in COURIERS)(
%  alldifferent([sub[it] | it in ITEMS where courier_assignment[it] == co])
%);

% Precedence can only happen between items carried by same courier
constraint forall(it in ITEMS, co in COURIERS where pre[it] != (n + 1)) (
  courier_assignment[it] == courier_assignment[pre[it]]
);

% Same for sub
%constraint forall(it in ITEMS, co in COURIERS where sub[it] != (n + 1)) (
%  courier_assignment[it] == courier_assignment[sub[it]]
%);

% Precedence can not happen with itself (courier can not remain in the same place)
constraint forall(it in ITEMS) (
  pre[it] != it
);

% Same for sub
%constraint forall(it in ITEMS) (
%  sub[it] != it
%);

% Precedence - avoid cycles
constraint forall(it in ITEMS where pre[it] < (n + 1)) (
  pre[pre[it]] != it
);

% Same for sub
%constraint forall(it in ITEMS where sub[it] < (n + 1)) (
%  sub[sub[it]] != it
%);

% Precedence - count that base appears as many times as the number of couriers
% (since alldifferent, it will be included exactly once for each of them)
constraint count(pre, (n + 1), m);

% At most 1 of each item in pre (0 when last item, so it would be precedent of source location)
% Yields lower values in some cases (11, 12)
array[ITEMS] of int: l_bound = [0 | i in ITEMS];
array[ITEMS] of int: r_bound = [1 | i in ITEMS];

constraint global_cardinality_low_up(pre, ITEMS, l_bound, r_bound);

% Break symmetry for max load
constraint forall(c1, c2 in COURIERS where (c1 < c2 /\ l[c1] == l[c2])) (
  lex_less(row(item_assignment, c1), row(item_assignment, c2))
);

% Break symmetry for forward/reversed equal distances between locations (last 10 tests)
% constraint lex_lesseq(array1d(pre_table), [ pre_table[j,i] | i,j in ITEMS]);

% Same sub
%constraint count(sub, (n + 1), m);

% Compute total distance
constraint total_dist = (sum(it in ITEMS) (D[pre[it], it]) + sum(it in ITEMS where count(pre, it, 0)) (D[it, (n + 1)]));

solve ::  int_search(pre_dist, smallest, indomain_min)
      ::  restart_linear(100)
          minimize total_dist;
