# Assignment 3 架构设计文档

## 📐 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     CloudFormation Stacks                    │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ StorageStack (基础设施层)                              │ │
│  │  ├─ S3 Bucket (自动生成名称)                          │ │
│  │  └─ DynamoDB Table                                     │ │
│  │      ├─ Partition Key: bucket_name                     │ │
│  │      ├─ Sort Key: timestamp                            │ │
│  │      └─ GSI: timestamp-index                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                             ↓ ↓ ↓                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ SizeTrackingStack (监控层)                            │ │
│  │  └─ Lambda Function                                    │ │
│  │      ├─ Triggered by: S3 Events                        │ │
│  │      ├─ Runtime: Python 3.9                            │ │
│  │      ├─ Timeout: 1 min                                 │ │
│  │      └─ Permissions: S3 Read + DynamoDB Write          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ PlottingStack (可视化层)                              │ │
│  │  ├─ Lambda Function                                    │ │
│  │  │   ├─ Runtime: Python 3.9                            │ │
│  │  │   ├─ Memory: 512 MB                                 │ │
│  │  │   ├─ Timeout: 1 min                                 │ │
│  │  │   ├─ Layer: matplotlib                              │ │
│  │  │   └─ Permissions: DynamoDB Read + S3 Write          │ │
│  │  └─ API Gateway                                        │ │
│  │      ├─ Type: REST API                                 │ │
│  │      ├─ Endpoint: /plot (GET)                          │ │
│  │      └─ Integration: Lambda Proxy                      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ DriverStack (测试层)                                  │ │
│  │  └─ Lambda Function                                    │ │
│  │      ├─ Runtime: Python 3.9                            │ │
│  │      ├─ Timeout: 2 min                                 │ │
│  │      └─ Permissions: S3 Read/Write/Delete              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 数据流动

### 正常操作流程

```
1. 用户上传文件到 S3
   ↓
2. S3 触发事件 → Size-tracking Lambda
   ↓
3. Lambda 计算 bucket 总大小
   ↓
4. 写入 DynamoDB (bucket_name, timestamp, total_size, object_count)
   ↓
5. 用户调用 Plotting API
   ↓
6. Plotting Lambda 从 DynamoDB Query 数据
   ↓
7. 生成 matplotlib 图表
   ↓
8. 保存 plot 到 S3
```

### Driver Lambda 测试流程

```
1. 手动触发 Driver Lambda
   ↓
2. 执行 4 个 S3 操作:
   - 创建 assignment1.txt (18 bytes)
   - 更新 assignment1.txt (27 bytes)
   - 删除 assignment1.txt (0 bytes)
   - 创建 assignment2.txt (2 bytes)
   ↓
3. 每个操作触发 Size-tracking Lambda
   ↓
4. Driver 调用 Plotting API
   ↓
5. 生成包含 4 个数据点的图表
```

---

## 🏗️ Stack 设计理念

### 为什么分成 4 个 Stacks？

#### 1. **StorageStack** - 基础设施层

**职责**: 提供基础存储资源

**包含资源**:

- S3 Bucket
- DynamoDB Table + GSI

**独立的原因**:

- 这些是最基础的资源，其他所有服务都依赖它们
- 存储资源通常生命周期较长，很少修改
- 便于跨多个应用共享（如果需要）

**优势**:

- 可以单独更新其他 stacks 而不影响存储
- 数据持久性更好

#### 2. **SizeTrackingStack** - 监控层

**职责**: 实时监控 S3 bucket 大小变化

**包含资源**:

- Size-tracking Lambda Function
- S3 Event Notification 配置
- IAM Roles and Policies

**独立的原因**:

- 单一职责：只负责监控和记录
- 可以独立更新代码逻辑
- 便于调试和监控

**优势**:

- 更新监控逻辑不影响其他功能
- 可以单独启用/禁用监控

#### 3. **PlottingStack** - 可视化层

**职责**: 提供数据可视化服务

**包含资源**:

- Plotting Lambda Function
- Lambda Layer (matplotlib)
- API Gateway
- IAM Roles and Policies

**独立的原因**:

- 独立的外部 API 接口
- 复杂的依赖（matplotlib layer）
- 可能需要不同的更新频率

**优势**:

- API 配置变更不影响其他功能
- Layer 更新独立
- 可以轻松添加认证/授权

#### 4. **DriverStack** - 测试层

**职责**: 提供端到端测试能力

**包含资源**:

- Driver Lambda Function
- IAM Roles and Policies

**独立的原因**:

- 可选组件（生产环境可能不需要）
- 测试代码可能经常变动
- 不影响核心业务逻辑

**优势**:

- 可以选择性部署
- 测试更新不影响生产功能
- 便于开发和调试

---

## 🔐 IAM 权限设计

### 最小权限原则

每个 Lambda 只拥有完成其功能所需的最小权限：

```python
# Size-tracking Lambda
permissions:
  - s3:ListBucket (read bucket contents)
  - s3:GetObject (read object metadata)
  - dynamodb:PutItem (write metrics)

# Plotting Lambda
permissions:
  - dynamodb:Query (query data, NO Scan)
  - dynamodb:GetItem (read specific items)
  - s3:PutObject (write plot image)

# Driver Lambda
permissions:
  - s3:PutObject (create/update files)
  - s3:DeleteObject (delete files)
  - s3:GetObject (read files if needed)
```

---

## 📊 DynamoDB 表设计

### 表结构

```
Table: S3-object-size-history
├─ Partition Key: bucket_name (String)
│   └─ 支持多个 bucket 的监控
├─ Sort Key: timestamp (Number)
│   └─ 支持时间范围查询
└─ Attributes:
    ├─ total_size (Number) - bucket 总大小 (bytes)
    ├─ object_count (Number) - 对象数量
    ├─ recorded_at (String) - ISO 格式时间戳
    └─ triggered_by (String) - 触发事件类型
```

### Global Secondary Index

```
Index: timestamp-index
├─ Partition Key: timestamp (Number)
└─ Projection: ALL
└─ 用途: 跨所有 bucket 的时间范围查询
```

### Query 模式

```python
# 查询特定 bucket 最近 N 秒的数据
query(
    KeyConditionExpression='bucket_name = :bucket AND timestamp >= :since'
)

# 查询特定 bucket 的所有历史数据（计算最大值）
query(
    KeyConditionExpression='bucket_name = :bucket AND timestamp >= 0'
)

# ❌ 不使用 Scan（效率低）
```

---

## 🌐 API Gateway 设计

### REST API 结构

```
PlottingAPI
└─ /plot (GET)
    ├─ Lambda Proxy Integration
    ├─ Query Parameters:
    │   ├─ bucket (optional) - 覆盖默认 bucket
    │   └─ window (optional) - 时间窗口（秒）
    └─ Response:
        ├─ 200: {"bucket": "...", "s3_key": "plot", ...}
        └─ 500: {"error": "..."}
```

### Lambda Proxy Integration

**优势**:

- Lambda 接收完整的请求信息（headers, query params, body）
- Lambda 完全控制响应格式
- 简化配置，无需定义 models/transforms

---

## 🔄 CDK vs 手动部署对比

| 方面           | Assignment 2 (手动) | Assignment 3 (CDK) |
| -------------- | ------------------- | ------------------ |
| **部署时间**   | 30-60 分钟          | 5-10 分钟          |
| **出错概率**   | 高                  | 低                 |
| **可重复性**   | 差                  | 优秀               |
| **版本控制**   | 仅代码              | 整个基础设施       |
| **更新操作**   | 容易遗漏步骤        | 自动化安全更新     |
| **资源命名**   | 硬编码              | 自动生成唯一名称   |
| **跨环境部署** | 需要手动调整        | 参数化配置         |
| **回滚能力**   | 困难                | 自动支持           |
| **文档化**     | 需要手动编写        | 代码即文档         |

---

## 🎯 设计决策

### 1. 不硬编码资源名称

```python
# ❌ Assignment 2: 硬编码
BUCKET_NAME = "testbucket-031988646272-d4h3b1qq"
TABLE_NAME = "S3-object-size-history"

# ✅ Assignment 3: 自动生成
bucket = s3.Bucket(self, "TestBucket")
# 生成类似: s3sizetrackingstoragestack-testbucketxxxxx-xxxxx
```

**优势**:

- 避免名称冲突
- 支持多环境部署
- 符合 AWS 最佳实践

### 2. 使用环境变量传递配置

```python
# Lambda 函数通过环境变量获取配置
environment={
    "TABLE_NAME": table.table_name,  # CDK 自动填充
    "BUCKET_NAME": bucket.bucket_name,
    "WINDOW_SECONDS": "10",
}
```

**优势**:

- 解耦配置和代码
- 便于不同环境使用不同配置
- 无需修改代码即可更新配置

### 3. 跨 Stack 资源引用

```python
# StorageStack 导出资源
self.bucket = s3.Bucket(...)
self.table = dynamodb.Table(...)

# SizeTrackingStack 导入资源
def __init__(self, scope, id, bucket, table, **kwargs):
    # 直接使用传入的资源
    bucket.grant_read(self.lambda_function)
```

**优势**:

- 类型安全
- CDK 自动管理依赖关系
- 编译时检查

### 4. RemovalPolicy

```python
bucket = s3.Bucket(
    self, "TestBucket",
    removal_policy=RemovalPolicy.DESTROY,  # 开发/测试环境
    auto_delete_objects=True,
)
```

**注意**: 生产环境应该使用 `RemovalPolicy.RETAIN`

---

## 📈 扩展性考虑

### 支持多环境

```python
# 可以添加环境参数
env = app.node.try_get_context("env") or "dev"

storage_stack = StorageStack(
    app, f"StorageStack-{env}",
    env=cdk.Environment(region="us-west-2")
)
```

### 支持多 Bucket 监控

现有设计已经支持：

- DynamoDB 用 `bucket_name` 作为 partition key
- Size-tracking Lambda 可以被多个 bucket 触发
- Plotting Lambda 可以通过参数指定 bucket

### 支持更多数据源

可以添加新的 Stack：

- **EFSTrackingStack** - 监控 EFS 文件系统
- **EC2TrackingStack** - 监控 EC2 实例
- 共享同一个 DynamoDB 表和 Plotting 服务

---

## ✅ 最佳实践遵循

### 1. Infrastructure as Code

- ✅ 所有资源定义在代码中
- ✅ 版本控制
- ✅ 可审计

### 2. 最小权限原则

- ✅ 每个 Lambda 只有必需权限
- ✅ 使用 CDK grant methods

### 3. 关注点分离

- ✅ 每个 Stack 单一职责
- ✅ 资源按功能组织

### 4. 可测试性

- ✅ 独立的 Driver Stack 用于测试
- ✅ 环境变量便于本地测试

### 5. 可观测性

- ✅ CloudWatch Logs 自动配置
- ✅ 可以轻松添加 Metrics 和 Alarms

---

## 🚀 未来改进方向

1. **添加监控告警**

   ```python
   alarm = cloudwatch.Alarm(
       self, "HighBucketSize",
       metric=...,
       threshold=1000000000,  # 1GB
   )
   ```

2. **添加 Lambda 错误处理**

   - Dead Letter Queue (DLQ)
   - Retry 配置
   - Error metrics

3. **添加 API 认证**

   ```python
   authorizer = apigateway.RequestAuthorizer(...)
   ```

4. **添加 CDK Pipeline**

   - 自动化 CI/CD
   - 多环境部署
   - 自动测试

5. **添加成本优化**
   - Reserved Capacity for DynamoDB
   - S3 Lifecycle policies
   - Lambda Reserved Concurrency

---

这个架构设计实现了**高可用、可扩展、易维护**的微服务系统，完全遵循 AWS 和 CDK 的最佳实践！🎉
