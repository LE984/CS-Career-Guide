#!/usr/bin/env python3
"""
同步数据库中的职业推荐记录到LanceDB
"""

import os
import sys
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cs_career_guide.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 生成预览函数
def generate_preview(self_introduction, max_length=150):
    """生成自我介绍的预览（高亮部分）"""
    if not self_introduction:
        return ""
    
    lines = self_introduction.split('\n')
    preview_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            preview_lines.append(line)
            if len(' '.join(preview_lines)) > max_length:
                break
    
    preview = ' '.join(preview_lines)
    if len(preview) > max_length:
        preview = preview[:max_length] + '...'
    
    return preview

def main():
    import django
    django.setup()
    from ai_integration.models import CareerRecommendationRecord
    from ai_integration.arag_integration import ARAGCareerSearch

    search = ARAGCareerSearch()
    succeeded = 0
    failed = 0
    try:
        for record in CareerRecommendationRecord.objects.all().iterator(chunk_size=100):
            preview = generate_preview(record.self_introduction)
            if record.introduction_preview != preview:
                record.introduction_preview = preview
                record.save(update_fields=["introduction_preview"])
            data = {
                "id": str(record.id),
                "user_id": str(record.user_id) if record.user_id else "",
                "self_introduction": record.self_introduction or "",
                "introduction_preview": preview,
                "recommendations": json.dumps(record.recommendations or [], ensure_ascii=False),
                "analysis_result": record.analysis_result or "",
                "created_at": record.created_at.isoformat() if record.created_at else "",
            }
            if search.add_record(data, upsert=True):
                succeeded += 1
            else:
                failed += 1
    finally:
        search._executor.shutdown(wait=True)
    print(f"Synced {succeeded} records; failed {failed}. Existing table was not deleted.")
    if failed:
        raise RuntimeError("Some records could not be synced; see logs")


if __name__ == "__main__":
    main()
