# Go 代码规则

中文版本是本规则集的基准。英文版本必须与中文版本保持同步；当规则发生冲突时，以中文版本为准。

本清单浓缩自：

- Google Go Style: https://google.github.io/styleguide/go/
- Google Go Style decisions: https://google.github.io/styleguide/go/decisions.html
- Google Go Style best practices: https://google.github.io/styleguide/go/best-practices.html
- Uber Go Style Guide: https://github.com/uber-go/guide/blob/master/style.md

## 格式和布局

- 使用 `gofmt` 作为最低要求；仓库已采用 `gofumpt` 时使用 `gofumpt`。
- 使用 `goimports` 将导入分为标准库、第三方和本地/项目导入。
- package 名称保持短、小写且有意义。避免 `util`、`common`、`misc`，也避免 `user.UserManager` 这类重复表达；能写成 `user.Manager` 时就不要重复。
- 文件按 package 职责保持内聚，不要按过宽的架构层随意切分。
- 在每个 package 中，可导出的 package-level 函数和方法必须位于不可导出的函数和方法之前。
- 将第一个不可导出的函数或方法视为 private section 的开始；其后不要再放大写开头的函数或方法。
- 生成代码和 `_test.go` 默认不参与 package 函数顺序检查，除非仓库明确要求纳入。
- 变量尽量延后声明。如果一个变量可能因为后续校验或依赖调用失败而没有机会使用，就把声明移动到这个失败点之后。
- 大业务结构体优先使用 keyed composite literal，让完整对象形状集中出现在一个地方。除非 API 或控制流确实需要可变赋值，不要先声明空结构体再逐字段赋值。

## 命名

- Go initialism 保持一致：`HTTP`、`ID`、`URL`、`JSON`、`SQL`、`API`、`TTL`、`RPC`。
- receiver 名称保持短且在同一类型内一致；避免 `this`、`self`，也避免损害清晰度的泛泛命名。
- interface 按行为命名，名称自然时使用 `Reader`、`Store`、`Validator` 或领域内等价名称。
- 避免不必要的导出。只有其他 package 必须使用时才导出。
- 不作为 package API 的函数必须以小写字母开头。

## API 设计

- 在能保持依赖小、测试简单时，接受 interface、返回具体类型。
- interface 尽量定义在消费者附近，除非它是有意共享的公共契约。
- interface 保持小。单方法 interface 可以接受，只要它表达真实行为。
- `context.Context` 放在 receiver 后的第一个参数。不要把 context 存进 struct。
- 不要用 `init` 做普通初始化；优先使用显式构造函数和依赖注入。

## 边界和规范化

- 系统边界要清晰。必填业务输入必须在请求解析、构造期或 service 入口校验，不要在深层业务逻辑中静默修复。
- 避免含糊的 `normalizeXxx` 函数同时做 trim、过滤、去重、默认值补齐和数据重塑。函数名应暴露真实操作，例如 `validateSkillRefs`、`dedupeSkillRefs` 或 `parseSkillRefs`。
- 不要通过静默清洗让系统同时接受合法和非法业务输入。空必填字段、畸形标识、不合法状态、缺失依赖和错误调用顺序都应尽早暴露为清晰错误。
- 只有当 normalization 是明确接口契约的一部分时才使用，例如修剪 UI 文本、保持向后兼容或规范化文档化的外部表示。
- 确实需要 normalization 时，把它放在靠近边界的位置，并让范围一眼可见：改了哪些字段、哪些非法输入会失败、接受哪些兼容形式以及为什么。
- 除非跳过是明确的业务规则，否则不要用 `continue` 丢弃非法业务数据。对于 `SkillKey` 这类必填字段，优先返回错误，而不是静默过滤。
- 当校验和转换都重要时，拆清楚两者。执行校验的函数不应同时改变业务语义，除非函数名和返回类型让这个契约非常明确。
- 优先显式失败，不要使用只是为了避免报错而存在的 fallback。降级必须是设计出来的业务能力，而不是运行时逃生通道。

## 错误和日志

- 处理每一个错误。如果有意忽略，使用注释或窄作用域 helper 明确说明。
- 当调用方可能需要 `errors.Is` 或 `errors.As` 时，使用 `%w` 包装错误并补充上下文。
- 错误字符串以小写开头，不要以标点结尾。
- 避免在同一层同时记录并返回同一个错误；选择真正拥有可观测性职责的边界。
- 项目已有结构化日志时，继续使用结构化日志。

## 数据、Slice 和 Map

- 零值优先使用 nil slice，除非 JSON/API 输出要求空数组。
- 已知或容易估计大小时，预分配 slice 和 map。
- 在 API 边界保留或暴露 slice、map、byte buffer 时，根据需要复制，避免意外修改。
- 使用 `time.Duration`、`time.Time` 和有类型常量，不要使用裸数字表达时间单位。

## 并发

- 每个 goroutine 都必须有生命周期：取消、关闭 channel、wait group、errgroup 或明确的所有权说明。
- 协调多个 goroutine 时优先使用 `errgroup` 或显式取消。
- 避免没有背压、限制或取消机制的无界 goroutine fan-out。
- 停止 ticker 和 timer。所有路径上关闭 response body 和文件。
- 对并发相关改动，在可行时运行 `go test -race ./...`。

## 测试

- 相关 case 使用表驱动测试。
- 除非有意做黑盒测试，否则测试放在同一个 package。
- 优先断言行为，不要过度断言实现细节。
- 测试 helper 使用 `t.Helper()`。
- 清理逻辑使用 `t.Cleanup()`。
- 覆盖错误、取消、nil/empty 输入和边界情况。

## Lint 期望

推荐 `golangci-lint` 覆盖：

- 正确性：`govet`、`staticcheck`、`ineffassign`、`errcheck`、`errorlint`、`nilerr`。
- 可维护性：`revive`、`gocritic`、`unconvert`、`unparam`、`prealloc`。
- 风格卫生：`misspell`、`whitespace`、`gofmt`、`goimports`，仓库采用时使用 `gofumpt`。
- 安全和资源：`gosec`、`bodyclose`、`rowserrcheck`、`sqlclosecheck`。

可以按仓库情况调低噪声规则，但禁用规则时要在配置或代码中留下简短原因。
