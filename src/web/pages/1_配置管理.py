#!/usr/bin/env python3
"""
配置管理页面
提供配置的查看、编辑、导入和导出功能
"""

import streamlit as st
from utils.config_manager import config_manager
import time
import json
from datetime import datetime


def render_config_management():
    """渲染配置管理页面"""
    
    st.title("⚙️ 配置管理")
    
    # 顶部操作按钮
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        pass
    
    with col2:
        if st.button("🔄 刷新", use_container_width=True):
            st.rerun()
    
    with col3:
        # 导出配置
        if st.button("📥 导出配置", use_container_width=True):
            st.session_state["show_export"] = True
    
    with col4:
        # 导入配置
        if st.button("📤 导入配置", use_container_width=True):
            st.session_state["show_import"] = True
    
    # 导出配置对话框
    if st.session_state.get("show_export", False):
        _render_export_dialog()
    
    # 导入配置对话框
    if st.session_state.get("show_import", False):
        _render_import_dialog()
    
    st.markdown("---")
    
    # 获取配置
    config = config_manager.get_config()
    
    # AI模型配置
    st.subheader("🤖 AI模型")
    for key, model in config["ai_models"].items():
        with st.expander(f"{model['name']}", expanded=model["configured"]):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if model["configured"]:
                    st.success(f"✅ 已配置: {model['masked_key']}")
                else:
                    st.info("⚪ 未配置")
            
            with col2:
                if st.button("编辑", key=f"edit_{key}"):
                    st.session_state[f"editing_{key}"] = True
            
            with col3:
                if model["configured"] and st.button("测试", key=f"test_{key}"):
                    st.info("测试功能开发中...")
            
            # 编辑模式
            if st.session_state.get(f"editing_{key}", False):
                # 1. 启用开关 (如果有配置)
                new_enabled = None
                if "enabled" in model:
                    new_enabled = st.checkbox("启用此模型", value=model["enabled"], key=f"enable_{key}")
                
                # 2. Base URL (如果有配置)
                new_base_url = None
                if "base_url" in model:
                    new_base_url = st.text_input(
                        "API Base URL",
                        value=model["base_url"],
                        key=f"base_url_{key}",
                        help="例如: https://api.deepseek.com"
                    )

                # 3. API Key
                new_key = st.text_input(
                    "新API密钥 (留空则不修改)",
                    type="password",
                    key=f"new_key_{key}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 保存", key=f"save_new_{key}"):
                        success = True
                        
                        # 保存 Enabled
                        if new_enabled is not None:
                            env_key = f"{key.upper()}_ENABLED"
                            res = config_manager.update_config(env_key, str(new_enabled).lower())
                            if not res["success"]: success = False
                        
                        # 保存 Base URL
                        if new_base_url is not None:
                            env_key = f"{key.upper()}_BASE_URL"
                            res = config_manager.update_config(env_key, new_base_url)
                            if not res["success"]: success = False
                        
                        # 保存 API Key
                        if new_key:
                            env_key = f"{key.upper()}_API_KEY"
                            res = config_manager.update_config(env_key, new_key)
                            if not res["success"]: success = False
                        
                        if success:
                            st.success("✅ 配置已保存")
                            st.session_state[f"editing_{key}"] = False
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("保存失败，请检查日志")
                
                with col2:
                    if st.button("取消", key=f"cancel_{key}"):
                        st.session_state[f"editing_{key}"] = False
                        st.rerun()
    
    st.markdown("---")
    
    # 数据源配置
    st.subheader("📊 数据源")
    for key, source in config["data_sources"].items():
        with st.expander(f"{source['name']}", expanded=source["configured"]):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if source["configured"]:
                    st.success(f"✅ 已配置: {source['masked_key']}")
                else:
                    st.info("⚪ 未配置")
            
            with col2:
                if st.button("编辑", key=f"edit_source_{key}"):
                    st.session_state[f"editing_source_{key}"] = True
            
            with col3:
                if source["configured"] and st.button("测试", key=f"test_source_{key}"):
                    with st.spinner("测试中..."):
                        st.info("测试功能开发中...")
            
            # 编辑模式
            if st.session_state.get(f"editing_source_{key}", False):
                new_key = st.text_input(
                    "新API密钥",
                    type="password",
                    key=f"new_key_source_{key}"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 保存", key=f"save_source_{key}"):
                        if new_key:
                            env_key = f"{key.upper()}_API_KEY"
                            res = config_manager.update_config(env_key, new_key)
                            if res["success"]:
                                st.success("✅ 已保存")
                                st.session_state[f"editing_source_{key}"] = False
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"保存失败: {res['message']}")
                        else:
                            st.warning("⚠️ 密钥不能为空")
                
                with col2:
                    if st.button("取消", key=f"cancel_source_{key}"):
                        st.session_state[f"editing_source_{key}"] = False
                        st.rerun()
    
    st.markdown("---")
    
    # 数据库配置
    st.subheader("💾 数据库")
    
    # MongoDB
    with st.expander("MongoDB", expanded=config["databases"]["mongodb"]["enabled"]):
        mongodb = config["databases"]["mongodb"]
        
        if mongodb["enabled"]:
            st.success("✅ 已启用")
            st.write(f"**主机**: {mongodb['host']}")
            st.write(f"**端口**: {mongodb['port']}")
            st.write(f"**数据库**: {mongodb['database']}")
        else:
            st.info("⚪ 未启用")
        
        if st.button("配置MongoDB", key="config_mongodb"):
            st.info("请使用环境变量配置数据库连接")
    
    # Redis
    with st.expander("Redis", expanded=config["databases"]["redis"]["enabled"]):
        redis = config["databases"]["redis"]
        
        if redis["enabled"]:
            st.success("✅ 已启用")
            st.write(f"**主机**: {redis['host']}")
            st.write(f"**端口**: {redis['port']}")
        else:
            st.info("⚪ 未启用")
        
        if st.button("配置Redis", key="config_redis"):
            st.info("请使用环境变量配置数据库连接")
    
    st.markdown("---")
    
    # 系统配置
    st.subheader("🔧 系统配置")
    system = config["system"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**时区**: {system['timezone']}")
        st.write(f"**日志级别**: {system['log_level']}")
    
    with col2:
        st.write(f"**内存功能**: {'✅ 启用' if system['memory_enabled'] else '❌ 禁用'}")
        st.write(f"**缓存策略**: {system['cache_strategy']}")
    
    if st.button("修改系统配置"):
        st.info("请修改 .env 文件或环境变量以调整系统配置")


def _render_export_dialog():
    """渲染导出配置对话框"""
    st.markdown("---")
    st.subheader("📥 导出配置")
    
    # 导出选项
    export_secrets = st.checkbox("包含API密钥（敏感信息）", value=False, 
                                  help="⚠️ 导出的文件将包含明文API密钥，请妥善保管")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("生成导出文件", use_container_width=True):
            export_data = _generate_export_data(include_secrets=export_secrets)
            st.session_state["export_data"] = export_data
    
    with col2:
        if st.button("关闭", key="close_export", use_container_width=True):
            st.session_state["show_export"] = False
            st.session_state.pop("export_data", None)
            st.rerun()
    
    # 显示导出数据
    if "export_data" in st.session_state:
        export_json = json.dumps(st.session_state["export_data"], indent=2, ensure_ascii=False)
        
        st.text_area("配置内容预览", export_json, height=200)
        
        # 下载按钮
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tradingagents_config_{timestamp}.json"
        
        st.download_button(
            label="⬇️ 下载配置文件",
            data=export_json,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )
        
        if not export_secrets:
            st.info("💡 提示：未包含API密钥，导入后需要重新配置")


def _render_import_dialog():
    """渲染导入配置对话框"""
    st.markdown("---")
    st.subheader("📤 导入配置")
    
    st.warning("⚠️ 导入配置将覆盖现有设置，请确认后操作")
    
    # 文件上传
    uploaded_file = st.file_uploader("选择配置文件", type=["json"], key="import_file")
    
    col1, col2 = st.columns(2)
    
    with col2:
        if st.button("关闭", key="close_import", use_container_width=True):
            st.session_state["show_import"] = False
            st.rerun()
    
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            
            # 验证配置格式
            if not _validate_import_data(import_data):
                st.error("❌ 配置文件格式无效")
                return
            
            st.success("✅ 配置文件格式正确")
            
            # 显示将要导入的内容
            st.markdown("**将要导入的配置：**")
            
            # AI模型
            if "ai_models" in import_data:
                with st.expander("🤖 AI模型配置", expanded=True):
                    for key, value in import_data["ai_models"].items():
                        if value:  # 只显示有值的配置
                            masked = f"{value[:4]}****{value[-4:]}" if len(value) > 8 else "****"
                            st.write(f"- {key}: {masked}")
            
            # 数据源
            if "data_sources" in import_data:
                with st.expander("📊 数据源配置", expanded=True):
                    for key, value in import_data["data_sources"].items():
                        if value:
                            masked = f"{value[:4]}****{value[-4:]}" if len(value) > 8 else "****"
                            st.write(f"- {key}: {masked}")
            
            # 系统配置
            if "system" in import_data:
                with st.expander("🔧 系统配置", expanded=True):
                    for key, value in import_data["system"].items():
                        st.write(f"- {key}: {value}")
            
            # 确认导入
            with col1:
                if st.button("✅ 确认导入", use_container_width=True, type="primary"):
                    result = _apply_import_data(import_data)
                    if result["success"]:
                        st.success(f"✅ 导入成功！已更新 {result['updated']} 项配置")
                        st.session_state["show_import"] = False
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ 导入失败: {result['message']}")
        
        except json.JSONDecodeError:
            st.error("❌ 无法解析JSON文件，请检查文件格式")
        except Exception as e:
            st.error(f"❌ 导入出错: {str(e)}")


def _generate_export_data(include_secrets: bool = False) -> dict:
    """生成导出数据"""
    import os
    
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "ai_models": {},
        "data_sources": {},
        "system": {}
    }
    
    # AI模型配置
    ai_keys = [
        ("DEEPSEEK_API_KEY", "deepseek_api_key"),
        ("DEEPSEEK_BASE_URL", "deepseek_base_url"),
        ("DEEPSEEK_ENABLED", "deepseek_enabled"),
        ("DASHSCOPE_API_KEY", "dashscope_api_key"),
        ("DASHSCOPE_ENABLED", "dashscope_enabled"),
        ("OPENAI_API_KEY", "openai_api_key"),
    ]
    
    for env_key, export_key in ai_keys:
        value = os.getenv(env_key, "")
        if "API_KEY" in env_key:
            export_data["ai_models"][export_key] = value if include_secrets else ""
        else:
            export_data["ai_models"][export_key] = value
    
    # 数据源配置
    source_keys = [
        ("FINNHUB_API_KEY", "finnhub_api_key"),
        ("ALPHA_VANTAGE_API_KEY", "alpha_vantage_api_key"),
        ("SERPER_API_KEY", "serper_api_key"),
    ]
    
    for env_key, export_key in source_keys:
        value = os.getenv(env_key, "")
        export_data["data_sources"][export_key] = value if include_secrets else ""
    
    # 系统配置
    system_keys = [
        ("TZ", "timezone"),
        ("LOG_LEVEL", "log_level"),
        ("MEMORY_ENABLED", "memory_enabled"),
        ("TA_CACHE_STRATEGY", "cache_strategy"),
    ]
    
    for env_key, export_key in system_keys:
        export_data["system"][export_key] = os.getenv(env_key, "")
    
    return export_data


def _validate_import_data(data: dict) -> bool:
    """验证导入数据格式"""
    if not isinstance(data, dict):
        return False
    
    # 检查版本
    if "version" not in data:
        return False
    
    # 至少要有一个配置分类
    has_config = any(key in data for key in ["ai_models", "data_sources", "system"])
    
    return has_config


def _apply_import_data(data: dict) -> dict:
    """应用导入的配置"""
    updated = 0
    errors = []
    
    # 映射关系：导出key -> 环境变量key
    ai_mapping = {
        "deepseek_api_key": "DEEPSEEK_API_KEY",
        "deepseek_base_url": "DEEPSEEK_BASE_URL",
        "deepseek_enabled": "DEEPSEEK_ENABLED",
        "dashscope_api_key": "DASHSCOPE_API_KEY",
        "dashscope_enabled": "DASHSCOPE_ENABLED",
        "openai_api_key": "OPENAI_API_KEY",
    }
    
    source_mapping = {
        "finnhub_api_key": "FINNHUB_API_KEY",
        "alpha_vantage_api_key": "ALPHA_VANTAGE_API_KEY",
        "serper_api_key": "SERPER_API_KEY",
    }
    
    system_mapping = {
        "timezone": "TZ",
        "log_level": "LOG_LEVEL",
        "memory_enabled": "MEMORY_ENABLED",
        "cache_strategy": "TA_CACHE_STRATEGY",
    }
    
    # 导入AI模型配置
    if "ai_models" in data:
        for key, value in data["ai_models"].items():
            if value and key in ai_mapping:
                env_key = ai_mapping[key]
                result = config_manager.update_config(env_key, value)
                if result["success"]:
                    updated += 1
                else:
                    errors.append(f"{env_key}: {result['message']}")
    
    # 导入数据源配置
    if "data_sources" in data:
        for key, value in data["data_sources"].items():
            if value and key in source_mapping:
                env_key = source_mapping[key]
                result = config_manager.update_config(env_key, value)
                if result["success"]:
                    updated += 1
                else:
                    errors.append(f"{env_key}: {result['message']}")
    
    # 导入系统配置
    if "system" in data:
        for key, value in data["system"].items():
            if value and key in system_mapping:
                env_key = system_mapping[key]
                result = config_manager.update_config(env_key, value)
                if result["success"]:
                    updated += 1
                else:
                    errors.append(f"{env_key}: {result['message']}")
    
    if errors:
        return {
            "success": False,
            "message": f"部分配置导入失败: {'; '.join(errors)}",
            "updated": updated
        }
    
    return {
        "success": True,
        "message": "导入成功",
        "updated": updated
    }


if __name__ == "__main__":
    render_config_management()
