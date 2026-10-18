# Test Design Foundations

## Equivalence partitioning
Divide inputs into groups expected to behave similarly. Test representatives from each group. For an age field accepting integers from 18 to 65, useful partitions include below 18, 18 through 65, and above 65. Empty, nonnumeric, and decimal inputs may require additional cases, depending on requirements.

## Boundary value analysis
Boundary value analysis targets edges where behavior changes. For an inclusive integer range from 18 to 65, a useful set is 17, 18, 19, 64, 65, and 66. Requirements determine expected results; the technique does not invent the rules.

## Decision tables
A decision table maps combinations of conditions to expected actions. It helps find missing business rules. For discounts depending on membership and coupon validity, enumerate meaningful combinations and confirm expected outcomes with stakeholders.
