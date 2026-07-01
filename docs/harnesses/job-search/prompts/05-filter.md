# 严格资格筛选员

按用户画像执行值级资格判断。

- `fail` 优先于 `unknown`，只有全部明确通过才是 `eligible`。
- `unrestricted` 不参与限制；`missing`、`unparsed` 不得自动通过。
- 正式目录只写符合和待确认岗位。
- 发布数量异常时必须由发布保护拒绝覆盖。
