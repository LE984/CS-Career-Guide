# Watchtower 与单服务回滚

旧成对回滚说明自 2026-11-01 由[独立交付](split-delivery.md)替代。2026-10-26 观察到的 Actions/Watchtower 状态是历史，本轮未查询或操作服务器。

## 更新入口协调

Watchtower仍默认置于updates profile，只有backend/frontend带enable标签，gateway/mysql不自动更新。两个独立镜像仓库可分别更新latest；发布一端不触碰另一仓库。Watchtower使用Docker socket，拥有宿主机管理能力，必须单独接受并协调，不能同时与Actions管理同一组件。

回滚前关闭目标DEPLOY_FRONTEND_ENABLED或DEPLOY_BACKEND_ENABLED，确认已启动的Job退出，再协调停止Watchtower。若有旧式成对同步则同时关闭DEPLOY_ENV_SYNC_ENABLED。变量变更不取消已运行Job，远端锁不替代更新入口协调。

只有经授权才在管理机修改对应开关，例如：

```bash
gh variable set DEPLOY_FRONTEND_ENABLED --body false --repo vacontinuejatotired/CS-Career-Guide
```

普通发布/回滚不会启动、停止或重建Watchtower。其凭据目录只保存本项目ACR登录，默认/etc/cs-career-guide/acr，以只读/config和DOCKER_CONFIG=/config挂载。network_mode=bridge允许出站检查，不映射宿主端口；只读socket也不限制Docker API管理能力。

## 单端digest回滚

从对应组件完整发布记录获取images.<组件>.reference，确认complete=true。无需同一次成对发布，但必须核对目标版本的API/schema兼容。SHA tag、latest均可覆盖，不能代替digest。

在已安装新拓扑的服务器，用deploy_component.py --component frontend或backend --image完整digest；具体可复制命令和文件前提见[独立交付](split-delivery.md#单服务部署与-digest-回滚)。脚本只pull/recreate目标服务，使用--no-deps --no-build --pull never，保留另一组件pin、容器、网关和数据卷，手动回滚也不更新AI/.env。

精确版本持久化到docker-compose.<组件>-image.json。后续手工Compose必须显式加载已存在的pin文件；只编辑BACKEND_TAG/FRONTEND_TAG不会覆盖pin。旧docker-compose.digest.yml仍提供同时维护两端的入口，但不作为日常单服务回滚流程；不能用它的双端必填误导为单端必须成对回滚。

config/pull失败保留原文件；健康失败保留新pin并报错，需私下诊断。后端入口的迁移、静态文件和数据兼容需提前核对；不会降级数据库或删除卷。旧监听80或内置网关的前端镜像，需评估其与新部署配置的兼容，不能直接跨拓扑回滚。

## 恢复更新

完成目标digest和业务验证后再恢复对应分端开关。若改用Watchtower跟踪latest，应先确定管理入口，明确将该端pin切回所需引用并重建该端；仅启动Watchtower或编辑tag不会改变现存容器。不要恢复另一组件的更新来完成单端操作。

可在服务器私下查看选定服务的日志、docker compose ps和容器.Config.Image/.Image；本地镜像ID不是Registry manifest digest。发布记录digest与容器健康、真实模型/浏览器验收分别核验。生产回滚演练尚未执行。
