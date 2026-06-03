# Go 通用风格规则

本文件只保留来自 Google Go Style 和 Uber Go Style Guide 的通用风格规则。它不用于发现并发、性能、逻辑或运行时风险。

## 格式和布局

- 使用 `gofmt` 作为最低要求；仓库已采用 `gofumpt` 时使用 `gofumpt`。
- 使用 `goimports` 将导入分为标准库、第三方和本地/项目导入。
- package 名称保持短、小写且有意义。避免 `util`、`common`、`misc`，也避免 `user.UserManager` 这类重复表达；能写成 `user.Manager` 时就不要重复。
- 文件按 package 职责保持内聚，不要按过宽的架构层随意切分。
- 生成代码和 `_test.go` 默认不参与 package 函数顺序检查，除非仓库明确要求纳入。

## 命名

- Go initialism 保持一致：`HTTP`、`ID`、`URL`、`JSON`、`SQL`、`API`、`TTL`、`RPC`。
- receiver 名称保持短且在同一类型内一致；避免 `this`、`self`，也避免损害清晰度的泛泛命名。
- interface 按行为命名，名称自然时使用 `Reader`、`Store`、`Validator` 或领域内等价名称。
- 避免不必要的导出。只有其他 package 必须使用时才导出。
- 不作为 package API 的函数必须以小写字母开头。

## API 形状

- 在能保持依赖小、测试简单时，接受 interface、返回具体类型。
- interface 尽量定义在消费者附近，除非它是有意共享的公共契约。
- interface 保持小。单方法 interface 可以接受，只要它表达真实行为。
- `context.Context` 放在 receiver 后的第一个参数。不要把 context 存进 struct。
- 不要用 `init` 做普通初始化；优先使用显式构造函数和依赖注入。

## 错误文案和日志风格

- 错误字符串以小写开头，不要以标点结尾。
- 错误包装和日志风格应与仓库已有模式一致。
- 避免同一层同时记录并返回同一个错误，除非仓库已有明确约定。

## Style Lint 期望

推荐 `golangci-lint` 风格覆盖：

- `gofmt`
- `goimports`
- `misspell`
- `revive`
- `whitespace`

可以按仓库情况调低噪声规则，但禁用规则时要在配置或代码中留下简短原因。
