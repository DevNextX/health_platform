# AKS MQTT LoadBalancer 连接数上不去（`ECONNREFUSED`）复盘

日期：2025-12-26

## 现象（Symptoms）
- AKS 中暴露 MQTT 服务，Kubernetes `Service` 类型为 `LoadBalancer`（Public）。
- 外部客户端（同 VNet 或公网 VM）使用 MQTTX / `mqttx bench conn` 压测时，大量报错：`connect ECONNREFUSED <public-ip>:<port>`，连接数无法提升。
- 集群内部（在另一个 Node 上）对同一个 Public LB 地址压测，可建立更多连接（例如 `50/50 Connected`）。

## 环境与关键配置（Environment）
- AKS 网络：Azure CNI Overlay。
- MQTT Service：
  - `spec.type: LoadBalancer`
  - `spec.externalTrafficPolicy: Local`（问题发生时）
  - `spec.ports[].port: 33882`
  - `spec.ports[].nodePort: 30711`
  - `spec.healthCheckNodePort: 31348`
- 业务容器对外提供两个入口：
  - MQTT（33882）
  - HTTP 健康检查（30000，路径 `/api/iot/broker/healthcheck`）
- Azure Portal（Load Balancer -> Health probes）观测到：
  - 负载均衡规则（33882）实际使用的健康探针为 **HTTP:30000**（而不是 `healthCheckNodePort=31348`）。

## 关键证据（Evidence）
- 外部压测出现 `ECONNREFUSED`：通常意味着目标端口在某一跳返回 TCP RST（被明确拒绝），而非网络黑洞/超时。
- 曾将 MQTT Service 临时切换为 `externalTrafficPolicy: Cluster` 后，外部压测连接恢复正常（作为对照验证）。
- 在 `externalTrafficPolicy=Local` 且只有 1 个 Pod 的情况下，按理应只有 **Pod 所在 Node** 才能接入 NodePort；如果 LB 仍把流量分发到其它 Node，会触发拒绝。

## 根因分析（Root Cause）
### 1. `externalTrafficPolicy: Local` 的实际含义
- Azure Load Balancer 的 backend pool 以 **Node（VMSS 实例）** 为粒度，不认识 Pod。
- `externalTrafficPolicy: Local` 要求：只有 **本机有 Endpoint（Pod）** 的 Node 才应接收来自 LB 的流量；其它没有 Endpoint 的 Node 会直接拒绝（RST），客户端表现为 `ECONNREFUSED`。
- Kubernetes 为此会生成 `healthCheckNodePort`（本例为 31348），用于让 LB 的 health probe 仅把“有本地 Endpoint 的 Node”判为健康。

### 2. 健康探针与业务端口的“错配”导致 LB 选择了错误的 Node
- 该 MQTT Service 希望通过 `Local` 保留客户端源 IP。
- 但 LB 的 33882 规则 **没有使用 31348** 作为健康判定依据，而是绑定到了 **HTTP:30000** 的探针。
- 由于 30000 这个 HTTP 健康检查在多个 Node 上都能被判为成功（例如该 30000 对应的 Service 使用 `externalTrafficPolicy: Cluster`，使得任意 Node 都能转发到 Endpoint），导致 LB 认为 **多个 Node 都健康**。
- LB 于是把 MQTT 流量分发到那些实际上 **没有 MQTT Pod Endpoint** 的 Node。
- 这些 Node 在 `externalTrafficPolicy=Local` 语义下对 `nodePort=30711` 进行拒绝，外部客户端出现大量 `ECONNREFUSED`。

> 总结：问题核心是 **LB 的健康探针与 MQTT `Local` 语义不一致**，导致 LB 没有按“是否有本地 Endpoint”过滤 Node。

## 为什么“集群内压测更容易成功”
- Azure LB 的分流通常基于 5 元组哈希（源 IP/源端口/目的 IP/目的端口/协议）。
- 不同来源（外部 VM vs 集群内部 Node）会形成不同的 5 元组分布，可能更集中命中“正确的 Node”（有 Endpoint 的 Node），因此出现“内部看起来没问题、外部明显失败”的差异。

## 解决方案（Fix）
最终方案并非修改 MQTT Service 为 `Cluster`（会丢失客户端源 IP），而是**让用于 LB 探测的 HTTP 健康检查入口（30000）与 MQTT 的 `Local` 语义保持一致**：

- 保持 MQTT Service：`spec.externalTrafficPolicy: Local`（用于保留客户端源 IP）。
- 将 **30000 端口对应的健康检查 Service** 的 `spec.externalTrafficPolicy` 也修改为 `Local`。

效果：
- 由于 33882 的 LB rule 实际使用的是 **HTTP:30000** 的 probe，修改后只有“本机有 Endpoint（Pod）”的 Node 才会在 30000 上返回健康（例如 `200 OK`）。
- LB 因而只会把 33882（MQTT）流量转发到真正有本地 Endpoint 的 Node，避免命中无 Endpoint Node 导致 `ECONNREFUSED`。
- 同时保留 MQTT `Local` 带来的源 IP 保留能力。

补充：
- 将 MQTT Service 临时改为 `Cluster` 仍是一个有效的对照验证/应急手段，但不满足“保留源 IP”的业务需求。

## 经验教训（Lessons Learned）
- 对于 **单 Pod + Public LoadBalancer** 的场景，`externalTrafficPolicy: Local` 风险很高：
  - 只要 LB 的健康探针不能严格按“本机有 Endpoint”筛 Node，就会出现“部分连接拒绝”。
- 自定义/复用健康探针（例如把 L4 MQTT 规则绑定到 HTTP:30000 探针）要非常谨慎：
  - 若 30000 对应的 Service 使用 `externalTrafficPolicy: Cluster`，探针可能在无本地 Endpoint 的 Node 上也返回成功，从而破坏 `Local` 的假设。
- 若业务必须保留源 IP（坚持 `Local`），建议：
  - 确保 LB health probe 的“判健康条件”与 `Local` 的“本机有 Endpoint”语义一致；
  - 若必须复用业务容器内的 HTTP 健康检查端口（如 30000），则该端口对应的 Service 也应采用 `externalTrafficPolicy: Local`（或确保无 Endpoint Node 探测失败）。

## 复现与验证步骤（Repro / Verification）
1. 设置 `externalTrafficPolicy: Local`，并确保仅 1 个 Pod（单节点有 Endpoint）。
2. 从外部 VM 压测 `mqttx bench conn -c 50 ...`，观察 `ECONNREFUSED`。
3. 在 Azure Portal 查看 Load Balancer：
   - 确认 33882 规则使用的 probe 端口/路径（本案为 HTTP:30000）。
4. 将 30000 健康检查 Service 的 `externalTrafficPolicy` 改为 `Local` 后重测：
  - 预期外部 `ECONNREFUSED` 消失或显著降低；
  - 同时 MQTT 仍可保留客户端源 IP。

## 备注：关于“按节点池绑定/过滤”的讨论
- Azure Load Balancer 后端池默认以 Node（VMSS 实例）为粒度加入，不支持直接“按 nodepool 过滤探针”。
- Kubernetes 的 `node.kubernetes.io/exclude-from-external-load-balancers` 标签的语义是：将该 Node 排除在 **外部 LoadBalancer 后端候选** 之外；
  - Pod 仍然可以调度到这些 Node 上；
  - 只是这些 Node 不会作为外部 LB 的后端接入点。
