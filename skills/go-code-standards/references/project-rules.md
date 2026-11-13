# Go Expression Rules (Highest Priority)

The Chinese version is authoritative; keep this English mirror semantically aligned. Review local expression and Go conventions only.

- Names must express actual responsibility, object, action and result. Prefer shorter unambiguous names; use consistent established abbreviations such as Req, Resp, Config and Ctx.
- Name slices/arrays/lists after plural concrete business elements, such as userIDs, orders and skillRefs. Maps use key2value, such as userID2user. Generic list, items, data and mapping names hide meaning.
- Package-private non-API functions, methods and structs start lowercase. Cross-file calls within a package require no export; methods required by a public interface contract are an exception.
- Put important exported functions first, other exported functions next, private functions last. Do not export merely to satisfy ordering.
- Functions need informative process-oriented comments. Explain key steps, conditions and boundaries for complex functions; for example, first parse the advanced-creation title, then use the inspiration title if absent.
- Exported structs need detailed meaning, purpose and boundary comments; fields explain meaning, source, units and limits.
- Declare variables after fallible steps and close to first use. Return explicit empty structs or nil on failure. Construct large structs with keyed composite literals rather than incremental field filling.
- Use meaningful documented constants for business states and protocol values rather than raw strings. Duplicate constant declarations belong to abstraction review.
- Break parameters, fields and logic phases into readable lines. Keep package names concise and meaningful.
- Use code.byted.org/lang/gg/gptr and gptr.Of, with explicit numeric types such as gptr.Of[int64](...) when needed; do not hand-write pointer helpers.
- Suggest file splits and directory moves; perform them only when the user explicitly authorizes them.
- Apply these rules before general Go guidance and non-conflicting project conventions. Current explicit user instructions take precedence.

Route data design, function values/types, thin wrappers, orchestration, fallback contracts and concrete failures to their respective specialties.
