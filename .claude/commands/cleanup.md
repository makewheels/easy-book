# cleanup: 清理项目中的临时垃圾文件

## 描述
清理项目根目录中的临时文件和垃圾文件，包括：
- Chrome浏览器截图文件（*.png, *.jpg, *.jpeg）
- 页面快照文件（*-snapshot.txt）
- 临时日志文件
- 构建产物缓存文件
- 开发过程中产生的临时测试文件

## 用法
```bash
/cleanup
```

## 示例
```bash
# 清理所有临时文件
/cleanup

# 清理后项目根目录将只保留重要文件：
# - .git/ (版本控制)
# - .idea/ (IDE配置)
# - backend/ (后端代码)
# - frontend/ (前端代码)
# - docs/ (文档)
# - tests/ (测试)
# - README.md (项目说明)
# - .gitignore (Git忽略规则)
```

## 注意事项
⚠️ **请谨慎使用此命令**
- 此命令会删除文件，无法撤销
- 建议在执行前确认没有重要的未提交文件
- 主要是清理开发过程中产生的临时文件
- 不会删除项目核心代码和配置文件

## 清理的文件类型
- **截图文件**: `*.png`, `*.jpg`, `*.jpeg`, `*.webp`
- **快照文件**: `*-snapshot.txt`, `page-snapshot.txt`, `form-snapshot.txt`
- **日志文件**: `*.log`, `test-*.txt`, `debug-*.txt`
- **临时脚本**: `clear_database.py`, `temp_*.py`, `test_*.py`
- **缓存文件**: `*.cache`, `*.tmp`, `.DS_Store`
- **构建临时文件**: `dist/`, `build/`, `node_modules/.cache/`