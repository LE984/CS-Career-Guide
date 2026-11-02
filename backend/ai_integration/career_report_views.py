import json
import logging

from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from ai_integration.langgraph.career_report.services.career_report_service import (
    generate_career_report,
    resolve_profile_from_request,
    save_career_report,
)

logger = logging.getLogger(__name__)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def career_report_generation(request):
    try:
        payload = json.loads(request.body or "{}")
        target_job = payload.get("target_job", "").strip()
        request_profile = payload.get("user_profile")

        if not target_job:
            return JsonResponse({"success": False, "error": "target_job is required"}, status=400)

        user_profile = resolve_profile_from_request(request, request_profile)
        if not user_profile:
            return JsonResponse({"success": False, "error": "user_profile is required"}, status=400)

        report = generate_career_report(user_profile=user_profile, target_job=target_job)
        session_id = save_career_report(report, request.user if request.user.is_authenticated else None)

        return JsonResponse({"success": True, "session_id": session_id, "target_job": target_job, "data": report})
    except Exception as exc:
        logger.exception("career_report_generation failed")
        return JsonResponse({"success": False, "error": str(exc)}, status=500)
