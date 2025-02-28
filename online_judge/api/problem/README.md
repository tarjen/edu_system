# 题目文件夹介绍

这个题目文件夹包含了以下内容:

## 文件夹结构

- **data/**: 包含用于样例和秘密测试的数据文件。
  - **sample/**: 包含样例数据文件。
  - **secret/**: 包含秘密测试数据文件。
  
- **problem_statement/**: 包含题目的具体描述和要求。
  - **problem.md**: 题目描述的Markdown文件。

- **submissions/**: 包含提交的代码文件。
  - **accept/**: 包含通过测试的代码文件。
  - **wrong_answer/**: 包含输出错误的代码文件。
  - 可能还包含其他类型的文件夹,根据不同的提交情况而定。

- **.timelimit**: 包含时间限制,单位为秒。

- **problem.yaml**: 题目的配置文件。
  ```yaml
  name: Hello! %s
  
  limits:
    memory: 2048 MB
    output: 8 MB
  
  oj_lab_config:
    difficulty: "easy"
    tags:
      - "strings"
      - "input-output"

关于 problem.yaml

    name: 题目名称。
    limits:
        memory: 内存限制,单位为MB。
        output: 输出限制,单位为MB。
    oj_lab_config:
        difficulty: 难度级别。
        tags: 标签列表。
