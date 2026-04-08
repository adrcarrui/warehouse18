from sqlalchemy import text

from warehouse18.infrastructure.db import SessionLocal


SQL_ARCHIVE = """
INSERT INTO public.rfid_event_log_archive
SELECT *
FROM public.rfid_event_log
WHERE review_status IN ('confirmed', 'rejected')
  AND seen_at < now() - interval '90 days'
ON CONFLICT (id) DO NOTHING
"""

SQL_DELETE = """
DELETE FROM public.rfid_event_log
WHERE review_status IN ('confirmed', 'rejected')
  AND seen_at < now() - interval '90 days'
"""


def run() -> None:
    db = SessionLocal()
    try:
        archive_result = db.execute(text(SQL_ARCHIVE))
        delete_result = db.execute(text(SQL_DELETE))
        db.commit()

        print(
            f"RFID archive done | inserted={archive_result.rowcount} deleted={delete_result.rowcount}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()