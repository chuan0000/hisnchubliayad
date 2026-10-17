with open('app/routers/team.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update imports in team.py
if 'CadreNotice' not in text:
    text = text.replace(
        'DutyInspectionLog, GoodDeedJournal, CarpoolTrip',
        'DutyInspectionLog, GoodDeedJournal, CarpoolTrip, CadreNotice'
    )
    text = text.replace(
        'DutyInspectionLogCreate, DutyInspectionLogResponse',
        'DutyInspectionLogCreate, DutyInspectionLogResponse, CadreNoticeCreate, CadreNoticeResponse'
    )
    print('Imported CadreNotice in team.py')

r19_team_code = '''
# ==============================================================================
# 【功能 94】道場青年幹部即時通訊公告與內部通知公佈欄 API
# ==============================================================================
@router.get("/cadre-notices", response_model=List[CadreNoticeResponse])
def list_cadre_notices(
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】調閱幹部內部專屬公佈欄與急件叮嚀"""
    return db.query(CadreNotice).order_by(CadreNotice.id.desc()).all()

@router.post("/cadre-notices", response_model=CadreNoticeResponse)
def create_cadre_notice(
    notice_in: CadreNoticeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】發布幹部內部專屬通知"""
    new_n = CadreNotice(
        title=notice_in.title,
        content=notice_in.content or "",
        priority=notice_in.priority or "normal",
        publisher_name=notice_in.publisher_name or user.username,
        target_roles=notice_in.target_roles or "all"
    )
    db.add(new_n)
    db.commit()
    db.refresh(new_n)
    record_audit_log(db, user.username, "發布幹部內部通告", target=new_n.title)
    return new_n

@router.delete("/cadre-notices/{notice_id}")
def delete_cadre_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】刪除內部通報"""
    n = db.query(CadreNotice).filter(CadreNotice.id == notice_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="找不到此通告")
    db.delete(n)
    db.commit()
    return {"status": "success", "message": "通報已刪除"}
'''

if 'cadre-notices' not in text:
    target = '@router.get(\"/all-admin\"'
    text = text.replace(target, r19_team_code + '\n' + target)
    print('Feature 94 added to team.py!')

with open('app/routers/team.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('app/routers/team.py updated for Feature 94!')
