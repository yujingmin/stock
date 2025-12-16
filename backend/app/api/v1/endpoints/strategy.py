"""
策略开发API端点
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Body, Query, Depends
from pydantic import BaseModel, Field

from app.services.strategy import conversation_service, strategy_service, template_service
from app.services.strategy.backtest_integration_service import backtest_integration_service
from app.models.strategy import MessageRole, ConversationStatus
from app.api.v1.endpoints.auth import get_current_user

# 创建路由器
router = APIRouter()


# ============ Pydantic 模型 ============


class CreateConversationRequest(BaseModel):
    """创建对话请求"""

    title: str = Field(..., description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    tags: Optional[List[str]] = Field(None, description="对话标签")


class UpdateConversationRequest(BaseModel):
    """更新对话请求"""

    title: Optional[str] = Field(None, description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")
    tags: Optional[List[str]] = Field(None, description="对话标签")
    status: Optional[ConversationStatus] = Field(None, description="对话状态")


class AddMessageRequest(BaseModel):
    """添加消息请求"""

    content: str = Field(..., description="消息内容")
    generated_code: Optional[str] = Field(None, description="生成的代码")
    strategy_version_id: Optional[str] = Field(None, description="关联的策略版本ID")


class CreateStrategyVersionRequest(BaseModel):
    """创建策略版本请求"""

    strategy_name: str = Field(..., description="策略名称")
    code: str = Field(..., description="策略代码")
    conversation_id: Optional[str] = Field(None, description="关联的对话ID")
    message_id: Optional[str] = Field(None, description="生成此版本的消息ID")
    strategy_type: Optional[str] = Field(None, description="策略类型")
    parameters: Optional[dict] = Field(None, description="策略参数")
    version_description: Optional[str] = Field(None, description="版本说明")


# ============ 对话管理端点 ============


@router.post("/conversations", summary="创建策略对话")
async def create_conversation(
    request: CreateConversationRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    创建新的策略对话

    - **title**: 对话标题
    - **description**: 对话描述（可选）
    - **tags**: 对话标签（可选）
    """
    try:
        conversation_id = await conversation_service.create_conversation(
            user_id=current_user["id"],
            title=request.title,
            description=request.description,
            tags=request.tags,
        )

        return {"conversation_id": conversation_id, "message": "对话创建成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建对话失败: {str(e)}")


@router.get("/conversations", summary="获取对话列表")
async def list_conversations(
    status: Optional[ConversationStatus] = Query(None, description="对话状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取用户的策略对话列表

    - **status**: 对话状态筛选（可选）
    - **skip**: 跳过数量
    - **limit**: 限制数量
    """
    try:
        conversations = await conversation_service.list_conversations(
            user_id=current_user["id"], status=status, skip=skip, limit=limit
        )

        return {"conversations": conversations, "count": len(conversations)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {str(e)}")


@router.get("/conversations/{conversation_id}", summary="获取对话详情")
async def get_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """
    获取对话详情

    - **conversation_id**: 对话ID
    """
    try:
        conversation = await conversation_service.get_conversation(
            conversation_id, user_id=current_user["id"]
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {str(e)}")


@router.put("/conversations/{conversation_id}", summary="更新对话")
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    更新对话信息

    - **conversation_id**: 对话ID
    - **title**: 新标题（可选）
    - **description**: 新描述（可选）
    - **tags**: 新标签（可选）
    - **status**: 新状态（可选）
    """
    try:
        # 构建更新字典
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.description is not None:
            updates["description"] = request.description
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.status is not None:
            updates["status"] = request.status

        if not updates:
            raise HTTPException(status_code=400, detail="没有提供更新字段")

        success = await conversation_service.update_conversation(
            conversation_id, current_user["id"], **updates
        )

        if not success:
            raise HTTPException(status_code=404, detail="对话不存在或无权限")

        return {"message": "对话更新成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新对话失败: {str(e)}")


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: str, current_user: dict = Depends(get_current_user)
):
    """
    删除对话（软删除）

    - **conversation_id**: 对话ID
    """
    try:
        success = await conversation_service.delete_conversation(
            conversation_id, current_user["id"]
        )

        if not success:
            raise HTTPException(status_code=404, detail="对话不存在或无权限")

        return {"message": "对话已删除"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除对话失败: {str(e)}")


# ============ 消息管理端点 ============


@router.post("/conversations/{conversation_id}/messages", summary="添加对话消息")
async def add_message(
    conversation_id: str,
    request: AddMessageRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    添加对话消息

    - **conversation_id**: 对话ID
    - **content**: 消息内容
    - **generated_code**: 生成的代码（可选）
    - **strategy_version_id**: 关联的策略版本ID（可选）
    """
    try:
        # 验证对话存在且属于当前用户
        conversation = await conversation_service.get_conversation(
            conversation_id, user_id=current_user["id"]
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        # 添加用户消息
        message_id = await conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=request.content,
            generated_code=request.generated_code,
            strategy_version_id=request.strategy_version_id,
        )

        return {"message_id": message_id, "message": "消息添加成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加消息失败: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", summary="获取对话消息列表")
async def get_messages(
    conversation_id: str,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="限制数量"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取对话消息列表

    - **conversation_id**: 对话ID
    - **skip**: 跳过数量
    - **limit**: 限制数量
    """
    try:
        # 验证对话存在且属于当前用户
        conversation = await conversation_service.get_conversation(
            conversation_id, user_id=current_user["id"]
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")

        messages = await conversation_service.get_messages(
            conversation_id, skip=skip, limit=limit
        )

        return {"messages": messages, "count": len(messages)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息列表失败: {str(e)}")


# ============ 策略版本管理端点 ============


@router.post("/strategies", summary="创建策略版本")
async def create_strategy_version(
    request: CreateStrategyVersionRequest = Body(...),
    current_user: dict = Depends(get_current_user),
):
    """
    创建策略版本

    - **strategy_name**: 策略名称
    - **code**: 策略代码
    - **conversation_id**: 关联的对话ID（可选）
    - **message_id**: 生成此版本的消息ID（可选）
    - **strategy_type**: 策略类型（可选）
    - **parameters**: 策略参数（可选）
    - **version_description**: 版本说明（可选）
    """
    try:
        strategy_id = await strategy_service.create_strategy_version(
            strategy_name=request.strategy_name,
            user_id=current_user["id"],
            code=request.code,
            conversation_id=request.conversation_id,
            message_id=request.message_id,
            strategy_type=request.strategy_type,
            parameters=request.parameters,
            version_description=request.version_description,
        )

        return {"strategy_id": strategy_id, "message": "策略版本创建成功"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建策略版本失败: {str(e)}")


@router.get("/strategies", summary="获取策略版本列表")
async def list_strategy_versions(
    strategy_name: Optional[str] = Query(None, description="策略名称筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    current_user: dict = Depends(get_current_user),
):
    """
    获取策略版本列表

    - **strategy_name**: 策略名称筛选（可选）
    - **skip**: 跳过数量
    - **limit**: 限制数量
    """
    try:
        strategies = await strategy_service.list_strategy_versions(
            user_id=current_user["id"],
            strategy_name=strategy_name,
            skip=skip,
            limit=limit,
        )

        return {"strategies": strategies, "count": len(strategies)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/strategies/{strategy_id}", summary="获取策略版本详情")
async def get_strategy_version(
    strategy_id: str, current_user: dict = Depends(get_current_user)
):
    """
    获取策略版本详情

    - **strategy_id**: 策略ID
    """
    try:
        strategy = await strategy_service.get_strategy_version(
            strategy_id, user_id=current_user["id"]
        )

        if not strategy:
            raise HTTPException(status_code=404, detail="策略版本不存在")

        return strategy

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取策略详情失败: {str(e)}")


@router.get("/strategies/{strategy_id}/compare/{target_id}", summary="比较策略版本")
async def compare_strategy_versions(
    strategy_id: str, target_id: str, current_user: dict = Depends(get_current_user)
):
    """
    比较两个策略版本

    - **strategy_id**: 策略版本1 ID
    - **target_id**: 策略版本2 ID
    """
    try:
        comparison = await strategy_service.compare_versions(
            strategy_id, target_id, current_user["id"]
        )

        return comparison

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比较策略版本失败: {str(e)}")


# ============ 策略模板管理端点 ============


@router.get("/templates", summary="获取策略模板列表")
async def list_templates(
    strategy_type: Optional[str] = Query(None, description="策略类型筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
):
    """
    获取策略模板列表

    - **strategy_type**: 策略类型筛选（可选）
    - **difficulty**: 难度筛选（beginner/intermediate/advanced）
    - **tags**: 标签筛选（可选）
    - **skip**: 跳过数量
    - **limit**: 限制数量
    """
    try:
        templates = await template_service.list_templates(
            strategy_type=strategy_type,
            difficulty=difficulty,
            tags=tags,
            skip=skip,
            limit=limit,
        )

        return {"templates": templates, "count": len(templates)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/templates/{template_id}", summary="获取模板详情")
async def get_template(template_id: str):
    """
    获取模板详情

    - **template_id**: 模板ID
    """
    try:
        template = await template_service.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")

        # 增加使用次数
        await template_service.increment_usage(template_id)

        return template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")


@router.get("/templates/search/{keyword}", summary="搜索模板")
async def search_templates(keyword: str):
    """
    搜索策略模板

    - **keyword**: 搜索关键词
    """
    try:
        templates = await template_service.search_templates(keyword)

        return {"templates": templates, "count": len(templates)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索模板失败: {str(e)}")


# ============ 回测相关接口 ============


class RunBacktestRequest(BaseModel):
    """运行回测请求"""

    strategy_id: str = Field(..., description="策略版本ID")
    symbol: str = Field(default="000001", description="股票代码")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYYMMDD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYYMMDD)")
    initial_cash: float = Field(default=100000.0, description="初始资金")
    commission: Optional[float] = Field(default=0.0003, description="佣金费率")
    stamp_duty: Optional[float] = Field(default=0.001, description="印花税")


@router.post("/backtest/run", summary="运行策略回测")
async def run_backtest(
    request: RunBacktestRequest = Body(...),
    current_user=Depends(get_current_user),
):
    """
    运行策略回测

    - **strategy_id**: 策略版本ID
    - **symbol**: 股票代码
    - **start_date**: 开始日期 (YYYYMMDD)
    - **end_date**: 结束日期 (YYYYMMDD)
    - **initial_cash**: 初始资金
    """
    try:
        user_id = str(current_user.id)

        # 运行回测
        result = await backtest_integration_service.run_strategy_backtest(
            strategy_id=request.strategy_id,
            user_id=user_id,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            commission=request.commission,
            stamp_duty=request.stamp_duty,
        )

        return {
            "success": True,
            "message": "回测完成",
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


class QuickBacktestRequest(BaseModel):
    """快速回测请求"""

    strategy_code: str = Field(..., description="策略代码")
    symbol: str = Field(default="000001", description="股票代码")
    start_date: Optional[str] = Field(None, description="开始日期 (YYYYMMDD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYYMMDD)")
    initial_cash: float = Field(default=100000.0, description="初始资金")
    strategy_params: Optional[dict] = Field(None, description="策略参数")


@router.post("/backtest/quick", summary="快速回测（不保存）")
async def quick_backtest(
    request: QuickBacktestRequest = Body(...),
    current_user=Depends(get_current_user),
):
    """
    快速回测策略代码（不保存策略版本）

    用于测试和预览策略表现
    """
    try:
        result = await backtest_integration_service.quick_backtest_from_code(
            strategy_code=request.strategy_code,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=request.initial_cash,
            strategy_params=request.strategy_params,
        )

        return {
            "success": True,
            "message": "快速回测完成",
            "result": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"快速回测失败: {str(e)}")


@router.get("/backtest/history/{strategy_id}", summary="获取策略回测历史")
async def get_backtest_history(
    strategy_id: str,
    current_user=Depends(get_current_user),
):
    """
    获取策略的回测历史记录

    - **strategy_id**: 策略版本ID
    """
    try:
        user_id = str(current_user.id)

        # 获取策略信息（包含回测结果）
        strategy = await strategy_service.get_strategy_version(strategy_id, user_id)

        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")

        # 返回回测相关信息
        backtest_info = {
            "strategy_id": strategy_id,
            "strategy_name": strategy.get("strategy_name"),
            "backtest_result_id": strategy.get("backtest_result_id"),
            "performance_metrics": strategy.get("performance_metrics", {}),
            "created_at": strategy.get("created_at"),
        }

        return {
            "success": True,
            "backtest_info": backtest_info,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取回测历史失败: {str(e)}")

