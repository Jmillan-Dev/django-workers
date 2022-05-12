from datetime import timedelta
from hashlib import sha1
import json
import logging

from django.db import models
from django.utils import timezone


log = logging.getLogger(__name__)


class Task(models.Model):
    WAITING = 'waiting'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = (
        (WAITING, 'Waiting'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed')
    )

    HOURLY = 3600
    DAILY = 24 * HOURLY
    WEEKLY = 7 * DAILY
    EVERY_2_WEEKS = 2 * WEEKLY
    EVERY_4_WEEKS = 4 * WEEKLY
    NEVER = 0
    REPEAT_CHOICES = (
        (HOURLY, 'hourly'),
        (DAILY, 'daily'),
        (WEEKLY, 'weekly'),
        (EVERY_2_WEEKS, 'every 2 weeks'),
        (EVERY_4_WEEKS, 'every 4 weeks'),
        (NEVER, 'never'),
    )

    handler = models.CharField(max_length=255, db_index=True)
    args = models.TextField(blank=True)
    kwargs = models.TextField(blank=True)

    task_hash = models.CharField(max_length=40, db_index=True)

    error = models.TextField(blank=True)

    schedule = models.IntegerField(blank=True, null=True, db_index=True)
    repeat = models.BigIntegerField(choices=REPEAT_CHOICES, default=NEVER)

    run_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True, db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=WAITING)

    class Meta:
        ordering = ('-completed_at', '-run_at')

    def __repr__(self):
        return 'Task(handler={0}, hash={1})'.format(
            self.handler, self.task_hash[:6]
        )

    def __str__(self):
        return self.handler

    def create_repeated(self):
        if self.repeat <= self.NEVER:
            return None

        scheduled_time = self.run_at + timedelta(seconds=self.repeat)

        while scheduled_time < timezone.now():
            scheduled_time += timedelta(seconds=self.repeat)

        task_hash = self.task_hash or self.get_hash(self.handler, self.args, self.kwargs)

        if Task.objects.filter(task_hash=self.task_hash, run_at=scheduled_time,
                               completed_at=None).exists():
            log.warn(
                'trying to schedule task with same hash and schedule:  {0}'
                .format(self.handler)
            )
            return

        log.debug('scheduling task: {0} for {1}'.format(
            self.handler, scheduled_time
        ))

        Task.objects.create(
            handler=self.handler,
            args=self.args,
            kwargs=self.kwargs,
            task_hash=task_hash,
            repeat=self.repeat,
            run_at=scheduled_time,
        )

    @staticmethod
    def get_hash(task_name, args=None, kwargs=None):
        args = args or []
        kwargs = kwargs or {}

        params = json.dumps((args, kwargs), sort_keys=True)
        v = '%s%s' % (task_name, params)
        return sha1(v.encode('utf-8')).hexdigest()

    @staticmethod
    def create_scheduled_task(handler, schedule):
        if Task.objects.filter(handler=handler, schedule=schedule, completed_at=None).exists():
            log.warn('trying to schedule an already scheduled task: {0}'.format(handler))
            return

        scheduled_time = timezone.now() + timedelta(seconds=schedule)
        log.debug('scheduling task: {0} for {1}'.format(handler, scheduled_time))
        Task.objects.create(
            handler=handler,
            args={},
            kwargs={},
            schedule=schedule,
            run_at=scheduled_time,
        )
