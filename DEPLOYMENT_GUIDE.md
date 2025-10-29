# Assignment 3 部署指南

## 📋 前置准备

### 1. 安装依赖

```bash
# 安装 AWS CDK CLI (需要 Node.js)
npm install -g aws-cdk

# 验证安装
cdk --version

# 安装 Python 依赖
cd /Users/yumengli/Desktop/NEU/6620/Assignment_2/Assignment_3
pip install -r requirements.txt
```

### 2. 配置 AWS 凭证

```bash
# 设置环境变量
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2

# 或者配置 AWS CLI
aws configure
```

### 3. 准备 matplotlib Layer

CDK 需要使用 Assignment_2 中构建的 matplotlib layer：

```bash
# 确保 layer.zip 存在
ls -lh ../layer_build/layer.zip

# 如果不存在，需要构建
cd ../layer_build
# 按照 build_matplotlib_layer.sh 的说明构建
```

---

## 🚀 部署步骤

### 步骤 1: CDK Bootstrap（首次使用）

```bash
# Bootstrap CDK 环境（每个区域只需要一次）
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-west-2

# 或者自动检测
cdk bootstrap
```

### 步骤 2: 合成 CloudFormation 模板

```bash
# 生成 CloudFormation 模板
cdk synth

# 查看将要创建的资源
cdk diff
```

### 步骤 3: 部署所有 Stacks

```bash
# 一次性部署所有 stacks
cdk deploy --all --require-approval never

# 或者逐个部署（推荐，可以看到进度）
cdk deploy S3SizeTrackingStorageStack
cdk deploy S3SizeTrackingSizeTrackingStack
cdk deploy S3SizeTrackingPlottingStack
cdk deploy S3SizeTrackingDriverStack
```

### 步骤 4: 获取输出信息

```bash
# 查看 stack 输出
aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs' \
  --output table

aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingPlottingStack \
  --query 'Stacks[0].Outputs' \
  --output table
```

记录以下信息：

- **BucketName**: S3 bucket 名称
- **TableName**: DynamoDB 表名称
- **ApiUrl**: Plotting API Gateway URL

### 步骤 5: 更新 Driver Lambda 环境变量

部署后，需要手动更新 Driver Lambda 的 API URL：

```bash
# 获取 API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingPlottingStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrlOutput`].OutputValue' \
  --output text)

echo "API URL: $API_URL"

# 获取 Driver Lambda 函数名
DRIVER_FUNCTION=$(aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `S3SizeTrackingDriverStack`)].FunctionName' \
  --output text)

echo "Driver Function: $DRIVER_FUNCTION"

# 更新环境变量
aws lambda update-function-configuration \
  --function-name $DRIVER_FUNCTION \
  --environment "Variables={BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name S3SizeTrackingStorageStack --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' --output text),PLOTTING_API_URL=$API_URL}"
```

---

## 🧪 测试系统

### 方法 1: 调用 Driver Lambda

```bash
# 获取 Driver Lambda 函数名
DRIVER_FUNCTION=$(aws lambda list-functions \
  --query 'Functions[?starts_with(FunctionName, `S3SizeTrackingDriverStack`)].FunctionName' \
  --output text)

# 调用 Lambda
aws lambda invoke \
  --function-name $DRIVER_FUNCTION \
  --payload '{}' \
  output.json

# 查看结果
cat output.json | python -m json.tool
```

### 方法 2: 手动测试

```bash
# 1. 获取 bucket 名称
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

# 2. 上传测试文件
echo "test content" > test.txt
aws s3 cp test.txt s3://$BUCKET_NAME/test.txt

# 3. 等待几秒钟让 size-tracking lambda 处理

# 4. 查看 DynamoDB 数据
aws dynamodb scan --table-name S3-object-size-history

# 5. 调用 plotting API
API_URL=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingPlottingStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrlOutput`].OutputValue' \
  --output text)

curl $API_URL

# 6. 下载生成的图表
aws s3 cp s3://$BUCKET_NAME/plot plot.png
open plot.png  # 在 macOS 上查看
```

### 验证 DynamoDB 表

```bash
# 查看表结构
aws dynamodb describe-table --table-name S3-object-size-history

# 查询数据
aws dynamodb query \
  --table-name S3-object-size-history \
  --key-condition-expression "bucket_name = :bn" \
  --expression-attribute-values '{":bn":{"S":"'$BUCKET_NAME'"}}' \
  --limit 10
```

---

## 🔍 监控和调试

### 查看 Lambda 日志

```bash
# Size-tracking Lambda
aws logs tail /aws/lambda/S3SizeTrackingSizeTrackingStack-SizeTrackingFunction* --follow

# Plotting Lambda
aws logs tail /aws/lambda/S3SizeTrackingPlottingStack-PlottingFunction* --follow

# Driver Lambda
aws logs tail /aws/lambda/S3SizeTrackingDriverStack-DriverFunction* --follow
```

### 查看 CloudWatch 指标

```bash
# Lambda 调用次数
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=$DRIVER_FUNCTION \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## 🗑️ 清理资源

### 方法 1: 使用 CDK

```bash
# 删除所有 stacks（按依赖倒序）
cdk destroy --all

# 或者逐个删除
cdk destroy S3SizeTrackingDriverStack
cdk destroy S3SizeTrackingPlottingStack
cdk destroy S3SizeTrackingSizeTrackingStack
cdk destroy S3SizeTrackingStorageStack
```

### 方法 2: 使用 AWS CLI

```bash
# 先清空 S3 bucket
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name S3SizeTrackingStorageStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BucketNameOutput`].OutputValue' \
  --output text)

aws s3 rm s3://$BUCKET_NAME --recursive

# 然后删除 stacks
aws cloudformation delete-stack --stack-name S3SizeTrackingDriverStack
aws cloudformation delete-stack --stack-name S3SizeTrackingPlottingStack
aws cloudformation delete-stack --stack-name S3SizeTrackingSizeTrackingStack
aws cloudformation delete-stack --stack-name S3SizeTrackingStorageStack
```

---

## ⚠️ 常见问题

### 问题 1: matplotlib layer 找不到

**错误**: `FileNotFoundError: [Errno 2] No such file or directory: '../layer_build/layer.zip'`

**解决**:

```bash
# 确保 layer.zip 存在
cd ../layer_build
# 如果不存在，参考 build_matplotlib_layer.sh 构建
```

### 问题 2: CDK bootstrap 失败

**错误**: `❌ BootstrapBucketName ...`

**解决**:

```bash
# 删除旧的 bootstrap stack
aws cloudformation delete-stack --stack-name CDKToolkit

# 重新 bootstrap
cdk bootstrap
```

### 问题 3: S3 bucket 无法删除

**错误**: `The bucket you tried to delete is not empty`

**解决**:

```bash
# 清空 bucket
aws s3 rm s3://$BUCKET_NAME --recursive

# 然后重新删除 stack
cdk destroy S3SizeTrackingStorageStack
```

### 问题 4: Driver Lambda API URL 是 PLACEHOLDER

**原因**: CDK 部署时无法跨 stack 传递运行时生成的值

**解决**: 按照步骤 5 手动更新环境变量

---

## 📊 架构对比

| 特性       | Assignment 2           | Assignment 3 (CDK) |
| ---------- | ---------------------- | ------------------ |
| 部署方式   | 手动点击 + Python 脚本 | 完全自动化         |
| 可重复性   | 低                     | 高                 |
| 版本控制   | 仅代码                 | 整个基础设施       |
| 更新操作   | 容易出错               | 安全的变更管理     |
| 回滚       | 困难                   | 自动支持           |
| 资源命名   | 硬编码                 | 自动生成           |
| 跨环境部署 | 需要手动调整           | 参数化配置         |

---

## ✅ 验收检查清单

部署成功后，验证以下内容：

- [ ] S3 bucket 已创建
- [ ] DynamoDB 表已创建且有 GSI
- [ ] Size-tracking Lambda 可以被 S3 事件触发
- [ ] Plotting Lambda 可以通过 API 调用
- [ ] Driver Lambda 可以执行完整流程
- [ ] 上传文件到 S3 后，DynamoDB 有记录
- [ ] 调用 Plotting API 后，S3 有 plot 图片
- [ ] 图片显示正确的数据点和历史最大值

---

## 🎯 最佳实践

1. **使用 Git**: 将整个 Assignment_3 目录提交到 Git
2. **环境分离**: 可以修改 app.py 支持 dev/prod 环境
3. **参数化**: 使用 CDK Context 或 Parameters 传递配置
4. **监控**: 启用 CloudWatch Dashboard 监控系统状态
5. **成本控制**: 使用 on-demand billing，定期清理测试数据

---

**祝你部署成功！** 🎉
