# Go Style and Maintainability Rules

This file is the highest-priority rule set for the Go style Skill. It only handles style, readability, and maintainability. Assume the code logic is correct.

Do not use this Skill to find concurrency issues, suspicious bugs, performance problems, or business logic errors. Use `code-risk-review` for those risks.

## Priority

1. This file: highest priority.
2. `references/go-style-rules.md`: general Go style rules from Google Go Style and the Uber Go Style Guide.
3. Repository-local conventions: follow them only when they do not violate the first two layers.

## Directories and Packages

- Directory levels should express business modules and responsibility boundaries. Do not create directories around temporary implementation details, helper buckets, or overly deep technical layers.
- Package names should be short, lowercase, and meaningful. Avoid names such as `util`, `common`, and `misc` that do not express responsibility.
- Splitting files, moving directories, or splitting packages is a heavy structural change. During review, point out files with unfocused responsibilities or too many topics and suggest possible responsibility-based split directions, but do not perform file splitting or code moves without explicit user confirmation.
- In each package, the most important exported functions and methods should appear first, then other exported functions and methods, then unexported functions and methods.
- Treat the first unexported function or method as the start of the private section; do not place uppercase function or method names after it.
- Do not mark non-API functions as exported. Do not capitalize a function merely for cross-file calls, test convenience, or perceived importance.

## Structs

- Structs must be necessary, clear, and reduce understanding cost. Do not define many intermediate structs for temporary transformation, ad hoc assembly, or hiding the call chain.
- Before defining a struct, confirm that it expresses a stable business concept, external contract, persistent state, or reused data shape.
- If a shape is only used once to pass a few fields, assemble temporary parameters, or later overwrite fields, prefer explicit inputs, local variables, or direct construction of the target object.
- Field meanings, sources, and lifecycles must be clear. Do not define structs with unclear boundaries.
- Every exported struct must have a detailed comment that explains its business concept, purpose, boundary, lifecycle, or external contract.
- Every field in an exported struct must have a clear comment that explains its meaning, source, unit, boundary, or usage limit.
- Structs that are not part of the package API must not be capitalized/exported. Do not export a struct merely for cross-file use, test convenience, or perceived importance.

## Functions and Methods

- Function and method placement must be reasonable. A method should express receiver behavior or state change; if it has no real relationship with the receiver, prefer a plain function.
- Good code is short and direct first. If a small amount of sequential code is clear, do not split it into many one-off helpers.
- Do not extract helper functions for logic used only once. Extract only when a function reduces complexity, expresses a clear business concept, or is reused.
- Do not cut code into too many small functions. You may suggest splitting files by responsibility, but do not split files or move code before the user explicitly confirms.
- Avoid wrapper functions that only call one other function with the same arguments and directly return its result. They add call-stack depth and navigation cost without adding meaning. Keep such a wrapper only when it defines a stable API boundary, adapts an interface, adds validation, logging, error context, or real semantic conversion.
- Do not create meaningless function aliases such as `var afunc = packageb.Bfunc` or `var afunc = bfunc`. If the goal is only a shorter name, call the original function or use an import alias. If a new API boundary is truly needed, write a real commented function that adds semantic value.
- Function code must include informative comments. Simple functions should explain business intent, input boundaries, or return semantics; complex functions should explain key branches, state changes, or constraints.
- Comments must not merely restate code. Avoid comments such as “assign value” or “call method”.

## Local Readability

- Declare variables as late as practical. If a variable may remain unused because a later step can fail, declare it after that fallible step.
- Return empty structs and nil values explicitly on failure. For example, return `dailyLoginRewardConfig{}` instead of declaring an empty variable early only to reuse it on failure paths.
- For large business structs, prefer keyed composite literals that construct the complete object in one place.
- Avoid declaring an empty struct and assigning fields one by one unless an API or control flow requires mutation.
- Use reasonable blank lines and line breaks to make logic phases easy to scan.

## Naming and Boundary Expression

- Names must reveal what code actually does. Avoid using `normalizeXxx` to hide trimming, filtering, deduplication, defaulting, and reshaping in one vague operation.
- If parsing, deduplication, validation, or conversion is required, name the function after the real action, such as `parseXxx`, `dedupeXxx`, or `validateXxx`.
- Do not create meaningless constant aliases such as `taskQueryStatePending = SongResultStatePending`. If two names represent the same state, enum value, or business concept, use the original constant directly. Do not introduce an equal-value constant merely for local naming, call convenience, or superficial layering.
- Business objects should be constructed from explicit input. Do not create a “default business object” and then overwrite it into a different meaning through branches.
- Do not add meaningless fallback or normalization for internal engineering parameters inside business flow, such as `normalizeAudioParseSyncTimeout` silently replacing invalid timeout, poll interval, or retry limit values with defaults or caps. Internal configuration must be decided and validated once at construction, startup, or config-loading boundaries. If internal code passes an invalid value, expose a clear error or fix the call site instead of adding fallback logic on every execution path.
- Defaults are allowed only at explicit boundaries: external request parsing, config loading, compatibility adapters, or constructors. The default source, scope, and limit must be obvious. Do not hide defaults inside deep helpers, service methods, or repeated loop paths.

## Pointer Helpers

- Do not write `stringPtr`, `int64Ptr`, `boolPtr`, or similar pointer helpers by hand. Use `gptr.Of(...)` from `code.byted.org/lang/gg/gptr`.
- Be careful with type inference when passing numeric constants to `gptr.Of`. Use `gptr.Of[int64](...)` or `gptr.Of[int32](...)` when the result must be `*int64`, `*int32`, or another explicit numeric pointer type.
