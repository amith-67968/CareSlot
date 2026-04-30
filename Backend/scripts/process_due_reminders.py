"""
Process due CareSlot reminders from a cron job or worker scheduler.

Example:
python Backend/scripts/process_due_reminders.py
"""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.notification_service import NotificationService  # noqa: E402


async def main() -> None:
    service = NotificationService()
    result = await service.process_due_reminders()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
