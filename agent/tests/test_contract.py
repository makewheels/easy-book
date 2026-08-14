"""契约测试：ALL_TOOLS schema 与 BookTools 方法签名一一对齐。

背景（video-2022 的教训）：工具 schema 与执行层参数漂移会导致模型调用断链。
这里不发任何网络请求，纯粹校验两边定义一致。
"""

from __future__ import annotations

import inspect

import pytest

from book_agent.schema import ALL_TOOLS, WRITE_TOOLS
from book_agent.tools import BookTools


def _tool_names() -> list[str]:
    return [t["function"]["name"] for t in ALL_TOOLS]


def test_no_duplicate_tool_names():
    names = _tool_names()
    assert len(names) == len(set(names)), "工具名重复"


def test_every_schema_has_method():
    for name in _tool_names():
        method = getattr(BookTools, name, None)
        assert callable(method), f"schema 定义了工具 {name}，但 BookTools 没有对应方法"


def test_every_public_tool_method_has_schema():
    schema_names = set(_tool_names())
    # execute 是分发入口，不是工具
    infra_methods = {"execute"}
    for attr_name in dir(BookTools):
        if attr_name.startswith("_") or attr_name in infra_methods:
            continue
        attr = getattr(BookTools, attr_name)
        if not callable(attr):
            continue
        # 数据类字段（api_url 等）不是方法
        if isinstance(attr, property):
            continue
        assert attr_name in schema_names, f"BookTools 方法 {attr_name} 没有对应的 schema"


@pytest.mark.parametrize("tool", ALL_TOOLS, ids=_tool_names())
def test_schema_matches_signature(tool):
    fn = tool["function"]
    name = fn["name"]
    params_schema = fn["parameters"]
    properties = params_schema.get("properties", {})
    required = set(params_schema.get("required", []))

    method = getattr(BookTools, name)
    sig = inspect.signature(method)
    method_params = {
        p.name: p for p in sig.parameters.values() if p.name != "self"
    }

    # properties 与方法参数集合一致
    assert set(properties) == set(method_params), (
        f"{name}: schema properties {sorted(properties)} != 方法参数 {sorted(method_params)}"
    )

    # required == 无默认值的参数
    no_default = {
        p.name for p in method_params.values()
        if p.default is inspect.Parameter.empty
    }
    assert required == no_default, (
        f"{name}: schema required {sorted(required)} != 无默认值参数 {sorted(no_default)}"
    )


def test_write_tools_are_declared_and_marked():
    schema_names = set(_tool_names())
    assert WRITE_TOOLS <= schema_names, "WRITE_TOOLS 里有未定义的工具"
    for tool in ALL_TOOLS:
        fn = tool["function"]
        if fn["name"] in WRITE_TOOLS:
            assert "确认" in fn["description"], f"写操作 {fn['name']} 的 description 未标注需确认"


def test_read_tools_not_in_write_set():
    read_tools = {"search_students", "get_student", "get_schedule", "profit_stats"}
    assert not (read_tools & WRITE_TOOLS), "只读工具不应在 WRITE_TOOLS 中"
