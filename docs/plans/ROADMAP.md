# Delivery roadmap

| Phase | Status | Deliverable / gate |
| --- | --- | --- |
| Engineering foundation | Complete | Architecture, schemas, contracts, isolated PLAN-001 and independent design review |
| PLAN-001 local deterministic MVP | Approved; not implemented | 39 isolated tasks proving orchestration and recovery against fake agents/hosting and real local Git |
| Production adapter pilot | Future plan | Select a supported agent/provider, verify actual model identity and higher-review capability, enforce requested sandbox, add resumable adapter; configure credentials and authority outside committed files |
| Hosting pilot | Future plan | Implement a real PR/CI adapter against verified official provider documentation and run authorized sandbox-repository delivery |
| Release hardening | Future plan | Real Windows/Linux runtime evidence, migration compatibility, installation UX, performance budgets, license and release decision |

Each future plan must receive its own researched contracts, small tasks and isolation approval before implementation. The fake-adapter MVP is deliberately the first testable slice; real code-generation capability and remote delivery are required follow-on work before claiming the full product goal is operational. No real provider, price, API availability or credential is assumed by this foundation.
