from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database.db import Database


scheduler = AsyncIOScheduler()


async def send_reminder(bot: Bot, user_id: int, visit_time: str) -> None:
    await bot.send_message(
        user_id,
        f'🔔 <b>Напоминаем, что вы записаны на завтра в {visit_time}. Ждём вас ❤️</b>',
        parse_mode='HTML',
    )


async def schedule_appointment_reminder(
    bot: Bot,
    db: Database,
    appointment_id: int,
    user_id: int,
    visit_datetime: datetime,
    visit_time: str,
    timezone: str,
) -> None:
    remind_at = visit_datetime - timedelta(hours=24)
    now = datetime.now(ZoneInfo(timezone))

    if remind_at <= now:
        return

    job_id = f'appointment_{appointment_id}'

    scheduler.add_job(
        send_reminder,
        'date',
        run_date=remind_at,
        args=[bot, user_id, visit_time],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,
    )

    await db.execute(
        'UPDATE appointments SET reminder_job_id = ? WHERE id = ?',
        (job_id, appointment_id),
    )


async def remove_reminder(db: Database, appointment_id: int) -> None:
    job = scheduler.get_job(f'appointment_{appointment_id}')
    if job:
        scheduler.remove_job(job.id)

    await db.execute(
        'UPDATE appointments SET reminder_job_id = NULL WHERE id = ?',
        (appointment_id,),
    )


async def restore_scheduler_jobs(bot: Bot, db: Database, timezone: str) -> None:
    tz = ZoneInfo(timezone)

    rows = await db.fetchall(
        '''
        SELECT a.id, a.user_id, wd.work_date, ts.slot_time
        FROM appointments a
        JOIN time_slots ts ON ts.id = a.slot_id
        JOIN work_days wd ON wd.id = ts.work_day_id
        WHERE a.status = 'booked'
        '''
    )

    for row in rows:
        visit_dt = datetime.fromisoformat(
            f"{row['work_date']} {row['slot_time']}"
        ).replace(tzinfo=tz)

        await schedule_appointment_reminder(
            bot=bot,
            db=db,
            appointment_id=row['id'],
            user_id=row['user_id'],
            visit_datetime=visit_dt,
            visit_time=row['slot_time'],
            timezone=timezone,
        )