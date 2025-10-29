# 🚀 Assignment 3 快速开始指南

## ⚡ 30 秒快速部署

```bash
# 1. 进入项目目录
cd /Users/yumengli/Desktop/NEU/6620/Assignment_2/Assignment_3

# 2. 安装依赖（首次）
npm install -g aws-cdk
pip install -r requirements.txt

# 3. 配置AWS（首次）
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# 4. 一键部署
./scripts/deploy.sh

# 5. 更新Driver配置
./scripts/update_driver_env.sh

# 6. 测试系统
./scripts/test_system.sh

# 7. 查看结果
open plot.png
```

---

## 📁 项目结构一览

```
Assignment_3/
├── 📄 app.py                  # CDK应用入口
├── ⚙️  cdk.json               # CDK配置
├── 📦 requirements.txt        # Python依赖
│
├── 📚 文档/
│   ├── README.md              # 项目概述
│   ├── DEPLOYMENT_GUIDE.md    # 详细部署指南
│   ├── ARCHITECTURE.md        # 架构设计文档
│   ├── SUMMARY.md             # 完成总结
│   └── QUICK_START.md         # 本文件
│
├── 🏗️  stacks/                # CDK Stacks
│   ├── storage_stack.py       # S3 + DynamoDB
│   ├── size_tracking_stack.py # 监控Lambda
│   ├── plotting_stack.py      # 绘图Lambda + API
│   └── driver_stack.py        # 测试Lambda
│
├── 💻 lambda_code/            # Lambda函数代码
│   ├── size_tracking/index.py # 监控逻辑
│   ├── plotting/index.py      # 绘图逻辑
│   └── driver/index.py        # 测试编排
│
└── 🔧 scripts/                # 自动化脚本
    ├── deploy.sh              # 部署
    ├── update_driver_env.sh   # 配置更新
    ├── test_system.sh         # 测试
    └── cleanup.sh             # 清理
```

---

## 🎯 核心命令速查

### 部署相关

```bash
# 查看将要创建的资源
cdk diff

# 生成CloudFormation模板
cdk synth

# 部署所有stacks
cdk deploy --all

# 部署单个stack
cdk deploy S3SizeTrackingStorageStack

# 查看部署输出
aws cloudformation describe-stacks --stack-name S3SizeTrackingStorageStack
```

### 测试相关

```bash
# 获取资源信息
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

# 手动测试 - 上传文件
echo "test" > test.txt
aws s3 cp test.txt s3://$BUCKET/

# 查看DynamoDB数据
aws dynamodb scan --table-name S3-object-size-history

# 调用Plotting API
API_URL=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingPlottingStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrlOutput`].OutputValue' \
  --output text)
curl $API_URL

# 下载生成的图表
aws s3 cp s3://$BUCKET/plot plot.png
```

### 调试相关

```bash
# 查看Lambda日志（实时）
aws logs tail /aws/lambda/S3SizeTrackingSizeTrackingStack-SizeTrackingFunction* --follow

# 获取Lambda函数名
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `S3SizeTracking`)].FunctionName'

# 手动调用Lambda
aws lambda invoke \
  --function-name FUNCTION_NAME \
  --payload '{}' \
  output.json
```

### 清理相关

```bash
# 清空S3桶
aws s3 rm s3://$BUCKET --recursive

# 删除所有stacks
cdk destroy --all

# 或使用清理脚本
./scripts/cleanup.sh
```

---

## 🏗️ 4 个 Stacks 功能

| Stack                 | 功能       | 包含资源                     |
| --------------------- | ---------- | ---------------------------- |
| **StorageStack**      | 基础存储   | S3 Bucket + DynamoDB Table   |
| **SizeTrackingStack** | 实时监控   | Lambda + S3 Event Trigger    |
| **PlottingStack**     | 数据可视化 | Lambda + Layer + API Gateway |
| **DriverStack**       | 端到端测试 | Lambda (测试编排)            |

---

## 📊 数据流程图

```
                    ┌─────────────────┐
                    │   S3 Bucket     │
                    └────────┬────────┘
                             │ 事件触发
                             ↓
                    ┌─────────────────┐
                    │ Size-tracking Λ │
                    └────────┬────────┘
                             │ 写入
                             ↓
                    ┌─────────────────┐
                    │   DynamoDB      │←───┐
                    └────────┬────────┘    │
                             │ 查询       查询
                             ↓             │
┌──────────┐       ┌─────────────────┐    │
│ Driver Λ │──────→│  Plotting Λ     │────┘
└──────────┘ 调用  └────────┬────────┘
  执行测试            ↑      │ 保存
                      │      ↓
                   ┌──┴──────────────┐
                   │   API Gateway    │
                   └──────────────────┘
```

---

## 🔍 常见问题快速解决

### Q: `cdk: command not found`

```bash
npm install -g aws-cdk
```

### Q: Layer 找不到

```bash
# 确保matplotlib layer存在
ls -lh ../layer_build/layer.zip

# 如果不存在，需要构建
cd ../layer_build
# 参考build_matplotlib_layer.sh
```

### Q: Driver Lambda API URL 是 PLACEHOLDER

```bash
# 运行更新脚本
./scripts/update_driver_env.sh
```

### Q: S3 bucket 无法删除

```bash
# 先清空bucket
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

aws s3 rm s3://$BUCKET --recursive

# 然后删除stack
cdk destroy S3SizeTrackingStorageStack
```

### Q: CDK bootstrap 失败

```bash
# 删除旧的bootstrap stack
aws cloudformation delete-stack --stack-name CDKToolkit

# 重新bootstrap
cdk bootstrap
```

---

## 📝 关键文件说明

### `app.py`

- CDK 应用入口
- 定义 4 个 stacks 及其依赖关系
- 配置输出参数

### `stacks/storage_stack.py`

- 创建 S3 bucket（自动命名）
- 创建 DynamoDB table（包含 GSI）
- 配置删除策略

### `stacks/size_tracking_stack.py`

- 创建监控 Lambda
- 配置 S3 事件触发器
- 设置 IAM 权限

### `stacks/plotting_stack.py`

- 创建绘图 Lambda
- 添加 matplotlib layer
- 创建 API Gateway
- 配置 REST API endpoint

### `stacks/driver_stack.py`

- 创建测试 Lambda
- 配置环境变量（需要后续更新）

---

## 🎓 学习资源

### CDK 相关

- [AWS CDK 文档](https://docs.aws.amazon.com/cdk/)
- [CDK Workshop](https://cdkworkshop.com/)
- [CDK Examples](https://github.com/aws-samples/aws-cdk-examples)

### AWS 服务

- [Lambda 最佳实践](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DynamoDB 查询优化](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [API Gateway 设计](https://docs.aws.amazon.com/apigateway/latest/developerguide/rest-api-design.html)

---

## ✅ 验收检查清单

部署完成后，检查以下内容：

- [ ] 运行 `cdk deploy --all` 成功
- [ ] 4 个 CloudFormation stacks 都是 `CREATE_COMPLETE` 状态
- [ ] 运行 `./scripts/test_system.sh` 成功
- [ ] DynamoDB 表中有数据记录
- [ ] S3 桶中有 `plot` 对象
- [ ] 下载的 plot.png 显示正确的图表
- [ ] 图表包含 4 个数据点（18, 27, 0, 2 bytes）
- [ ] 图表包含红色虚线（历史最大值）
- [ ] CloudWatch Logs 有 Lambda 执行日志

---

## 🎯 下一步

### 完成部署后

1. ✅ 保存 bucket 名称和 API URL
2. ✅ 截图 plot 图表
3. ✅ 准备 demo 演示
4. ✅ 理解架构设计

### 进阶学习

1. 📚 研究 CDK 的高级特性（Aspects, Custom Resources）
2. 📚 添加 CloudWatch Dashboard
3. 📚 实现 CI/CD Pipeline
4. 📚 添加多环境支持（dev/staging/prod）

---

## 💡 小贴士

1. **首次部署**: 完整走一遍流程，记录任何问题
2. **测试数据**: 可以多次运行 driver lambda 生成更多数据点
3. **清理**: 测试完成后及时清理，避免产生费用
4. **文档**: 所有操作都有详细文档，遇到问题先查文档
5. **日志**: CloudWatch Logs 是调试的最好朋友

---

## 📞 支持

遇到问题？

1. 查看 `DEPLOYMENT_GUIDE.md` 的常见问题部分
2. 查看 CloudWatch Logs
3. 检查 IAM 权限配置
4. 验证环境变量设置

---

**祝你部署成功！** 🎉

如有任何问题，请参考详细文档：

- 部署问题 → `DEPLOYMENT_GUIDE.md`
- 架构理解 → `ARCHITECTURE.md`
- 项目总结 → `SUMMARY.md`
