# Task template

Every task carries this shape in its description on the board before an agent may touch it. The
rules around it are in [workflow.md](workflow.md) — this file is the form itself.

**Every line cites its source.** A section of the domain document, an ADR, a file and line, or a
decision recorded in this task. An uncited line is an invention, and can be recognised as one
without checking anything.

---

```markdown
**Goal.** <One sentence: why this task exists.>

**Scope.**
- <What changes, in modules and files.>

**Out of scope.**
- <What is deliberately not built here.>

**Contract.**
- <Formula, constant, type or signature> — *<source>*

**Acceptance.**
- [ ] <A command to run, or a number to assert> — *<source>*

**Verification.**
- `<check command>`
- `<mutation command>` <only when the task touches the mutation-tested area>
- <anything else this task needs>

**Open questions.**
- <none>

**Risk.** low | normal | high
```

---

## Filling it in

**Goal** — one sentence. If it needs two, the task is two tasks.

**Scope** names modules and files, not behaviour: *what will be different in the tree*. Behaviour
belongs in Contract.

**Out of scope** is not decoration. It is the field that stops invented work: a settings module
with fake settings, a helper nothing calls, an abstraction for a second case that does not exist.
When a task plausibly implies something it should not build, say so here.

**Contract** is the substance — the formulas, constants, types and signatures the implementation
must match, each with the source it came from. `credit = round2(price × remaining / cycle)` is a
contract line; "the customer should get a fair credit" is not.

**Acceptance** has one rule: **each line is a command or an asserted number, never an opinion.**

- Good: *the five rows of table 3 in PRD 4.2 reproduce exactly*; *the same request replayed twice
  yields one row, not two*; *p99 latency under 50 ms on the committed fixture*; *the check command
  passes*.
- Not acceptable: *the numbers look reasonable*; *the code is clean*; *performance is good*.

If a criterion genuinely cannot be expressed that way, the task is not ready — it goes back to
`refine`, or the criterion is dropped and named in Out of scope.

**Verification** is the exact command list the agent runs before requesting review. It exists so
the pull request's evidence block can be filled without judgement.

**Open questions** must read `none` for the task to leave `refine`. Anything else here is the
reason it cannot.

**Risk** is recorded but carries no rule yet. It is here so the data exists when a rule about
closer review for high-risk tasks is worth writing.

## Worked example

A task of the shape this workflow expects, from a billing service whose product requirements
document (PRD) owns the rules. The shape is what matters, not the domain: every line names where it
came from, and every acceptance line is a number or a command.

```markdown
**Goal.** Compute the credit and the charge when a subscription changes plan mid-cycle, as a pure function, so that billing has exactly one place that number comes from.

**Scope.**
- `src/billing/proration.ts` — `prorate(change, cycle)` — *PRD 4.2, ADR-0007*
- `src/billing/types.ts` — `PlanChange`, `BillingCycle`, `Proration` — *PRD 4.2*
- Tests alongside `proration.ts`

**Out of scope.**
- Writing the invoice, calling the payment provider, touching the database. The function returns numbers; the invoice is task #214 — *ADR-0007*
- Currency conversion. Both plans are priced in the cycle's currency — *PRD 4.2; decision in this task*
- Currencies without a minor unit. A later task — *decision in this task*
- Any UI for changing plans

**Contract.**
- `credit = round2(old_price × remaining_days / cycle_days)` — *PRD 4.2, formula (1)*
- `charge = round2(new_price × remaining_days / cycle_days)` — *PRD 4.2, formula (2)*
- The day of the change counts as remaining: a change on the last day of the cycle has `remaining_days = 1` — *PRD 4.2, note b*
- `round2` rounds half-up to the minor unit — *PRD 4.5*
- A downgrade never refunds: when `credit − charge` is positive it is reported as `balance_carry`, and `charge` is 0 — *PRD 4.3*
- `prorate(change: PlanChange, cycle: BillingCycle): Proration`; it reads no clock — the change date is an argument — *ADR-0007*

**Acceptance.**
- [ ] The five rows of table 3 in PRD 4.2 reproduce exactly (`toEqual` on `{credit, charge, balance_carry}`) — *PRD 4.2, table 3*
- [ ] A change on the last day of a 30-day cycle with `old_price = 30.00` gives `credit = 1.00` — *PRD 4.2, note b*
- [ ] Downgrade 50.00 → 10.00 with 15 of 30 days remaining gives `charge = 0` and `balance_carry = 20.00` — *PRD 4.3, example 2*
- [ ] Property: for every `remaining_days` in 1..`cycle_days`, `credit` and `charge` are non-negative and never exceed the respective full price — *PRD 4.2*
- [ ] `grep -rn "Date.now\|new Date()" src/billing` prints nothing — *ADR-0007*
- [ ] `npm run check` passes — *workflow 9*
- [ ] `npm run test:mutation` reports a score ≥ 85 and no lower than the score on the main branch — *ADR-0004*

**Verification.**
- `npm run check`
- `npm run test:mutation`

**Open questions.**
- none

**Risk.** normal
```
