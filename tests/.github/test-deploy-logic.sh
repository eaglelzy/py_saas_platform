#!/bin/bash

# =============================================================================
# GitHub Actions 部署脚本测试工具
# 用于本地测试部署逻辑，无需实际部署
# =============================================================================

set -e

echo "🧪 开始测试 GitHub Actions 部署脚本逻辑..."

# 模拟 GitHub 环境变量
GITHUB_OUTPUT="/tmp/github_output"

# 清理之前的输出
rm -f $GITHUB_OUTPUT

# 测试函数
test_deployment_logic() {
    local test_name="$1"
    local github_ref="$2"
    local github_event_name="$3"
    local github_ref_name="$4"
    local github_sha="$5"
    local github_inputs_env="$6"
    
    echo ""
    echo "📋 测试: $test_name"
    echo "   GITHUB_REF: $github_ref"
    echo "   GITHUB_EVENT_NAME: $github_event_name"
    echo "   GITHUB_REF_NAME: $github_ref_name"
    
    # 清理输出文件
    rm -f $GITHUB_OUTPUT
    
    # 模拟部署逻辑
    if [[ "$github_event_name" == "workflow_dispatch" ]]; then
        ENVIRONMENT="$github_inputs_env"
        echo "environment=$ENVIRONMENT" >> $GITHUB_OUTPUT
        echo "should_deploy=true" >> $GITHUB_OUTPUT
        
        if [[ "$github_ref" == refs/heads/* ]]; then
            SAFE_TAG=$(echo "$github_ref_name" | sed 's/\//_/g')
            echo "tag=$SAFE_TAG" >> $GITHUB_OUTPUT
        else
            echo "tag=$github_sha" >> $GITHUB_OUTPUT
        fi
        
    elif [[ "$github_ref" == refs/heads/release/* ]]; then
        echo "environment=test" >> $GITHUB_OUTPUT
        echo "should_deploy=true" >> $GITHUB_OUTPUT
        SAFE_TAG=$(echo "$github_ref_name" | sed 's/\//_/g')
        echo "tag=$SAFE_TAG" >> $GITHUB_OUTPUT
        
    elif [[ "$github_ref" == refs/tags/v* ]]; then
        # 模拟检查标签是否来自 main 分支
        # 这里我们假设标签名称包含 "main" 或者不包含其他分支名
        if [[ "$github_ref_name" == v* ]] && [[ ! "$github_ref_name" == *"-"* ]]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
            echo "should_deploy=true" >> $GITHUB_OUTPUT
            echo "tag=$github_ref_name" >> $GITHUB_OUTPUT
        else
            echo "environment=none" >> $GITHUB_OUTPUT
            echo "should_deploy=false" >> $GITHUB_OUTPUT
            echo "tag=$github_ref_name" >> $GITHUB_OUTPUT
        fi
        
    elif [[ "$github_ref" == refs/heads/develop ]]; then
        echo "environment=test" >> $GITHUB_OUTPUT
        echo "should_deploy=true" >> $GITHUB_OUTPUT
        echo "tag=latest" >> $GITHUB_OUTPUT
        
    else
        echo "environment=none" >> $GITHUB_OUTPUT
        echo "should_deploy=false" >> $GITHUB_OUTPUT
        echo "tag=$github_sha" >> $GITHUB_OUTPUT
    fi
    
    # 读取结果
    if [[ -f $GITHUB_OUTPUT ]]; then
        source $GITHUB_OUTPUT
        echo "   结果:"
        echo "     environment: $environment"
        echo "     should_deploy: $should_deploy"
        echo "     tag: $tag"
    else
        echo "   ❌ 错误: 没有生成输出文件"
    fi
}

# 测试用例
echo "🚀 开始执行测试用例..."

# 测试 1: release 分支推送
test_deployment_logic \
    "Release 分支推送" \
    "refs/heads/release/1.0.0" \
    "push" \
    "release/1.0.0" \
    "abc123def456"

# 测试 2: main 分支的标签推送（生产环境）
test_deployment_logic \
    "Main 分支标签推送" \
    "refs/tags/v1.0.0" \
    "push" \
    "v1.0.0" \
    "abc123def456"

# 测试 3: 其他分支的标签推送（应该不触发部署）
test_deployment_logic \
    "其他分支标签推送" \
    "refs/tags/v1.0.0-beta" \
    "push" \
    "v1.0.0-beta" \
    "abc123def456"

# 测试 4: develop 分支推送
test_deployment_logic \
    "Develop 分支推送" \
    "refs/heads/develop" \
    "push" \
    "develop" \
    "abc123def456"

# 测试 5: 手动触发 - 测试环境
test_deployment_logic \
    "手动触发 - 测试环境" \
    "refs/heads/main" \
    "workflow_dispatch" \
    "main" \
    "abc123def456" \
    "test"

# 测试 6: 手动触发 - 生产环境
test_deployment_logic \
    "手动触发 - 生产环境" \
    "refs/heads/main" \
    "workflow_dispatch" \
    "main" \
    "abc123def456" \
    "production"

# 测试 7: 其他分支推送（应该不触发部署）
test_deployment_logic \
    "其他分支推送" \
    "refs/heads/feature/new-feature" \
    "push" \
    "feature/new-feature" \
    "abc123def456"

echo ""
echo "✅ 所有测试完成！"
echo ""
echo "📊 测试结果总结:"
echo "   - Release 分支 → 测试环境部署"
echo "   - Main 分支标签 → 生产环境部署"
echo "   - 其他分支标签 → 不触发部署"
echo "   - Develop 分支 → 测试环境部署"
echo "   - 手动触发 → 用户选择环境"
echo "   - 其他分支 → 不触发部署"
