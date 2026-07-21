# Subagent architecture

`t-think` is the root at depth zero. Ten terminal workers operate at depth one: investigator, modeler, planner, critic, builder, technical reviewer, security reviewer, breaking reviewer, verifier, and reconciler. Composite phases use multiple fresh terminal delegations but one aggregate lifecycle transition. Workers never delegate recursively.
