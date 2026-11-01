# 前端与网关排障

本分支将入口从frontend移至gateway；首次安装说明见[独立交付](split-delivery.md)。新frontend是纯静态镜像，独立启动不要求backend在线。历史服务器端口配置不能直接套在新静态前端上。

## 端口和健康

frontend和gateway均监听容器内8080，但只有gateway发布WEB_PORT（默认127.0.0.1:48080）。已有宿主80/48080映射应在经授权的拓扑维护时移到gateway，不发布backend。容器健康只验证内部端口，不证明宿主映射、API、数据库或AI。

## 定位

- 页面可达、API404：确认浏览器访问gateway，而不是直接暴露的frontend。检查VITE_API_BASE_URL构建值及gateway的/api路由。
- 首次切换连接失败：检查gateway实际PortBindings、nginx.conf只读挂载权限和容器8080监听；不要因此开放backend端口。
- 单端重建后短暂502：网关Docker DNS缓存有效5s；超过重试窗口仍失败则检查同一网络、service alias与gateway日志，不靠重新发布另一组件恢复。
- 缺static/media：检查backend收集/写入目录、原命名卷和gateway只读挂载；frontend不承担这些文件。不要创建空卷代替原用户数据。
- SSE整段返回：检查gateway聊天精确路由的proxy_buffering off、proxy_cache off和300s超时，以及外层反代；合成runner测试不证明真实模型速度。
- company-api503：仍表示独立企业服务未配置，不等同于Django整体故障。
- 页面没更新：确认frontend运行digest、index.html no-store以及assets版本；VITE_*只能重建生效。

仅前端镜像回滚/更新使用单组件digest脚本；不要重建backend或gateway。若修改gateway端口/配置，那是网关维护，仅在明确授权后对gateway使用--no-deps重建。排查不要输出Config.Env、真实.env、登录凭据或未脱敏日志。

验证/login、注册登录、无Token业务API401、静态/媒体、SSE与另一组件ID；容器健康、浏览器和真实模型分别记录。服务器只读 HTTP 核验与浏览器验收分别记录，见[部署状态](deployment-status.md)。
