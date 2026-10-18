# Risk-Based Testing

## Prioritizing by risk
Risk-based testing allocates effort using the likelihood of failure and its impact. Consider user-critical journeys, recent changes, dependencies, historical defects, and the ease of detecting problems after release. A simple likelihood-times-impact score can support discussion but is not a precise probability model.

## Testing levels
Unit tests examine small units of behavior. Integration tests examine interactions between components. End-to-end tests exercise complete workflows. Choose a mix based on the risks and architecture; no fixed ratio fits every product.

## Release evidence
A release assessment summarizes tested scope, meaningful failures, known defects, untested areas, and residual risks. Test pass percentage alone does not prove readiness. Stakeholders need evidence about the important workflows and remaining gaps.
