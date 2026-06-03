# General Go Style Rules

This file keeps only general style rules derived from Google Go Style and the Uber Go Style Guide. It is not for finding concurrency, performance, logic, or runtime risks.

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

## API Shape

- Accept interfaces and return concrete types when that keeps dependencies small and testing simple.
- Define interfaces near the consumer unless a shared public contract is intentional.
- Keep interfaces small. Single-method interfaces are fine when they model real behavior.
- Put `context.Context` as the first parameter after the receiver. Do not store contexts in structs.
- Do not use `init` for ordinary setup; prefer explicit constructors and dependency injection.

## Error Text and Logging Style

- Start error strings with lowercase text and do not end them with punctuation.
- Error wrapping and logging style should match the repository's existing pattern.
- Avoid logging and returning the same error at the same layer unless the repository has an explicit convention.

## Style Lint Expectations

Recommended `golangci-lint` style coverage:

- `gofmt`
- `goimports`
- `misspell`
- `revive`
- `whitespace`

Tune noisy linters per repository, but leave a short reason when disabling a rule.
