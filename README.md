# 考试辅助工具

这是一个基于 Python 的自动化考试辅助工具，仅用于学习和测试目的。

## ⚠️ 重要声明

**本工具仅用于学习和测试自动化技术，严禁用于任何形式的作弊行为！**

**请遵守考试规则和学术诚信，后果自负！**

## 安装步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Playwright 浏览器

```bash
playwright install chromium
```

## 使用方法

### 运行程序

```bash
python exam_helper.py
```

### 使用流程

1. **输入考试 URL** ilearn->我的考试->进入考试(地址栏url)
   ```
   Please enter exam URL: https://ilearn.gientech.com/goExamNew?isExam=true&courseForm=xxx&examId=xxx&archivesId=xxx
   ```

2. **手动登录**
   - 程序会打开浏览器，等待您完成登录操作（最多等待5分钟）

3. **点击开始考试**
   - 登录成功后，程序会提示您点击"开始考试"按钮

4. **自动填写答案**
   - 自动匹配页面题目并填写正确答案

5. **人工检查提交**
   - 答案填写完成后，请人工检查确认
   - 手动点击提交按钮

### 支持的题型

- **单选题**：`input[type='radio']`
- **多选题**：`input[type='checkbox']`

## 文件结构

```
exam_helper/
├── exam_helper.py    # 主程序
├── requirements.txt  # 依赖配置
├── exam_helper.log   # 日志文件（运行后自动生成）
└── README.md         # 说明文档
```

## 注意事项

1. 请确保网络环境能够正常访问考试系统
2. 登录时请在规定时间内完成操作
3. 答案填写完成后请务必人工检查
4. 本工具不会自动提交试卷

## 免责声明

本工具仅供学习和研究使用。作者不对任何因使用本工具而产生的后果负责。使用前请确保符合相关规定和道德准则。

**严禁用于作弊！后果自负！**