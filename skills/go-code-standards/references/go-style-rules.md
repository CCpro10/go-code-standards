# General Go Style Rules

The Chinese project rules in `references/project-rules.zh.md` have the highest priority and must be followed completely. This file keeps only general Go style rules derived from Google Go Style and the Uber Go Style Guide. If this file conflicts with the project rules, follow the project rules.

This checklist condenses high-signal rules from:

- Google Go Style: https://google.github.io/styleguide/go/
- Google Go Style decisions: https://google.github.io/styleguide/go/decisions.html
- Google Go Style best practices: https://google.github.io/styleguide/go/best-practices.html
- Uber Go Style Guide: https://github.com/uber-go/guide/blob/master/style.md

## Formatting and Layout

- Use `gofmt` as the floor; use `gofumpt` when the repo has adopted it.
- Use `goimports` to group imports into standard library, third-party, and local/project imports.
- Keep package names short, lowercase, and meaningful. Avoid `util`, `common`, `misc`, and stutter such as `user.UserManager` when `user.Manager` is sufficient.
- Keep files cohesive by package responsibility, not by broad architectural layers.
- Generated files and `_test.go` files are exempt from package function ordering unless a repository explicitly opts in.

## Naming

- Use Go initialisms consistently: `HTTP`, `ID`, `URL`, `JSON`, `SQL`, `API`, `TTL`, `RPC`.
- Keep receiver names short and consistent within a type; avoid `this`, `self`, and generic receiver names when clarity suffers.
- Name interfaces by behavior when the name is natural, usually `Reader`, `Store`, `Validator`, or domain-specific equivalents.
- Avoid needless exported names. Export only what another package must use.
- Functions that are not intended as package API must start with a lowercase letter.

## API Design

- Accept interfaces and return concrete types when that keeps dependencies small and testing simple.
- Define interfaces near the consumer unless a shared public contract is intentional.
- Keep interfaces small. Single-method interfaces are fine when they model real behavior.
- Put `context.Context` as the first parameter after the receiver. Do not store contexts in structs.
- Do not use `init` for ordinary setup; prefer explicit constructors and dependency injection.

## Errors and Logging

- Handle every error. If intentionally ignored, make that explicit with a comment or a narrowly-scoped helper.
- Wrap errors with context using `%w` when callers may need `errors.Is` or `errors.As`.
- Start error strings with lowercase text and do not end them with punctuation.
- Avoid logging and returning the same error at the same layer; choose the boundary that owns observability.
- Use structured logging where the project already has it.

## Data, Slices, and Maps

- Prefer nil slices for zero values unless JSON/API output requires an empty array.
- Preallocate slices and maps when the size is known or easily estimated.
- Copy slices, maps, and byte buffers at API boundaries when retaining or exposing them could allow accidental mutation.
- Use `time.Duration`, `time.Time`, and typed constants instead of raw numeric units.

## Concurrency

- Every goroutine must have a lifecycle: cancellation, channel close, wait group, errgroup, or documented ownership.
- Prefer `errgroup` or explicit cancellation for coordinated goroutines.
- Avoid unbuffered goroutine fan-out without backpressure, limits, or cancellation.
- Stop tickers and timers. Close response bodies and files on all paths.
- Run `go test -race ./...` for concurrency-heavy changes when feasible.

## Testing

- Use table-driven tests for related cases.
- Keep tests in the same package unless black-box testing is intentional.
- Prefer behavior assertions over implementation detail assertions.
- Use `t.Helper()` in test helpers.
- Use `t.Cleanup()` for teardown.
- Cover errors, cancellation, nil/empty inputs, and boundary cases.

## Lint Expectations

Recommended `golangci-lint` coverage:

- Correctness: `govet`, `staticcheck`, `ineffassign`, `errcheck`, `errorlint`, `nilerr`.
- Maintainability: `revive`, `gocritic`, `unconvert`, `unparam`, `prealloc`.
- Style hygiene: `misspell`, `whitespace`, `gofmt`, `goimports`, `gofumpt` when adopted.
- Security and resources: `gosec`, `bodyclose`, `rowserrcheck`, `sqlclosecheck`.

Tune noisy linters per repository, but do not disable a rule without a short reason in config or code.
