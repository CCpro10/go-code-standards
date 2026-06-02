# Go Project Rules

The Chinese file `references/project-rules.zh.md` is the highest-priority source of truth and must be followed completely. Keep this English version synchronized with it. If this file, the general Go style rules, or local habits conflict with the Chinese project rules, follow the Chinese project rules.

These rules come from user requirements for real Go business code. The goal is explicit boundaries, explicit failure, short and direct logic, and readable naming and structure.

## Priority

1. This project rule set: highest priority and mandatory.
2. `references/go-style-rules.md`: general Go style rules from Google Go Style and the Uber Go Style Guide.
3. Repository-local conventions: follow them only when they do not violate the first two layers.

## Boundaries and Failure

- Do not keep “theoretically impossible” branches in business methods. Missing dependencies, missing configuration, and invalid constructor arguments should fail at startup or construction time. Do not make every RPC method return runtime fallback responses such as `not implemented`.
- Do not make one piece of logic accept too many unclear input sources. Missing fields, invalid states, uninitialized dependencies, and wrong call ordering should fail early with clear errors instead of continuing.
- Degradation must be an explicitly designed business capability. If fallback exists only to avoid an error, prefer explicit failure.
- Trust the boundary of called functions. If a called function can return an invalid result, it should return an error internally instead of forcing the outer layer to add blind fallback checks.
- Log meaningful context for important failure paths and wrap errors so the call chain preserves business context.

## Inputs, Defaults, and Normalization

- Do not hide trimming, filtering, deduplication, defaulting, and reshaping behind vague `normalizeXxx` functions. Function names must reveal the real operation, such as `validateSkillRefs`, `dedupeSkillRefs`, or `parseSkillRefs`.
- Do not let the system accept both valid and invalid business inputs. Required business fields must be validated at request parsing, construction, or service entry. Invalid inputs should fail clearly, not be silently repaired deep in business logic.
- Do not use vague defaults to hide the call chain. If a request field is part of business semantics, such as `occurred_at`, the caller must pass it explicitly and the entry point must validate it. Do not silently fall back to `time.Now()` inside a service.
- Business configuration should be explicitly declared. Unless an interface contract, product rule, or technical plan explicitly requires a default, do not fill missing business configuration with code defaults.
- Defaults are allowed only for non-business engineering parameters or documented compatibility behavior. Fill defaults near entry validation, and make the source, default policy, and scope visible.
- Do not drop invalid business data with `continue` unless skipping is a documented business rule. For required fields such as `SkillKey`, prefer returning an error over silently filtering the item.
- Separate validation from transformation when both matter. A function that validates should not also mutate semantics unless its name and return type make that contract obvious.

## Construction and Local Variables

- Return empty structs and nil values explicitly on failure. For example, return `dailyLoginRewardConfig{}` instead of declaring an empty variable early only to reuse it on failure paths.
- In a function, if a variable may remain unused because a later step can fail, do not declare it yet. Declare it after that fallible step.
- Do not first construct a “default business object” and then overwrite it into another semantic meaning through branches. Business objects should be parsed from explicit input; missing input should fail.
- For large business structs, prefer keyed composite literals that construct the complete object in one place. Avoid declaring an empty struct and assigning fields one by one unless an API or control flow requires mutation.

## Functions, Files, and Splitting

- Good code is short and direct first. If a small amount of sequential code is clear, do not split it into many one-off helpers, and do not introduce verbose normalization layers just to “remove branches”.
- Do not extract extra helper functions for logic used only once. Extract only when a function reduces complexity, expresses a clear business concept, or is reused in multiple places.
- Do not cut code into too many small functions. Prefer splitting files by responsibility, then keep a small number of business-meaningful functions.
- Functions need necessary comments. Comments should explain business intent, failure boundaries, or key constraints. Do not write low-information comments such as “assign value to variable”.
- Important business logic should have meaningful logs.
- Use reasonable blank lines and line breaks to make logic phases clear.

## Package and Naming

- In each package, exported package-level functions and methods must appear before unexported package-level functions and methods.
- Treat the first unexported function or method as the start of the private section; do not place uppercase function or method names after it.
- Functions that are not intended as package APIs must start with a lowercase letter.

## Pointer Helpers

- Do not write `stringPtr`, `int64Ptr`, `boolPtr`, or similar pointer helpers by hand. Use `gptr.Of(...)` from `code.byted.org/lang/gg/gptr`.
- Be careful with type inference when passing numeric constants to `gptr.Of`. Use `gptr.Of[int64](...)` or `gptr.Of[int32](...)` when the result must be `*int64`, `*int32`, or another explicit numeric pointer type.
