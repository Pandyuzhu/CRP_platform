# 设置远程仓库指南

当你准备好将本地仓库连接到远程服务器（如GitHub或GitLab）时，请按照以下步骤操作：

## GitHub 设置

1. 在GitHub上创建一个新仓库（不要初始化它）

2. 连接本地仓库到远程仓库：
   ```
   git remote add origin https://github.com/YOUR_USERNAME/smart_construction_platform.git
   ```

3. 推送所有分支和标签到远程仓库：
   ```
   git push -u origin --all
   git push origin --tags
   ```

## GitLab 设置

1. 在GitLab上创建一个新仓库（不要初始化它）

2. 连接本地仓库到远程仓库：
   ```
   git remote add origin https://gitlab.com/YOUR_USERNAME/smart_construction_platform.git
   ```

3. 推送所有分支和标签到远程仓库：
   ```
   git push -u origin --all
   git push origin --tags
   ```

## 从远程仓库克隆

其他团队成员可以使用以下命令克隆仓库：

```
git clone https://github.com/YOUR_USERNAME/smart_construction_platform.git
# 或
git clone https://gitlab.com/YOUR_USERNAME/smart_construction_platform.git
```

克隆后，他们应该创建自己的功能分支：

```
git checkout develop
git checkout -b feature/my-feature
```

## 密钥认证（推荐）

为了避免每次推送都需要输入密码，建议设置SSH密钥：

1. 生成SSH密钥（如果还没有）：
   ```
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. 将公钥添加到GitHub/GitLab账户：
   - 复制 `~/.ssh/id_ed25519.pub` 的内容
   - 在GitHub/GitLab设置中添加SSH密钥

3. 将远程URL更改为SSH格式：
   ```
   git remote set-url origin git@github.com:YOUR_USERNAME/smart_construction_platform.git
   # 或
   git remote set-url origin git@gitlab.com:YOUR_USERNAME/smart_construction_platform.git
   ```

## 协作提示

- 经常从`develop`分支拉取最新更改以保持同步
- 在推送之前解决所有合并冲突
- 对同一文件进行更改前与团队成员沟通
- 使用有意义的提交消息，遵循提交规范 