"""
Smart Check-In Decision Engine for Moroccan gyms.
Backend is single source of truth - no business logic in frontend.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from django.utils import timezone
from members.models import Member
from .models import Attendance


@dataclass
class CheckInDecision:
    """Result of the check-in decision engine."""
    result: str  # 'allowed', 'warning', 'blocked'
    reason: str  # 'ok', 'expired', 'debt', 'insurance', 'already_checked_in', 'inactive'
    message: str  # Human-readable message
    member_snapshot: dict  # Member state at decision time
    can_override: bool = False  # Whether admin can override


class CheckInDecisionEngine:
    """
    Decision engine for Smart Check-In.
    
    Decision Flow (priority order):
    1. already_checked_in → BLOCKED (no override)
    2. inactive (is_active=False) → BLOCKED
    3. expired subscription → BLOCKED
    4. has debt → WARNING (allow with confirmation)
    5. no insurance → WARNING (allow with confirmation)
    6. else → ALLOWED
    """
    
    def __init__(self, member: Member, staff_user):
        self.member = member
        self.staff_user = staff_user
        self.today = timezone.now().date()
    
    def evaluate(self) -> CheckInDecision:
        """Run the decision engine and return result."""
        
        # Build member snapshot first
        snapshot = self._build_snapshot()
        
        # 1. Check if already checked in today
        if self._is_already_checked_in():
            return CheckInDecision(
                result='blocked',
                reason='already_checked_in',
                message=f'{self.member.full_name} has already checked in today.',
                member_snapshot=snapshot,
                can_override=False  # Cannot override - DB constraint
            )
        
        # 2. Check if member is inactive (suspended)
        if not self.member.is_active:
            return CheckInDecision(
                result='blocked',
                reason='inactive',
                message=f'{self.member.full_name} account is suspended.',
                member_snapshot=snapshot,
                can_override=True  # Admin can override
            )
        
        # 3. Check if subscription expired
        if self.member.membership_status == 'EXPIRED':
            return CheckInDecision(
                result='blocked',
                reason='expired',
                message=f'{self.member.full_name} subscription has expired.',
                member_snapshot=snapshot,
                can_override=True  # Admin can override
            )
        
        # 4. Check if subscription is pending (never paid)
        if self.member.membership_status == 'PENDING':
            return CheckInDecision(
                result='blocked',
                reason='pending',
                message=f'{self.member.full_name} has no active subscription.',
                member_snapshot=snapshot,
                can_override=True
            )
        
        # 5. Check for warnings (debt, insurance)
        warnings = []
        warning_reasons = []
        
        debt = self.member.remaining_debt
        if debt > 0:
            warnings.append(f'Outstanding debt: {debt:.0f} DH')
            warning_reasons.append('debt')
        
        # Check insurance only if plan requires it
        plan = self.member.membership_plan
        insurance_required = plan.insurance_required if plan else False
        if insurance_required and not self.member.insurance_paid:
            warnings.append('Insurance required but not paid')
            warning_reasons.append('insurance')
        
        if warnings:
            return CheckInDecision(
                result='warning',
                reason=','.join(warning_reasons),
                message=f'{self.member.full_name}: {"; ".join(warnings)}. Proceed with check-in?',
                member_snapshot=snapshot,
                can_override=False  # Warning allows proceeding, no override needed
            )
        
        # 6. All clear - ALLOWED
        return CheckInDecision(
            result='allowed',
            reason='ok',
            message=f'{self.member.full_name} check-in allowed.',
            member_snapshot=snapshot,
            can_override=False
        )
    
    def _is_already_checked_in(self) -> bool:
        """Check if member already checked in today."""
        return Attendance.objects.filter(
            member=self.member,
            date=self.today
        ).exists()
    
    def _build_snapshot(self) -> dict:
        """Build member state snapshot."""
        return {
            'id': self.member.id,
            'full_name': self.member.full_name,
            'photo_url': self.member.photo.url if self.member.photo else None,
            'status': self.member.membership_status,
            'days_left': self.member.days_remaining,
            'debt': float(self.member.remaining_debt),
            'insurance_paid': self.member.insurance_paid,
            'activity_type': self.member.activity_type.name if self.member.activity_type else None,
            'is_active': self.member.is_active,
        }


def perform_checkin(member: Member, staff_user, override: bool = False, override_reason: str = '') -> tuple:
    """
    Execute check-in after decision is made.
    
    Returns: (attendance_record, decision)
    """
    engine = CheckInDecisionEngine(member, staff_user)
    decision = engine.evaluate()
    
    # If blocked and not overriding, don't create record
    if decision.result == 'blocked':
        if not override:
            return None, decision
        # Admin override - check permissions
        if not staff_user.is_admin:
            decision.message = 'Only admin can override blocked check-ins.'
            return None, decision
        if not override_reason:
            decision.message = 'Override reason is required.'
            return None, decision
    
    # Create attendance record
    from django.utils import timezone
    
    attendance = Attendance.objects.create(
        member=member,
        date=engine.today,
        check_in_time=timezone.now().time(),
        recorded_by=staff_user,
        # Snapshot fields
        activity_at_entry=member.activity_type,
        status_at_entry=member.membership_status,
        debt_at_entry=member.remaining_debt,
        insurance_paid_at_entry=member.insurance_paid,
        # Decision fields
        checkin_result=decision.result if not override else 'allowed',
        checkin_reason=decision.reason,
        # Override fields
        override_used=override,
        override_reason=override_reason if override else ''
    )
    
    # Update decision message for successful check-in
    if decision.result == 'warning':
        decision.message = f'{member.full_name} checked in with warnings.'
    elif override:
        decision.message = f'{member.full_name} checked in (admin override).'
        decision.result = 'allowed'
    else:
        decision.message = f'{member.full_name} checked in successfully!'
    
    return attendance, decision
