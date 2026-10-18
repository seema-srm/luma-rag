# Investigating Flaky Tests

## What is a flaky test?
A flaky test produces inconsistent results without a relevant change to the application or test. Common causes include timing assumptions, shared state, unstable external dependencies, and nondeterministic test data.

## Investigating failures
Collect the failure message, application logs, environment details, test data, and timing. Run the test alone and in its usual suite. Check whether order, parallel execution, or resource limits affect outcomes. A retry can help diagnose intermittence but does not repair the underlying cause.

## Reliable synchronization
Prefer waiting for an observable application condition with a bounded timeout over arbitrary fixed sleeps. Isolate test data and clean up owned resources. Quarantine requires an owner and a repair plan so it does not silently remove important coverage.
