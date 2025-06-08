# 智能建筑平台 Git 工作流程

## 分支结构

本项目使用以下分支结构进行开发和版本管理：

- `master`: 主分支，包含生产就绪的代码
- `develop`: 开发分支，包含最新的开发功能
- `feature/xxx`: 功能分支，用于开发新功能
- `bugfix`: 用于修复问题的分支

## 工作流程

### 开发新功能

1. 从 `develop` 分支创建新的功能分支
   ```
   git checkout develop
   git pull
   git checkout -b feature/new-feature-name
   ```

2. 在功能分支上进行开发和提交
   ```
   git add .
   git commit -m "描述性的提交信息"
   ```

3. 完成功能后，将 `develop` 分支合并到功能分支以解决任何冲突
   ```
   git checkout feature/new-feature-name
   git pull origin develop
   ```

4. 将功能分支合并回 `develop` 分支
   ```
   git checkout develop
   git merge feature/new-feature-name
   git push origin develop
   ```

### 修复问题

1. 从 `develop` 分支创建 bugfix 分支或直接使用 bugfix 分支
   ```
   git checkout develop
   git pull
   git checkout bugfix
   git pull origin develop
   ```

2. 修复问题并提交
   ```
   git add .
   git commit -m "修复: 问题描述"
   ```

3. 将修复合并回 `develop` 分支
   ```
   git checkout develop
   git merge bugfix
   git push origin develop
   ```

### 发布版本

1. 当 `develop` 分支稳定并准备发布时，将其合并到 `master` 分支
   ```
   git checkout master
   git pull
   git merge develop
   git tag -a v1.0.0 -m "版本 1.0.0"
   git push origin master --tags
   ```

## 提交信息规范

提交信息应遵循以下格式：

- 功能: 添加了新功能
- 修复: 修复了某个问题
- 改进: 改进了现有功能
- 重构: 代码重构，不影响功能
- 文档: 更新文档
- 测试: 添加或修改测试

示例：
```
功能: 添加登高车控制界面
修复: 修复视频流断开问题
改进: 优化UI响应性
```

## Git 常用命令

```
# 查看状态
git status

# 查看分支
git branch

# 创建并切换到新分支
git checkout -b branch-name

# 拉取最新代码
git pull

# 推送到远程
git push origin branch-name

# 查看提交历史
git log --oneline

# 查看差异
git diff
``` 