"""
推送规则配置 API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
import logging
from datetime import datetime

from ....schemas.notification_rule import (
    NotificationRuleCreate,
    NotificationRuleUpdate,
    NotificationRuleResponse,
)
from ....models.notification_rule import NotificationRuleModel
from ....core.database import get_mongodb

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=NotificationRuleResponse, summary="创建推送规则")
async def create_rule(
    rule: NotificationRuleCreate,
    db=Depends(get_mongodb)
):
    """
    创建推送规则

    - **name**: 规则名称
    - **enabled**: 是否启用
    - **notification_types**: 启用的通知类型列表
    - **min_priority**: 最低优先级
    """
    try:
        rule_id = str(uuid.uuid4())

        rule_model = NotificationRuleModel(
            rule_id=rule_id,
            **rule.dict()
        )

        await db.notification_rules.insert_one(rule_model.dict())

        logger.info(f"创建推送规则: {rule_id}, 名称: {rule.name}")

        return NotificationRuleResponse(**rule_model.dict())
    except Exception as e:
        logger.error(f"创建推送规则失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[NotificationRuleResponse], summary="查询推送规则列表")
async def list_rules(
    enabled: Optional[bool] = None,
    db=Depends(get_mongodb)
):
    """
    查询推送规则列表

    - **enabled**: 是否仅查询启用的规则（可选）
    """
    try:
        filter_dict = {}
        if enabled is not None:
            filter_dict["enabled"] = enabled

        rules = await db.notification_rules.find(filter_dict).sort("created_at", -1).to_list(length=100)

        return [NotificationRuleResponse(**rule) for rule in rules]
    except Exception as e:
        logger.error(f"查询推送规则列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{rule_id}", response_model=NotificationRuleResponse, summary="获取推送规则详情")
async def get_rule(
    rule_id: str,
    db=Depends(get_mongodb)
):
    """
    获取推送规则详情

    - **rule_id**: 规则ID
    """
    try:
        rule = await db.notification_rules.find_one({"rule_id": rule_id})

        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")

        return NotificationRuleResponse(**rule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推送规则详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{rule_id}", response_model=NotificationRuleResponse, summary="更新推送规则")
async def update_rule(
    rule_id: str,
    update_data: NotificationRuleUpdate,
    db=Depends(get_mongodb)
):
    """
    更新推送规则

    - **rule_id**: 规则ID
    """
    try:
        # 构建更新字典（仅包含非空字段）
        update_dict = {
            k: v for k, v in update_data.dict().items()
            if v is not None
        }

        if not update_dict:
            raise HTTPException(status_code=400, detail="没有需要更新的字段")

        update_dict["updated_at"] = datetime.now()

        result = await db.notification_rules.update_one(
            {"rule_id": rule_id},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")

        # 获取更新后的规则
        rule = await db.notification_rules.find_one({"rule_id": rule_id})

        logger.info(f"更新推送规则: {rule_id}")

        return NotificationRuleResponse(**rule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新推送规则失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rule_id}", response_model=dict, summary="删除推送规则")
async def delete_rule(
    rule_id: str,
    db=Depends(get_mongodb)
):
    """
    删除推送规则

    - **rule_id**: 规则ID
    """
    try:
        result = await db.notification_rules.delete_one({"rule_id": rule_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="规则不存在")

        logger.info(f"删除推送规则: {rule_id}")

        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除推送规则失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{rule_id}/toggle", response_model=NotificationRuleResponse, summary="一键启停规则")
async def toggle_rule(
    rule_id: str,
    db=Depends(get_mongodb)
):
    """
    一键启停规则

    - **rule_id**: 规则ID
    """
    try:
        # 获取当前规则
        rule = await db.notification_rules.find_one({"rule_id": rule_id})

        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")

        # 切换启用状态
        new_enabled = not rule.get("enabled", True)

        await db.notification_rules.update_one(
            {"rule_id": rule_id},
            {
                "$set": {
                    "enabled": new_enabled,
                    "updated_at": datetime.now()
                }
            }
        )

        # 获取更新后的规则
        updated_rule = await db.notification_rules.find_one({"rule_id": rule_id})

        logger.info(f"切换推送规则状态: {rule_id}, 新状态: {new_enabled}")

        return NotificationRuleResponse(**updated_rule)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换推送规则状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
