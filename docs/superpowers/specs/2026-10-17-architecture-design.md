# 单商家购物小程序 · 架构设计规格

日期：2026-10-17
状态：待评审
关联文档：[README](../../../README.md)、[数据库设计](../../database-design.md)

## 一、背景与目标

给单个商家做一套自用的购物小程序，替代手工记价和手工记账。商家需要按客户设置不同的 SKU 价格，
让客户自己在小程序里看到「属于我的价格」并下单，商家线下用自己习惯的方式收款，收完之后在程序里
点一下确认，随时能看到今天、本周、这个月收了多少钱，以及谁还欠着多少。

## 二、范围

### 做

- 微信登录，客户与商家两种角色，共用一套小程序按角色分流
- 客户档案、分组、交付地址，商家可随时修改客户备注
- 商品分类、商品、SKU、默认价
- 客户专属价（按 SKU），支持设置与恢复默认价，价格变更留痕
- 购物车、下单、订单价格快照
- 订单查询、交付状态、**批量确认收款**、撤销确认
- 日 / 周 / 月营收看板，客户欠款与消费统计，客户对账单（实时查询）
- 价格变更记录

### 不做

- 在线支付、微信支付接口、支付回调与对账
- 收款金额记录：不记金额、不记方式、不分次收款、不记退款
- 库存与仓储管理
- 优惠券与促销引擎
- 多商家、多店铺
- 税务发票
- 社区、点赞、评论、分享
- 商家端 Web 后台（第一版在小程序内）
- 订单提交后的改价

## 三、已确认的关键决策

| # | 决策 | 说明 |
| --- | --- | --- |
| 1 | 商家身份 = 微信登录 + `role` 标记 | 第一个商家由初始化 SQL 指定 openid，系统不做密码登录 |
| 2 | 不实现支付功能 | 收款由商家线下完成，系统不记录收款金额、方式、退款 |
| 3 | 客户仍参与 | 客户可微信登录、查看自己的专属价、下单 |
| 4 | 收款 = 订单上的一次确认 | 商家点「确认收款」写入 `received_at`，支持批量勾选 |
| 5 | 营收口径 = 确认收款时间 | 不是下单时间；客户今天下单、商家明天确认，则计入明天的营收 |
| 6 | 专属价按 SKU 设定 | `customer_price` 唯一键为 `(customer_id, sku_id)` |
| 7 | 订单金额创建后冻结 | 任何改价都不回写已有订单，小票与统计只读快照 |
| 8 | 整单确认 | 不支持部分收款；确认错误则撤销确认并留审计日志 |
| 9 | 无「商家确认接单」环节 | 客户提交即生效，商家不接就取消该订单 |
| 10 | 跟踪「已交付」 | 先货后款场景下，交付与收款是两条独立的线 |
| 11 | 时间统一存 Asia/Shanghai 本地时间 | 只服务国内单商家；若将来出海需重做 |

## 四、总体架构

```
微信小程序（客户侧 + 商家侧，按角色分流）
        |  HTTPS
        v
   Nginx（443：TLS、静态图片、反代 /api）
        |
        v
  FastAPI 模块化单体（单进程、单库）
        |
        v
      MySQL 9
```

后端是**模块化单体**：一个进程、一个数据库，模块之间只能通过 service 接口互相调用，
禁止跨模块直接读写对方的表。不引入微服务、消息队列、支付网关。

## 五、仓库结构

单仓库（monorepo），后端与小程序并列：

```
demo/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/       配置、鉴权、依赖注入、异常、日志
│  │  ├─ db/         engine、session、Base
│  │  ├─ modules/
│  │  │  ├─ auth/        登录、角色、绑定
│  │  │  ├─ customer/    客户档案、分组、地址、备注
│  │  │  ├─ catalog/     分类、商品、SKU
│  │  │  ├─ pricing/     专属价、价格解析、变更记录
│  │  │  ├─ cart/        购物车
│  │  │  ├─ order/       订单、快照、批量确认收款
│  │  │  └─ report/      营收看板、客户统计
│  │  └─ alembic/        迁移脚本
│  └─ pyproject.toml
├─ miniprogram/
│  ├─ pages/             主包：login、bind、profile
│  ├─ packages/
│  │  ├─ shop/           客户侧分包
│  │  └─ admin/          商家侧分包
│  ├─ components/
│  ├─ services/
│  └─ app.ts / app.json
├─ docs/
└─ deploy/               Dockerfile、nginx、compose
```

每个后端模块内部固定五个文件：`router.py`、`schemas.py`、`service.py`、`repository.py`、`models.py`。

## 六、技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 |
| 数据库迁移 | Alembic |
| 数据库 | MySQL 9，utf8mb4，`utf8mb4_0900_ai_ci` |
| 鉴权 | 微信登录换取 JWT，无状态，有效期 2 小时，无 refresh token |
| 小程序 | 微信原生 + TypeScript |
| 部署 | Docker Compose + Nginx + Uvicorn（2 workers） |

**刻意不引入**（YAGNI，等真正需要再加）：

- **Redis**：JWT 无状态不需要服务端会话，微信登录走 `code2Session` 也不需要 `access_token` 缓存
- **对象存储 COS/OSS**：商品图直接存服务器磁盘，Nginx 托管静态目录，与 API 共用同一个 HTTPS 域名
- **PDF / Excel 导出**：对账单先给页面 + 可截图，避免中文字体与排版成本

## 七、后端模块划分

| 模块 | 职责 | 拥有的表 |
| --- | --- | --- |
| `auth` | 微信登录、签发校验 JWT、角色判定、客户绑定申请 | `user` |
| `customer` | 客户档案、分组、交付地址、备注、绑定审核 | `customer`、`customer_group`、`customer_address` |
| `catalog` | 分类、商品、SKU、上下架、图片上传 | `product_category`、`product`、`sku` |
| `pricing` | 专属价维护、价格解析、价格变更留痕 | `customer_price`、`price_change_log` |
| `cart` | 购物车读写 | `cart`、`cart_item` |
| `order` | 下单、价格快照、订单查询、批量确认收款 | `orders`、`order_item` |
| `report` | 日/周/月营收、客户欠款与消费统计 | 不拥有表，只读聚合 |

### 五条红线

1. **价格只有一个出口。** 任何地方想知道「某客户买某 SKU 多少钱」，只能调
   `pricing.resolve_price()` / `resolve_prices()`。`order` 模块禁止自己 join `customer_price`
   或读 `sku.default_price`。
2. **订单金额算一次就冻住。** 只有 `order.create_order()` 能计算并写入金额快照，
   此后任何路径都不允许回写订单金额，改价接口连订单表都不碰。
3. **模块之间只走 service。** 禁止跨模块 import 对方的 `models` / `repository`。
   `report` 是唯一例外：它是纯只读聚合，允许直接查库，但只允许 `SELECT`。
4. **客户数据隔离落在后端。** 所有返回订单、购物车、欠款的接口必须校验数据归属，
   一个地方漏掉就是客户看到别人的订单。
5. **改变金额归属的动作全部留痕。** 价格变更、订单取消、确认收款、撤销确认写 `audit_log`；
   交付状态变更不改金额，只记在 `orders.delivered_at` 上。

### 模块能力

- `auth`：`login_by_wx(code)`、`issue_token(user)`、`current_user()`
- `customer`：档案增删改查（含备注）、`approve_bind()`、`reject_bind()`、`get_by_user_id()`
- `catalog`：分类/商品/SKU 增删改查、`list_on_sale()`、图片上传
- `pricing`：`resolve_price()`、`resolve_prices()`、`set_customer_price()`、`reset_to_default()`、
  `list_customer_overrides()`
- `cart`：`get_or_create()`、`add_item()`、`update_qty()`、`remove_item()`、`clear()`
- `order`：`create_order()`、`list_orders()`、`get_order()`、`confirm_receipt(order_ids)`、
  `undo_confirm_receipt()`、`mark_delivered()`、`cancel()`
- `report`：`revenue_summary(day|week|month)`、`customer_debt()`、`customer_stats()`、`statement()`

**编排规则**：商品列表需要同时给出商品信息和「该客户的最终身价」，这属于展示层组装，
不属于任何单个模块。由 `router` 层先调 `catalog.list_on_sale()`，再调 `pricing.resolve_prices()`
批量补价，两个 service 互不依赖。

## 八、数据模型

完整字段定义见 [数据库设计](../../database-design.md)。本节只描述相对该文档的变更。

### 删除四组表

| 删除 | 理由 | 替代 |
| --- | --- | --- |
| `payment` | 不记录收款明细 | `orders.received_at` + `orders.received_by` |
| `receipt` | 小票就是订单详情页 | 订单号即小票号 |
| `statement`、`statement_item` | 对账单是一次实时查询，不是要归档的文档 | `report` 模块实时聚合 |
| `daily_sales_summary` | 营收直接聚合即可 | `report` 模块实时聚合，量大了再补 |

### 最终表清单（15 张）

`merchant`、`user`、`customer`、`customer_group`、`customer_address`、`product_category`、
`product`、`sku`、`customer_price`、`price_change_log`、`cart`、`cart_item`、`orders`、
`order_item`、`audit_log`。

### orders 最终结构

订单金额在下单时一次写入并冻结，之后只能改收款与交付状态，不能改金额。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | BIGINT UNSIGNED | 主键 |
| order_no | VARCHAR(32) | 订单号，唯一，对客户可见，即小票号 |
| customer_id | BIGINT UNSIGNED | 下单客户 |
| status | ENUM('pending','delivered','cancelled') | 订单业务状态 |
| total_amount | DECIMAL(12,2) | 下单时冻结的订单总额 |
| received_at | DATETIME NULL | 确认收款时间；为空表示未收款 |
| received_by | BIGINT UNSIGNED NULL | 确认收款的商家 |
| delivery_type | ENUM('pickup','delivery') | 自提或配送 |
| consignee | VARCHAR(50) | 收货人快照 |
| consignee_phone | VARCHAR(20) | 收货电话快照 |
| consignee_address | VARCHAR(255) | 收货地址快照 |
| remark | VARCHAR(255) | 客户下单留言 |
| idempotency_key | VARCHAR(64) | 幂等键，唯一 |
| placed_at | DATETIME | 下单时间 |
| delivered_at | DATETIME NULL | 交付时间 |
| cancelled_at | DATETIME NULL | 取消时间 |
| cancel_reason | VARCHAR(255) NULL | 取消原因 |

对比原设计**删除**：`received_amount`、`refund_amount`、`paid_amount`、`receivable_amount`、
`pay_status`、`delivery_status`、`confirmed_at`、`completed_at`。

索引：

- `UNIQUE(order_no)`、`UNIQUE(idempotency_key)`
- `INDEX(received_at)` —— 营收统计
- `INDEX(customer_id, received_at)` —— 客户欠款
- `INDEX(customer_id, placed_at)` —— 客户历史订单
- `INDEX(status, placed_at)` —— 商家订单列表筛选

### 状态表达

- 未收款：`received_at IS NULL`
- 已收款：`received_at IS NOT NULL`
- 欠款金额：该客户 `received_at IS NULL` 订单的 `total_amount` 之和
- 未完成：`status <> 'cancelled' AND received_at IS NULL`
- 已完成：`status = 'delivered' AND received_at IS NOT NULL`

### audit_log 动作

`price.change`、`order.cancel`、`order.confirm_receipt`、`order.undo_receipt`。

## 九、核心流程

### 9.1 登录与绑定

1. 小程序 `wx.login()` 拿 code，调 `POST /auth/login`
2. `auth` 用 code 换 openid，按 openid 查 `user`，没有则新建 `role=customer`
3. 已绑定客户档案 → 签发 JWT，进商城
4. 未绑定 → 返回 `need_bind`。**绑定前不返回任何商品**（没有客户身份无从算价）
5. 客户填姓名手机号提交绑定申请，状态 `pending`
6. 商家审核通过。**通过时按手机号匹配商家已建的客户档案**，匹配上则挂接，
   匹配不上才新建

约束：一个 `user` 只能绑一个 `customer`，一个 `customer` 只能被一个 `user` 绑定，双向唯一。
商家的 `user` 不参与绑定。

### 9.2 客户看价

1. 小程序请求商品列表
2. `router` 调 `catalog.list_on_sale()`
3. `router` 调 `pricing.resolve_prices(customer_id, sku_ids)`，**一次查询**取回这批 SKU 的专属价
4. `pricing` 逐条判定：`customer_price` 有记录用专属价，否则用 `sku.default_price`
5. 合并返回，每个 SKU 带 `final_price` 与 `price_source`

### 9.3 下单

1. 客户在确认页提交订单，带 `items` 与 `idempotency_key`
2. 先查幂等键，重复请求直接返回原订单
3. 调 `pricing.resolve_prices()` 重新算价
4. 与前端确认价比对，不一致返回 `409 PRICE_CHANGED` 与最新价格，客户重新确认
5. 一致则开事务：写 `orders`（冻结 `total_amount`）+ 写 `order_item` 全套快照
6. 清空购物车对应条目，返回订单号

快照字段：商品名、规格名、成交单价、数量、小计、价格来源。

下单时若 SKU 已停用或商品已下架，返回 `400 INVALID_ARGUMENT` 并指出具体 SKU，
客户调整购物车后再提交；同一订单内不允许出现重复 SKU。

### 9.4 批量确认收款

1. 商家勾选若干订单，调 `POST /admin/orders/confirm-receipt`
2. 开事务，`SELECT ... FOR UPDATE` 锁定这批订单
3. **跳过而非报错**：已确认的、已取消的、不存在的各记一个跳过原因
4. 其余写入 `received_at`、`received_by`
5. 写一条 `order.confirm_receipt` 审计日志，明细含订单号列表
6. 返回 `{confirmed: N, skipped: [{order_no, reason}]}`

撤销为单张操作：清空 `received_at` 与 `received_by`，写 `order.undo_receipt` 审计日志。
不提供「按客户一键全收」，批量必须人工勾选。

订单取消规则：客户只能取消 `status='pending'` 且 `received_at IS NULL` 的订单；
商家取消需要填写原因；已收款的订单不能直接取消，必须**先撤销确认收款**再取消，
否则返回 `409 ORDER_STATE_INVALID`。交付与收款互不阻塞，可任意先后。

### 9.5 营收统计

- 口径：按 `received_at` 落点统计
- 日 = 本地 00:00 至次日 00:00；周 = 周一到周日；月 = 自然月
- 营收 = 区间内订单 `total_amount` 之和
- 待收 = `received_at IS NULL` 的订单金额之和（可全局可按客户）
- 客户累计消费 = 该客户全部订单金额之和
- 全部为 `orders` 单表聚合，走 `(received_at)` 与 `(customer_id, received_at)` 索引

## 十、接口规范与鉴权

### 路径分三类

- `/api/v1/auth/*` —— 登录与绑定
- `/api/v1/me/*` —— 客户自己的资源
- `/api/v1/admin/*` —— 商家管理端

### 接口清单

| 模块 | 接口 |
| --- | --- |
| auth | `POST /auth/login`、`POST /auth/bind-apply`、`GET /auth/profile` |
| 客户·商品 | `GET /me/products`、`GET /me/products/{id}` |
| 客户·购物车 | `GET /me/cart`、`POST /me/cart/items`、`PATCH /me/cart/items/{sku_id}`、`DELETE /me/cart/items/{sku_id}` |
| 客户·订单 | `POST /me/orders`、`GET /me/orders`、`GET /me/orders/{order_no}`、`POST /me/orders/{order_no}/cancel` |
| 商家·客户 | `GET/POST /admin/customers`、`PATCH /admin/customers/{id}`、`GET /admin/customers/bind-requests`、`POST /admin/customers/{id}/approve-bind`、`.../reject-bind` |
| 商家·商品 | `GET/POST /admin/categories`、`GET/POST /admin/products`、`PATCH /admin/products/{id}`、`GET/POST /admin/products/{id}/skus`、`PATCH /admin/skus/{id}` |
| 商家·上传 | `POST /admin/uploads` —— 商品图上传，返回可访问 URL |
| 商家·价格 | `GET/PUT/DELETE /admin/customers/{id}/prices/{sku_id}`、`GET /admin/customers/{id}/prices`、`GET /admin/skus/{id}/prices`、`GET /admin/price-changes` |
| 商家·订单 | `GET /admin/orders`、`POST /admin/orders/confirm-receipt`、`POST /admin/orders/{order_no}/undo-receipt`、`POST /admin/orders/{order_no}/mark-delivered`、`POST /admin/orders/{order_no}/cancel` |
| 商家·报表 | `GET /admin/reports/revenue?period=day\|week\|month`、`GET /admin/reports/customer-debt`、`GET /admin/customers/{id}/statement` |

价格管理提供两个入口：从客户进入看「该客户所有 SKU 的价格」，从 SKU 进入看「该商品所有客户的价格」。

### 鉴权矩阵

JWT 放 `Authorization: Bearer`，payload 为 `sub`（user_id）、`role`、`exp`。

| 接口组 | 游客 | 已登录·未绑定 | 已绑定客户 | 商家 |
| --- | --- | --- | --- | --- |
| `/auth/login` | 可 | 可 | 可 | 可 |
| `/auth/bind-apply` | 否 | **可** | 否 | 否 |
| `/me/*` | 否 | 否 | **可** | 否 |
| `/admin/*` | 否 | 否 | 否 | **可** |

「未绑定」是独立状态，只有绑定申请一个权限，必须在鉴权层强制。

### 响应与错误

成功直接返回数据；列表为 `{items, total, page, page_size}`；错误为 HTTP 状态码 + `{code, message, detail}`。

| HTTP | code | 场景 |
| --- | --- | --- |
| 400 | `INVALID_ARGUMENT` | 参数不合法 |
| 401 | `UNAUTHENTICATED` | 未登录或 token 过期 |
| 403 | `FORBIDDEN` | 角色不足 |
| 403 | `CUSTOMER_NOT_BOUND` | 未绑定客户档案 |
| 404 | `NOT_FOUND` | 资源不存在，含「他人的订单」，不泄露存在性 |
| 409 | `PRICE_CHANGED` | 下单时价格变化，`detail` 带最新价格 |
| 409 | `ORDER_STATE_INVALID` | 订单当前状态不允许该操作（如已收款订单取消） |
| 422 | `VALIDATION_ERROR` | 字段校验失败 |

幂等：下单靠 `idempotency_key` 唯一索引兜底，重复提交返回原订单；批量确认天然幂等。
`GET /docs` 仅开发环境开放。

## 十一、小程序端结构

```
miniprogram/
├─ pages/                    主包：login、bind、profile
├─ packages/
│  ├─ shop/                  客户侧：products、product-detail、cart、checkout、orders、order-detail
│  └─ admin/                 商家侧：dashboard、customers、customer-detail、bind-requests、
│                            customer-prices、products、product-edit、sku-prices、orders
├─ components/               sku-picker、price-tag、order-card、empty-state
├─ services/                 request.ts + 各模块 api
├─ store/                    token、role、customerId、购物车角标
└─ utils/
```

- **分包理由**：主包限制 2MB，客户侧与商家侧各占一个分包，客户不下载商家代码
- **导航**：两角色需要不同 tab，使用**自定义 tabBar** 按 `role` 渲染；备选是客户用原生 tabBar、
  商家走宫格导航，但会牺牲客户侧体验
- **请求层**：`request.ts` 统一注入 token、统一错误提示、401 时重新 `wx.login()` 并重试一次
- **状态管理**：不引入状态库，全局只存 `token`、`role`、`customerId`、购物车角标；
  购物车明细以服务端为准
- **路由守卫**：每页 `onShow` 校验 token 与 role；未绑定是绑定页的唯一入口状态
- **金额**：前端只渲染后端返回值，不做任何计算

## 十二、部署与运维

- 一台 2C4G 服务器，Docker Compose 三个容器：`nginx`、`api`、`mysql`
- Nginx：终止 HTTPS、托管静态图片、反代 `/api`
- `api`：Uvicorn 2 workers
- 配置：`local` 与 `prod` 两套，`.env` + pydantic-settings；AppID/Secret、JWT 密钥、
  数据库密码全部走环境变量
- 微信侧前置：小程序 AppID + Secret，已备案的 HTTPS 域名并在小程序后台配置服务器域名白名单；
  **不需要微信支付商户号**
- 迁移：全部走 Alembic，禁止手工改库。初始迁移生成 15 张表；种子数据为一条 `merchant`
  记录与一条 `role=merchant` 的 `user`（openid 从环境变量读）
- 日志：结构化日志到 stdout + 文件，请求带 `request_id`；下单与确认收款打 info
- 备份：每天定时 `mysqldump` 落盘，保留 30 天。这是唯一容灾手段

## 十三、测试策略

`pytest` + FastAPI TestClient，跑在独立测试库上。按风险排序：

1. **价格解析**：专属价优先、无专属价回退默认价、恢复默认价后回退
2. **订单快照冻结**：下单后改价，订单金额与小票不变
3. **下单价格校验**：价格变化必须返回 `PRICE_CHANGED` 并带最新价
4. **幂等**：同一 `idempotency_key` 重复提交只产生一张订单
5. **批量确认收款**：混入已确认、已取消、不存在的订单，`confirmed` / `skipped` 必须准确
6. **权限隔离**：客户 A 取客户 B 的订单返回 404
7. **营收口径**：跨日、跨周、跨月边界正确

前端不做自动化测试，小程序侧手工验收。

## 十四、文档同步待办

`docs/database-design.md` 目前仍包含已废弃的 `payment`、`receipt`、`statement`、
`statement_item`、`daily_sales_summary` 五张表，以及 `orders` 的旧金额字段。
实现阶段需要同步该文档，使其与第 8 节一致。

## 十五、后续可选（不在第一版）

- 收款金额记录与部分收款（升级路径：新增 `payment` 表，`orders` 增加派生金额字段）
- 客户专属价批量导入、复制某客户价格表到另一个客户
- 按客户分组统一设置价格
- 专属价生效期
- 对账单 PDF / Excel 导出，订单小票打印
- 库存与可售数量
- 商家端 Web 后台
- Redis 缓存、对象存储
